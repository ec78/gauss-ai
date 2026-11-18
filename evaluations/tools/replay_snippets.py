"""Replay every `gauss_validate_code` snippet of a live evaluation on two
versions of the validator, and optionally run the HEAD handoff candidates in
real GAUSS.

Planning: `planning/evaluation-automation.md` §2. A developer tool, not a
product module: it lives outside `scripts/`, so it is never packaged, and it is
never called from the automated test suite (which must not touch a real GAUSS
install or documentation checkout). It replaces the per-evaluation scratch
scripts of 85.x/86.x (`rv86.py`, `tg86.py`, `bnd86.py`), which re-implemented
the same three steps by hand each time:

1. pull the snippets a client submitted out of its transcript;
2. validate each on HEAD and on the previous release, to separate what the
   milestone changed from pre-existing behaviour (CLAUDE.md, 74.x);
3. re-run the approved code with `tgauss.exe -b` to compare.

Each version is validated in its own subprocess (`--worker`), with only that
version's `scripts/` on `sys.path`, so the two module trees can never mix in
one interpreter. The baseline comes from `git archive -o <tar> <ref> scripts`
and `tar -xf` -- the route that works on Windows, where piping `git archive`
into `tar` from PowerShell corrupts the stream.

Transcript formats:

- Claude Code session JSONL (`~/.claude/projects/<project>/*.jsonl`): an
  `assistant` record's `tool_use` block named `...gauss_validate_code`. Each
  real user message starts a new task, so snippets are grouped by the task
  that produced them.
- Codex `codex exec --json` event streams: their event shapes are not pinned
  by this repo, so they are searched structurally -- any object naming a
  `...gauss_validate_code` tool next to an argument object (or JSON string)
  holding `code`. One file is one task (the runner in §3 writes one file per
  task). Repeated events for one call (`item.started` / `item.completed`) are
  collapsed by call id, or by consecutive identical code when there is none.

usage:
  python evaluations/tools/replay_snippets.py TRANSCRIPT [TRANSCRIPT ...]
      --baseline v0.94.1 --docs-root DIR [--gauss-executable EXE]
      [--input-dir DIR] [--run] [--out PREFIX]
  python evaluations/tools/replay_snippets.py --self-check

`--input-dir` passes the analysis folder's `input/` as the file context, as
the MCP server does when an analysis folder is configured (v0.94.0+). It is
ignored for a baseline older than v0.94.0, which has no file context.

`--run` (manual only, touches real GAUSS) writes every snippet that is
`handoff_candidate` on HEAD into a fresh scratch directory, copies in every
file of `--input-dir` (a superset of what the real handoff copies in, which is
only the named files), runs `tgauss.exe -b`, and records the exit code, the
first `G####` error line and the files the run created.
"""
from __future__ import annotations

import argparse
import dataclasses
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parents[2]
TOOL_SUFFIX = "gauss_validate_code"
ID_KEYS = ("id", "call_id", "tool_use_id", "item_id")
NAME_KEYS = ("name", "tool", "tool_name")
ARG_KEYS = ("input", "arguments", "args", "params")


# --------------------------------------------------------------------------
# Transcript extraction
# --------------------------------------------------------------------------

def _records(path: Path) -> list[dict]:
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            out.append(value)
    return out


def _is_claude_code(records: list[dict]) -> bool:
    return any(r.get("type") in ("user", "assistant") and isinstance(r.get("message"), dict) for r in records)


def _user_text(record: dict) -> str | None:
    """The text of a real user message, or None for tool results, command
    wrappers and harness-injected meta records."""
    if record.get("type") != "user" or record.get("isMeta"):
        return None
    content = record["message"].get("content")
    if isinstance(content, str):
        text = content
    elif isinstance(content, list):
        if any(isinstance(b, dict) and b.get("type") == "tool_result" for b in content):
            return None
        text = "\n".join(b.get("text", "") for b in content if isinstance(b, dict) and b.get("type") == "text")
    else:
        return None
    text = text.strip()
    if not text or text.startswith("<"):
        return None
    return text


def _claude_snippets(records: list[dict], source: str) -> list[dict]:
    snippets, task, task_text, seen = [], 0, "", set()
    for r in records:
        text = _user_text(r)
        if text is not None:
            task += 1
            task_text = text
            continue
        if r.get("type") != "assistant":
            continue
        for block in r["message"].get("content") or []:
            if not (isinstance(block, dict) and block.get("type") == "tool_use"):
                continue
            if not str(block.get("name", "")).endswith(TOOL_SUFFIX):
                continue
            if block.get("id") in seen:
                continue
            seen.add(block.get("id"))
            code = (block.get("input") or {}).get("code")
            if isinstance(code, str):
                snippets.append({"source": source, "task": task, "task_text": task_text[:120], "code": code})
    return snippets


def _arguments(obj: dict) -> dict | None:
    for key in ARG_KEYS:
        value = obj.get(key)
        if isinstance(value, str):
            try:
                value = json.loads(value)
            except json.JSONDecodeError:
                continue
        if isinstance(value, dict) and isinstance(value.get("code"), str):
            return value
    return None


def _walk(value, found: list[tuple[str | None, str]]) -> None:
    if isinstance(value, dict):
        if any(str(value.get(k, "")).endswith(TOOL_SUFFIX) for k in NAME_KEYS):
            args = _arguments(value)
            if args is not None:
                call_id = next((str(value[k]) for k in ID_KEYS if value.get(k)), None)
                found.append((call_id, args["code"]))
                return
        for child in value.values():
            _walk(child, found)
    elif isinstance(value, list):
        for child in value:
            _walk(child, found)


def _generic_snippets(records: list[dict], source: str) -> list[dict]:
    found: list[tuple[str | None, str]] = []
    for r in records:
        _walk(r, found)
    snippets, seen_ids, last = [], set(), None
    for call_id, code in found:
        if call_id is not None:
            if call_id in seen_ids:
                continue
            seen_ids.add(call_id)
        elif code == last:
            continue
        last = code
        snippets.append({"source": source, "task": Path(source).stem, "task_text": "", "code": code})
    return snippets


def extract_snippets(path: Path) -> list[dict]:
    records = _records(path)
    if _is_claude_code(records):
        return _claude_snippets(records, path.name)
    return _generic_snippets(records, path.name)


# --------------------------------------------------------------------------
# Worker: validate with one version's scripts/ on sys.path
# --------------------------------------------------------------------------

def _plain(value):
    if dataclasses.is_dataclass(value):
        return {k: _plain(v) for k, v in dataclasses.asdict(value).items()}
    if isinstance(value, (list, tuple)):
        return [_plain(v) for v in value]
    if hasattr(value, "value") and not isinstance(value, (str, int, float)):
        return value.value
    return value


def worker(scripts_dir: str, snippets_path: str, out_path: str, docs_root: str,
           gauss_executable: str | None, input_dir: str | None) -> None:
    sys.path.insert(0, scripts_dir)
    import gauss_conversation_engine as engine  # noqa: E402

    installation = None
    if gauss_executable:
        try:
            import gauss_installed_libraries as libraries  # noqa: E402
            installation = libraries.load_installation(gauss_executable)
        except ImportError:  # a baseline older than v0.92.0
            installation = None
    kwargs = {}
    if installation is not None:
        kwargs["installation"] = installation
    if input_dir and hasattr(engine, "file_access_context"):
        kwargs["file_context"] = engine.file_access_context(
            input_dir=input_dir, gauss_dir=getattr(installation, "gauss_dir", None),
        )
    results = []
    for snippet in json.loads(Path(snippets_path).read_text(encoding="utf-8")):
        r = engine.validate_code(snippet["code"], docs_root=docs_root, **kwargs)
        pre = r.pre_execution
        state = r.handoff_readiness.state
        results.append({
            "state": getattr(state, "value", str(state)),
            "reasons": list(r.handoff_readiness.reasons),
            "rejected_reason": getattr(r, "rejected_reason", None),
            "coverage_gaps": _plain(getattr(pre, "coverage_gaps", ()) if pre else ()),
            "role_checks": [
                {"symbol": c.symbol, "position": c.position, "status": _plain(c.status),
                 "origin": _plain(getattr(c, "origin", "")), "cause": _plain(getattr(c, "unknown_cause", None))}
                for c in (getattr(pre, "parameter_role_checks", ()) if pre else ())
            ],
            "system_statements": [
                {"name": f.name, "category": f.category, "detail": getattr(f, "detail", "")}
                for f in (getattr(pre, "system_statements", ()) if pre else ())
            ],
        })
    Path(out_path).write_text(json.dumps(results, indent=1), encoding="utf-8")


def _run_worker(scripts_dir: Path, snippets_path: Path, out_path: Path, args) -> list[dict]:
    cmd = [sys.executable, str(Path(__file__).resolve()), "--worker", str(scripts_dir), str(snippets_path),
           str(out_path), "--docs-root", args.docs_root]
    if args.gauss_executable:
        cmd += ["--gauss-executable", args.gauss_executable]
    if args.input_dir:
        cmd += ["--input-dir", args.input_dir]
    subprocess.run(cmd, check=True)
    return json.loads(out_path.read_text(encoding="utf-8"))


def _baseline_scripts(ref: str, work: Path) -> Path:
    tar = work / "baseline.tar"
    subprocess.run(["git", "-C", str(REPO), "archive", "-o", str(tar), ref, "scripts"], check=True)
    dest = work / "baseline"
    dest.mkdir()
    subprocess.run(["tar", "-xf", str(tar), "-C", str(dest)], check=True)
    return dest / "scripts"


# --------------------------------------------------------------------------
# Optional real-GAUSS run
# --------------------------------------------------------------------------

def run_in_gauss(code: str, exe: str, input_dir: str | None, work: Path, n: int) -> dict:
    d = work / f"run{n:02d}"
    d.mkdir()
    if input_dir:
        for f in Path(input_dir).iterdir():
            if f.is_file():
                shutil.copy(f, d)
    before = set(os.listdir(d))
    (d / "s.gss").write_text(code + "\n", encoding="utf-8")
    try:
        p = subprocess.run([exe, "-b", "s.gss"], cwd=d, capture_output=True, text=True, timeout=180)
    except subprocess.TimeoutExpired:
        return {"exit": None, "error": "timeout after 180 s", "created": []}
    text = (p.stdout or "") + (p.stderr or "")
    errors = re.findall(r"G\d{4}[^\n]*", text)
    created = sorted(set(os.listdir(d)) - before - {"s.gss"})
    return {"exit": p.returncode, "error": errors[0].strip() if errors else "", "created": created,
            "tail": text.strip().splitlines()[-4:]}


# --------------------------------------------------------------------------
# Report
# --------------------------------------------------------------------------

def _gap_causes(result: dict) -> str:
    causes = sorted({g.get("cause", "") for g in result["coverage_gaps"]} - {""})
    return ", ".join(causes)


def _cell(text: str) -> str:
    return text.replace("|", "\\|").replace("\n", " ")


def markdown(rows: list[dict], baseline: str, run: bool) -> str:
    head = f"| n | task | {baseline} | HEAD | moved | HEAD gap causes |"
    rule = "|---|---|---|---|---|---|"
    if run:
        head += " GAUSS |"
        rule += "---|"
    lines = [head, rule]
    for row in rows:
        moved = "**yes**" if row["baseline"]["state"] != row["head"]["state"] else (
            "reasons" if row["baseline"]["reasons"] != row["head"]["reasons"] else "")
        line = (f"| {row['n']} | {_cell(str(row['task']))} | {row['baseline']['state']} | {row['head']['state']} "
                f"| {moved} | {_cell(_gap_causes(row['head']))} |")
        if run:
            g = row.get("gauss")
            line += " " + (_cell(f"exit {g['exit']}" + (f"; {g['error']}" if g["error"] else "")) if g else "") + " |"
        lines.append(line)
    return "\n".join(lines) + "\n"


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("transcripts", nargs="*")
    ap.add_argument("--baseline")
    ap.add_argument("--docs-root")
    ap.add_argument("--gauss-executable")
    ap.add_argument("--input-dir")
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--out", default="replay")
    ap.add_argument("--self-check", action="store_true")
    ap.add_argument("--worker", nargs=3, metavar=("SCRIPTS", "SNIPPETS", "OUT"))
    args = ap.parse_args(argv)

    if args.self_check:
        return self_check()
    if args.worker:
        worker(*args.worker, args.docs_root, args.gauss_executable, args.input_dir)
        return 0
    if not (args.transcripts and args.baseline and args.docs_root):
        ap.error("TRANSCRIPT, --baseline and --docs-root are required")
    if args.run and not args.gauss_executable:
        ap.error("--run needs --gauss-executable")

    snippets = [s for t in args.transcripts for s in extract_snippets(Path(t))]
    print(f"{len(snippets)} snippets from {len(args.transcripts)} transcript(s)")
    if not snippets:
        return 1
    with tempfile.TemporaryDirectory(prefix="gauss-replay-") as tmp:
        work = Path(tmp)
        snippets_path = work / "snippets.json"
        snippets_path.write_text(json.dumps(snippets), encoding="utf-8")
        head = _run_worker(REPO / "scripts", snippets_path, work / "head.json", args)
        base = _run_worker(_baseline_scripts(args.baseline, work), snippets_path, work / "base.json", args)
        rows = []
        for n, (s, h, b) in enumerate(zip(snippets, head, base), 1):
            row = {"n": n, "source": s["source"], "task": s["task"], "task_text": s["task_text"], "code": s["code"],
                   "baseline": b, "head": h}
            if args.run and h["state"] == "handoff_candidate":
                row["gauss"] = run_in_gauss(s["code"], args.gauss_executable, args.input_dir, work, n)
            rows.append(row)
    Path(args.out + ".json").write_text(json.dumps(rows, indent=1), encoding="utf-8")
    Path(args.out + ".md").write_text(markdown(rows, args.baseline, args.run), encoding="utf-8")
    moved = sum(r["baseline"]["state"] != r["head"]["state"] for r in rows)
    print(f"{moved} state move(s); wrote {args.out}.json and {args.out}.md")
    return 0


# --------------------------------------------------------------------------
# Self-check: the extractors on synthetic transcripts (no GAUSS, no docs)
# --------------------------------------------------------------------------

def self_check() -> int:
    failures = []

    def check(name: str, condition: bool) -> None:
        print(("ok   " if condition else "FAIL ") + name)
        if not condition:
            failures.append(name)

    claude = [
        {"type": "user", "message": {"role": "user", "content": "<command-name>/mcp</command-name>"}},
        {"type": "user", "message": {"role": "user", "content": "Compute the mean of a column."}},
        {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "id": "t1", "name": "mcp__gauss-ai__gauss_validate_code",
             "input": {"session_id": "s", "code": "x = meanc(y);"}}]}},
        {"type": "user", "message": {"content": [{"type": "tool_result", "tool_use_id": "t1", "content": "{}"}]}},
        {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "id": "t1", "name": "mcp__gauss-ai__gauss_validate_code",
             "input": {"session_id": "s", "code": "x = meanc(y);"}}]}},
        {"type": "user", "isMeta": True, "message": {"content": "meta"}},
        {"type": "user", "message": {"content": [{"type": "text", "text": "Now sort it."}]}},
        {"type": "assistant", "message": {"content": [
            {"type": "tool_use", "id": "t2", "name": "mcp__gauss-ai__gauss_search_docs", "input": {"query": "sort"}},
            {"type": "tool_use", "id": "t3", "name": "mcp__gauss-ai__gauss_validate_code",
             "input": {"code": "z = sortc(y, 1);"}}]}},
    ]
    with tempfile.TemporaryDirectory() as tmp:
        p = Path(tmp) / "claude.jsonl"
        p.write_text("\n".join(json.dumps(r) for r in claude) + "\n", encoding="utf-8")
        got = extract_snippets(p)
        check("claude: two snippets, duplicate id collapsed", [s["code"] for s in got] == ["x = meanc(y);",
                                                                                         "z = sortc(y, 1);"])
        check("claude: tasks numbered by real user messages", [s["task"] for s in got] == [1, 2])
        check("claude: task text kept", got[1]["task_text"] == "Now sort it.")

        codex = [
            {"type": "thread.started"},
            {"type": "item.started", "item": {"id": "c1", "type": "mcp_tool_call", "server": "gauss-ai",
                                             "tool": "gauss_validate_code",
                                             "arguments": {"session_id": "s", "code": "a = 1;"}}},
            {"type": "item.completed", "item": {"id": "c1", "type": "mcp_tool_call", "server": "gauss-ai",
                                               "tool": "gauss_validate_code",
                                               "arguments": {"session_id": "s", "code": "a = 1;"}}},
            {"type": "item.completed", "item": {"type": "function_call", "name": "gauss_validate_code",
                                               "arguments": json.dumps({"code": "b = 2;"})}},
            {"type": "item.completed", "item": {"type": "function_call", "name": "gauss_search_docs",
                                               "arguments": json.dumps({"query": "code"})}},
        ]
        q = Path(tmp) / "task03.jsonl"
        q.write_text("\n".join(json.dumps(r) for r in codex) + "\nnot json\n", encoding="utf-8")
        got = extract_snippets(q)
        check("codex: started/completed collapsed by id; string arguments parsed",
              [s["code"] for s in got] == ["a = 1;", "b = 2;"])
        check("codex: one file is one task", {s["task"] for s in got} == {"task03"})

    rows = [{"n": 1, "task": 1, "baseline": {"state": "review_required", "reasons": ["r"], "coverage_gaps": []},
             "head": {"state": "handoff_candidate", "reasons": [], "coverage_gaps": [{"cause": "c|d"}]}}]
    md = markdown(rows, "v0.94.1", False)
    check("markdown: a state move is marked and pipes are escaped", "**yes**" in md and "c\\|d" in md)
    print("self-check:", "PASS" if not failures else f"{len(failures)} failure(s)")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
