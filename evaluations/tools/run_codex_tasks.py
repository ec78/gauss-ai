"""Run evaluation tasks through a Codex client connected to `gauss-ai-mcp`,
one fresh `codex exec` conversation per task, and collect the transcripts.

Planning: `planning/evaluation-automation.md` §3. A developer tool outside
`scripts/` (never packaged, never run by the test suite). It does not grade
anything: the developing session reads the transcripts afterwards under the
usual live-evaluation rules, and `replay_snippets.py` replays the validated
snippets.

Isolation, and why each piece is there:

- **No user Codex config** (`--ignore-user-config`). The user's
  `~/.codex/config.toml` enables plugins (browser, computer use), hooks and
  other MCP servers; a test client that can drive a browser is not the client
  under test. Auth still comes from `CODEX_HOME`. Everything the run needs is
  passed with `-c`: the model, and one MCP server, `gauss-ai`.
- **No real GAUSS.** `GAUSS_AI_MCP_ALLOW_REAL_GAUSS` is never set, so an
  attempted run stops at `real_gauss_not_allowed`. A `codex exec` turn ends
  its MCP server when it ends, so a run prompt could never be answered by the
  user anyway (§4), and the client must never answer one itself.
- **A separate gauss-ai home.** The MCP server runs with `USERPROFILE` (which
  `Path.home()` follows on Windows; `HOME` elsewhere) set to `<eval>/home`,
  whose `.gauss-ai/config.json` is written by `setup`. That gives the run its
  own analysis folder, holding fresh copies of the input files, without
  touching the user's real configuration. The analysis folder is still set
  by a config file the user's own tooling wrote, never by an MCP argument.
- **A clean working directory** (`<eval>/work`, `-C`): no `AGENTS.md`,
  `CLAUDE.md`, planning docs or repository, so nothing there coaches the
  client. (The sandbox is read-only, which limits writes, not reads; whether
  the client read anything outside, such as gauss-ai's own source, is
  checked in its transcript's commands.)

usage:
  python evaluations/tools/run_codex_tasks.py setup EVAL_DIR --input FILE [--input FILE ...]
  python evaluations/tools/run_codex_tasks.py run EVAL_DIR TASKS.md OUT_DIR [--only 86.1,86.2]
      [--model gpt-6.1-sol] [--sandbox read-only]

TASKS.md holds one task per `## <id>` heading; the text under it, up to the
next heading, is sent verbatim as the user's message.

`--preamble FILE` puts a fixed note before every task. Batch 1 of 86.x
(plan §8) showed why one is needed: told by `gauss_session_start` that
execution is off, the client stopped before writing any code in four of
ten tasks. A preamble is a deviation from the user's verbatim message. It
is recorded in the manifest and must be disclosed in every run file.
"""
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import time
from pathlib import Path

#: The newest model this account's Codex accepts (2026-11-18). `gpt-6.2-sol` and
#: `gpt-6.2-astra` are listed in Codex's model cache, but a ChatGPT-account login
#: refuses them ("not supported when using Codex with a ChatGPT account").
DEFAULT_MODEL = "gpt-6.1-sol"
COPIED_SETTINGS = ("gauss_executable", "docs_root", "workspace_parent", "default_runner", "default_timeout_seconds")


def _toml_str(value: str) -> str:
    return json.dumps(value)  # a JSON string is a valid TOML basic string


def setup(eval_dir: Path, inputs: list[str]) -> int:
    """Create `<eval>/home/.gauss-ai/config.json`, `<eval>/data/input/`
    (fresh copies), `<eval>/data/output/` and an empty `<eval>/work/`. The
    docs root, executable and workspace parent are copied from the user's own
    gauss-ai config; the analysis folder is the eval's own."""
    user_config = Path.home() / ".gauss-ai" / "config.json"
    base = json.loads(user_config.read_text(encoding="utf-8")) if user_config.exists() else {}
    data = eval_dir / "data"
    (data / "input").mkdir(parents=True, exist_ok=True)
    (data / "output").mkdir(parents=True, exist_ok=True)
    work = eval_dir / "work"
    work.mkdir(parents=True, exist_ok=True)
    if any(work.iterdir()):
        print(f"refusing: {work} is not empty")
        return 1
    for f in inputs:
        shutil.copy2(f, data / "input")
    config = {k: v for k, v in base.items() if k in COPIED_SETTINGS}
    config["analysis_folder"] = str(data)
    home = eval_dir / "home" / ".gauss-ai"
    home.mkdir(parents=True, exist_ok=True)
    (home / "config.json").write_text(json.dumps(config, indent=2), encoding="utf-8")
    print(json.dumps(config, indent=2))
    print("inputs:", sorted(p.name for p in (data / "input").iterdir()))
    return 0


def parse_tasks(path: Path) -> list[tuple[str, str]]:
    tasks, current, lines = [], None, []
    for line in path.read_text(encoding="utf-8-sig").splitlines():
        m = re.match(r"^##\s+(\S+)\s*$", line)
        if m:
            if current:
                tasks.append((current, "\n".join(lines).strip()))
            current, lines = m.group(1), []
        elif current:
            lines.append(line)
    if current:
        tasks.append((current, "\n".join(lines).strip()))
    return [(i, t) for i, t in tasks if t]


def codex_command(codex: list[str], eval_dir: Path, out: Path, task_id: str, model: str, sandbox: str,
                  server_command: str) -> list[str]:
    home = str(eval_dir / "home")
    env_table = "{" + ", ".join(f"{k} = {_toml_str(home)}" for k in ("USERPROFILE", "HOME")) + "}"
    return [
        *codex, "exec", "--json", "--ephemeral", "--skip-git-repo-check", "--ignore-user-config",
        "-m", model, "-s", sandbox, "-C", str(eval_dir / "work"),
        "-o", str(out / f"{task_id}-final.md"),
        "-c", f"mcp_servers.gauss-ai.command={_toml_str(server_command)}",
        "-c", f"mcp_servers.gauss-ai.env={env_table}",
        "-c", "mcp_servers.gauss-ai.startup_timeout_sec=60",
        # No network beyond the model itself (plan §5 decision 1). Without
        # this, batch 1's 86.5 opened FRED through Codex's built-in web
        # search and reported a regression no code ever computed.
        "-c", 'web_search="disabled"',
    ]


def resolve_codex(given: str | None) -> list[str]:
    """The argv prefix that starts Codex. On Windows the npm install puts
    `codex`/`codex.cmd`/`codex.ps1` shims on PATH; going through `cmd.exe`
    would re-parse the quotes and braces of the `-c` TOML values and the
    task text, so the shim's own target -- `node <npm>/node_modules/@openai/
    codex/bin/codex.js` -- is called directly instead."""
    if given:
        return [given]
    found = shutil.which("codex")
    if found and found.lower().endswith(".exe"):
        return [found]
    if found:
        script = Path(found).parent / "node_modules" / "@openai" / "codex" / "bin" / "codex.js"
        node = shutil.which("node")
        if script.exists() and node:
            return [node, str(script)]
    raise SystemExit("codex not found; pass --codex PATH")


def _gauss_ai_calls(transcript: Path) -> int:
    count = 0
    for line in transcript.read_text(encoding="utf-8").splitlines():
        if not line.startswith("{"):
            continue
        event = json.loads(line)
        item = event.get("item") or {}
        if event.get("type") == "item.completed" and item.get("type") == "mcp_tool_call" \
                and item.get("server") == "gauss-ai":
            count += 1
    return count


def run(eval_dir: Path, tasks_path: Path, out: Path, only: set[str] | None, model: str, sandbox: str,
        codex: list[str], preamble: str | None = None) -> int:
    if os.environ.get("GAUSS_AI_MCP_ALLOW_REAL_GAUSS"):
        print("refusing: GAUSS_AI_MCP_ALLOW_REAL_GAUSS is set in this environment; automated runs never execute")
        return 1
    server = shutil.which("gauss-ai-mcp")
    if not server:
        print("gauss-ai-mcp not found on PATH")
        return 1
    out.mkdir(parents=True, exist_ok=True)
    tasks = [(i, t) for i, t in parse_tasks(tasks_path) if only is None or i in only]
    versions = {
        "codex": subprocess.run([*codex, "--version"], capture_output=True, text=True).stdout.strip(),
        "gauss_ai": subprocess.run(["gauss-ai", "version"], capture_output=True, text=True).stdout.splitlines()[0],
    }
    manifest = {"model": model, "sandbox": sandbox, "versions": versions, "server": server, "preamble": preamble,
                "tasks": []}
    for task_id, text in tasks:
        cmd = codex_command(codex, eval_dir, out, task_id, model, sandbox, server)
        started = time.time()
        print(f"--- {task_id}: {text[:70]}")
        with open(out / f"{task_id}.jsonl", "w", encoding="utf-8") as stdout, \
                open(out / f"{task_id}.stderr.txt", "w", encoding="utf-8") as stderr:
            p = subprocess.run(cmd + [f"{preamble}\n\n{text}" if preamble else text], stdout=stdout, stderr=stderr, stdin=subprocess.DEVNULL,
                               text=True, encoding="utf-8", errors="replace", timeout=1800)
        entry = {"id": task_id, "text": text, "exit": p.returncode, "seconds": round(time.time() - started, 1),
                 "command": cmd, "gauss_ai_calls": _gauss_ai_calls(out / f"{task_id}.jsonl")}
        manifest["tasks"].append(entry)
        (out / "manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf-8")
        print(f"    exit {p.returncode} in {entry['seconds']} s, {entry['gauss_ai_calls']} gauss-ai call(s)")
        if entry["gauss_ai_calls"] == 0:
            # Batch 2 of 86.x: one task (86.0) ran with no gauss-ai tools
            # loaded at all (a quarter of the usual input tokens, nothing on
            # stderr); two reruns were normal. Flagged, never retried here:
            # the grader decides whether it was the client's choice or a
            # startup failure, and records any rerun as one.
            print("    WARNING: no gauss-ai call; check whether the MCP server's tools loaded")
        if p.returncode != 0:
            print(f"stopping: infrastructure error; see {out / (task_id + '.stderr.txt')}")
            return 1
    return 0


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("setup")
    s.add_argument("eval_dir")
    s.add_argument("--input", action="append", default=[])
    r = sub.add_parser("run")
    r.add_argument("eval_dir")
    r.add_argument("tasks")
    r.add_argument("out_dir")
    r.add_argument("--only")
    r.add_argument("--model", default=DEFAULT_MODEL)
    r.add_argument("--sandbox", default="read-only")
    r.add_argument("--codex")
    r.add_argument("--preamble", help="a file whose text is sent before every task (recorded in the manifest)")
    a = ap.parse_args(argv)
    if a.cmd == "setup":
        return setup(Path(a.eval_dir).resolve(), a.input)
    only = set(a.only.split(",")) if a.only else None
    return run(Path(a.eval_dir).resolve(), Path(a.tasks), Path(a.out_dir).resolve(), only, a.model, a.sandbox, resolve_codex(a.codex),
               Path(a.preamble).read_text(encoding="utf-8-sig").strip() if a.preamble else None)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

