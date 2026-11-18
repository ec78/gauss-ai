"""Summarize a `run_codex_tasks.py` batch for grading: per task, every
gauss-ai tool call with its key argument and its verdict, every shell command
the client ran, and token usage.

Planning: `planning/evaluation-automation.md` §3 ("Grading"). It only lists
what is in the transcripts. Grading stays with the developing session.
Commands are listed in full because the live-evaluation rules require
disclosing:

- every way the client stepped outside gauss-ai (86.5's `curl`, a Desktop
  write);
- every time the client read gauss-ai's own source, which the read-only
  sandbox does not prevent.

Commands that reach outside the work folder are flagged mechanically:

- any absolute path other than the work folder or the system's own shell
  binaries;
- any `http(s)://` URL.

A flag is a pointer for the grader to read the command, not a verdict.

usage: python evaluations/tools/summarize_codex_run.py OUT_DIR [--work DIR] > summary.md
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

_ABS_PATH = re.compile(r"(?i)\b[a-z]:[\\/][^\s'\"|;]*")
_URL = re.compile(r"https?://\S+")
_SYSTEM = re.compile(r"(?i)^[a-z]:[\\/]windows[\\/]")


def _result_json(item: dict) -> dict:
    for block in ((item.get("result") or {}).get("content") or []):
        if block.get("type") == "text":
            try:
                return json.loads(block["text"])
            except (json.JSONDecodeError, TypeError):
                return {}
    return {}


def _call_line(item: dict) -> str:
    tool = item.get("tool", "")
    args = item.get("arguments") or {}
    res = _result_json(item)
    detail = ""
    if tool == "gauss_validate_code":
        state = (res.get("handoff_readiness") or {}).get("state") or res.get("error", "?")
        causes = sorted({g.get("cause", "") for g in res.get("coverage_gaps") or []} - {""})
        first = (args.get("code") or "").strip().splitlines()
        detail = f"**{state}**" + (f" ({', '.join(causes)})" if causes else "") + (f" `{first[0][:60]}`" if first else "")
    elif tool == "gauss_search_docs":
        detail = f"`{args.get('query', '')}`"
    elif tool == "gauss_read_doc":
        detail = f"`{args.get('page') or args.get('symbol') or args}`"
    elif tool == "gauss_execution_prepare":
        detail = res.get("error") or ("prompt returned" if res.get("rendered_prompt") else "?")
    elif tool == "gauss_session_start":
        detail = f"real_gauss_allowed={res.get('real_gauss_allowed')}"
    if item.get("error"):
        detail += f" error: {item['error']}"
    return f"- `{tool}` {detail}".rstrip()


def _flags(command: str, work: str | None) -> list[str]:
    flags = []
    for path in _ABS_PATH.findall(command):
        # Codex records Windows commands with doubled backslashes
        # (`"C:\\WINDOWS\\System32\\...powershell.exe"`).
        path = re.sub(r"\\+", r"\\", path)
        if _SYSTEM.match(path):
            continue
        if work and path.lower().replace("/", "\\").startswith(work.lower().replace("/", "\\")):
            continue
        flags.append(f"path `{path}`")
    flags += [f"URL `{u}`" for u in _URL.findall(command)]
    return flags


def summarize(out_dir: Path, work: str | None) -> str:
    manifest = json.loads((out_dir / "manifest.json").read_text(encoding="utf-8"))
    lines = [f"# Codex batch `{out_dir.name}`", "",
             f"Model `{manifest['model']}`, sandbox `{manifest['sandbox']}`, {manifest['versions']['codex']}, "
             f"{manifest['versions']['gauss_ai']}.", ""]
    for task in manifest["tasks"]:
        tid = task["id"]
        events = [json.loads(line) for line in (out_dir / f"{tid}.jsonl").read_text(encoding="utf-8").splitlines()
                  if line.strip().startswith("{")]
        items = [e["item"] for e in events if e.get("type") == "item.completed" and "item" in e]
        usage = next((e.get("usage") for e in events if e.get("type") == "turn.completed"), {}) or {}
        lines += [f"## {tid}", "", f"> {task['text']}", "",
                  f"exit {task['exit']}, {task['seconds']} s, {usage.get('input_tokens', '?')} input / "
                  f"{usage.get('output_tokens', '?')} output tokens", ""]
        calls = [i for i in items if i.get("type") == "mcp_tool_call"]
        commands = [i for i in items if i.get("type") == "command_execution"]
        other = sorted({i.get("type") for i in items} - {"mcp_tool_call", "command_execution", "agent_message",
                                                          "reasoning"})
        lines.append(f"**gauss-ai calls ({len(calls)}):**")
        lines += [_call_line(i) for i in calls] or ["- none"]
        lines += ["", f"**Shell commands ({len(commands)}):**"]
        for c in commands:
            flags = _flags(c.get("command", ""), work)
            lines.append(f"- exit {c.get('exit_code')}: `{c.get('command', '')[:200]}`"
                         + (f" -- **outside:** {', '.join(flags)}" if flags else ""))
        if not commands:
            lines.append("- none")
        if other:
            lines += ["", f"**Other item types:** {', '.join(other)}"]
        lines.append("")
    return "\n".join(lines)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("out_dir")
    ap.add_argument("--work")
    a = ap.parse_args(argv)
    sys.stdout.reconfigure(encoding="utf-8")
    print(summarize(Path(a.out_dir), a.work))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
