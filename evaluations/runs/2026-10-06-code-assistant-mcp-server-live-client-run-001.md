# Evaluation Result

Date: 2026-10-06
Evaluator: Claude (v0.79.0 MCP Server milestone, driven live through a real connected Claude Code session -- not a transcript replayed after the fact)
Agent Version: Current repository state on 2026-10-06 (`v0.79.0`, tag/release already pushed at session start)
Prompt ID: 69.1
Prompt Category: MCP Server Live-Client Validation
Prompt Text:

Via a real Claude Code session with `gauss-ai` registered as a project-scoped MCP server (this
repository's own `.mcp.json`, `gauss-ai-mcp` running over stdio, installed via `pip install -e
".[mcp]"`): `gauss_chat_start(runner="fake")` -> `gauss_chat_ask("Write exactly one minimal GAUSS
statement, no comments, no explanation, no separate variable for the matrix: y = invpd({2 1, 1
2}); print y;")` -> `gauss_execution_prepare` -> human approval ('yes') relayed through the
connected client -> `gauss_execution_decide("yes")` -> `gauss_chat_close`.

Objective: Prove the real MCP wire protocol (tool discovery, JSON schema negotiation, session
state held correctly across separate tool calls) works end to end through an actual connected
client -- something the automated `test_gauss_mcp_server.py` suite cannot exercise, since it calls
every tool function directly, never through a real transport.
Evidence source: A real, locally running `gauss-ai-mcp` process, connected to this exact Claude
Code session via the repository's own `.mcp.json`. Real local Ollama model (`qwen2.5-coder:7b`),
real configured documentation checkout for grounding. `runner="fake"` was used deliberately for
the execution step, since this scenario's purpose is validating the MCP transport/session
mechanics, not re-validating real-GAUSS execution (already covered by `68.x`) or generation
quality (already covered by `61.x`-`67.x`).
Model provider: **Real ollama (`qwen2.5-coder:7b`)** for the chat turn; fake runner for the
execution step.

Session setup: The user reloaded the VS Code window after `.mcp.json` was committed in `v0.79.0`;
Claude Code's MCP panel showed `gauss-ai -- Connected` and all 9 tools (`gauss_chat_start`,
`gauss_chat_ask`, `gauss_chat_reset`, `gauss_chat_close`, `gauss_execution_prepare`,
`gauss_execution_decide`, `gauss_repair_start`, `gauss_repair_command`, `gauss_repair_close`)
appeared as available MCP tools in a fresh session. A separate attempt to reach the server from
claude.ai's web chat correctly found no such server available -- expected and confirmed, not a
defect: a local stdio MCP server is reachable only from a local client (Claude Code/Desktop)
running on the same machine, never from a cloud-hosted web chat, which has no access to any
process on the user's machine. claude.ai's own "connectors" (Gmail, Calendar, Drive) are a
separate, unrelated, remote/OAuth-based mechanism.

Captured output (verbatim tool results from the live session):

```
gauss_chat_start(runner="fake") ->
{"session_id":"b513bb3e37644922872861927b5e13bf","provider":"ollama","model":"qwen2.5-coder:7b","docs_root_configured":true}

gauss_chat_ask(...) -> (after two earlier turns in the same session that reached only
REVIEW_REQUIRED -- see Defects below)
{"text":"...\n\n```gauss\nprint invpd({2 1, 1 2});\n```\n\n(This example has not been executed in this conversation.)",
 "intent":"qa","grounded":true,"grounding_status":"partially_grounded","grounding_source":"official_docs",
 "grounding_topic":"invpd","generated_code":["print invpd({2 1, 1 2});"],
 "handoff_readiness":{"state":"handoff_candidate","reasons":[
   "generated code is grounded and symbol-supported","documented call signatures are compatible",
   "syntax was validated with no known violation","no documented precondition is known to be violated",
   "validation coverage is broad"]},
 "execution_offer_eligible":true}

gauss_execution_prepare(session_id) ->
{"request_id":"f7184eac-d0f2-4b90-8414-24b4936570bf",
 "digest":"ab98c5367f140adc76c7169252a66dda2564e1f38afe7c6eab1fc18f9647d5fd",
 "rendered_prompt":"Ready for controlled execution.\n\nCode:\n```gauss\nprint invpd({2 1, 1 2});\n```\n\nRunner: fake (no real GAUSS invocation)\n...\nApprove this exact execution using fake (no real GAUSS invocation) with a 30-second timeout? [yes/no]"}

[rendered_prompt relayed verbatim to the human; human replied "Yes" in the actual conversation]

gauss_execution_decide(session_id, "yes") ->
{"outcome":"success","launched":true,"blocked_reason":null,
 "result_digest":"8f3ff22c89aae4586c174b8b968cfe2893f747103f38fff24f7e2c071e71fd9f",
 "rendered":"Execution completed.\n\nstdout:\n(fake runner: no real GAUSS was invoked)\n\nstderr:\n(none)\n\nGAUSS exit status: 0\n...",
 "evidence":{"runner":"fake","gauss_ran":false,"executed":true,"execution_status":"completed","exit_code":0,
   "stdout_text":"(fake runner: no real GAUSS was invoked)","stderr_text":"","timed_out":false}}

gauss_chat_close(session_id) -> {"session_id":"b513bb3e37644922872861927b5e13bf","closed":true}
```

Expected behavior: Real local-model answer grounded in real official documentation; reaching
`HANDOFF_CANDIDATE` makes `execution_offer_eligible: true`; `gauss_execution_prepare` returns the
exact code and a digest for a human to review before anything executes; approval is read from the
actual human (relayed through the connected client, not asserted by any tool or model on the
human's behalf); `gauss_execution_decide` returns `outcome: "success"` with fake-runner evidence,
no real GAUSS touched.

Observed behavior: Exactly as expected, with one additional, genuinely interesting finding (see
Defects below). Two earlier turns in the same live session ("What does the meanc function do?" and
a `meanc`-based code-generation request) correctly stayed `grounded`/`review_required` respectively
and did not reach `HANDOFF_CANDIDATE` -- real, honest evidence that reaching candidacy is not
trivial even against a real model and real docs, consistent with `66.x`-`67.x`'s own prior
findings that direct-literal-call, no-intermediate-variable phrasing is what reliably reaches
`HANDOFF_CANDIDATE`.

Defects found: One, incidental, already-disclosed, not new. The prompt that reached
`HANDOFF_CANDIDATE` live here used a bare `print invpd(...)` call -- exactly the `v0.74.0`-era
`extract_generated_calls(...)` gap already documented in `KNOWN_LIMITATIONS.md` and first found
live during `v0.78.0`'s own `68.8` evaluation: a call wrapped directly in a bare `print f(...)`
statement is not extracted by the call/precondition/parameter-role checkers, so this particular
`HANDOFF_CANDIDATE` verdict was reached partly because nothing was actually checked against the
call, not because every dimension was positively verified. This reproduced the identical,
previously-known limitation live again, through the new MCP transport this time, confirming the
gap is a property of the shared `gauss_pre_execution_validation.py` module (unmodified by
`v0.79.0`) rather than anything specific to either front-end. Not a new defect; not in scope for
`v0.79.0`'s own module to fix (it performs no call/symbol extraction of any kind). The MCP
transport layer itself -- tool registration, session-state handling, the two-step
prepare/decide handoff, and the real-GAUSS operator gate's absence from `.mcp.json`'s `env` (left
correctly empty, so a `runner="gauss"` request from this session would have been refused by
`gauss_execution_prepare`'s `GAUSS_AI_MCP_ALLOW_REAL_GAUSS` check, not exercised in this scenario
since `runner="fake"` was used) -- showed no defect.

Pass/fail: Pass
Defect severity: None in the component under test (the MCP transport). Informational-only
reproduction of a pre-existing, already-disclosed, out-of-scope validation-coverage gap.
Remediation: None required for this milestone; the gap remains tracked in `KNOWN_LIMITATIONS.md`
under its original `v0.74.0`/`v0.78.0` entries, not duplicated here.

Overall Score: 4.0
Decision: Pass
