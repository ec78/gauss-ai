# Controlled Execution Handoff

**Status: `v0.78.0`.** Extends [docs/execution-handoff-readiness.md](execution-handoff-readiness.md), [docs/pre-execution-validation.md](pre-execution-validation.md), and [docs/conversational-code-generation.md](conversational-code-generation.md) — read those first. This is the **first** milestone in which conversationally generated GAUSS code can actually be executed. It adds one narrow, explicit, user-consented bridge from a `HANDOFF_CANDIDATE` conversational answer to the **existing** GAUSS execution adapter (`gauss_execution_adapter.GaussExecutionAdapter`, unmodified). It does not add any other execution path, and it does not change how `HANDOFF_CANDIDATE`/`REVIEW_REQUIRED`/`NOT_READY` are computed (`gauss_pre_execution_validation.py` is unmodified by this milestone).

## What this is — and what it is not

This is **not** a general code-execution feature. It is a single, auditable, single-use handoff:

    conversational request -> model generates code -> deterministic validation -> HANDOFF_CANDIDATE
        -> ExecutionHandoffRequest -> shown to you exactly -> explicit "yes"/"no"
        -> ExecutionHandoffApproval -> re-validated -> existing GAUSS execution adapter
        -> ExecutionEvidence -> ConversationalExecutionResult -> shown to you exactly

It is **not**:
- Arbitrary code execution — only code that has already reached `HANDOFF_CANDIDATE` (the strongest deterministic evidence level; see execution-handoff-readiness.md) can even be offered.
- Source-file execution — the code is run as an ephemeral inline snippet in a fresh temporary workspace, never a file in your project.
- Standing permission — every single execution requires its own fresh, explicit "yes." Nothing is ever remembered across requests, turns, or sessions.
- Proof of correctness — a successful run proves the code executed; it never proves the result is statistically or methodologically correct.
- A repair mechanism — a failed execution is reported honestly, with no retry and no automatic fix. Repairing code remains a separate, unstarted, future milestone.

## The consent contract

Before you can approve anything, you see, in full:

- The **exact** code that will run (never summarized, never truncated).
- The **runner** (`fake` for a local demo/no-GAUSS-installed session, or `GAUSS` for the real `tgauss.exe`).
- The **executable path**, when a real runner is used.
- The **timeout**.
- Where the code **runs**: a new temporary directory, deleted after the run (since `v0.87.0`; earlier prompts showed a "Workspace parent" line, which the run never used).
- The request's **digest** (a SHA-256 fingerprint over every field that affects execution).
- An explicit statement that the code has **not yet run**, and that success will not prove methodological correctness.

You then answer a narrow yes/no question. Only `yes` or `approve` (case-insensitive) counts as approval; only `no` or `decline` counts as a decline. Anything else (`"okay"`, `"sure"`, `"looks good"`, `"go ahead"`, ...) is treated as **unrecognized** — you are asked once more, and a second unrecognized answer safely cancels the request without executing anything.

Approval is bound to exactly one request, identified by its digest, and is **single-use**:

- A `yes` for one request never approves a different request, even if the code looks similar.
- Changing the code, the runner, the executable, or the timeout after approval invalidates the approval — the digest no longer matches, and execution is blocked before anything runs.
- A decline can never later be treated as approval.
- Once an execution attempt is actually made — success, GAUSS error, or timeout — that approval is consumed and cannot be used again. Running the same code again requires typing `run this` again and answering `yes` again, which creates a brand-new request and a brand-new approval.
- Through the MCP server (`v0.87.0`), `gauss_execution_decide` must name the `request_id` of the prompt the answer was given to. A prompt that a later `gauss_execution_prepare` replaced can no longer be approved, and an answer without a `request_id` approves nothing.
- Approval from a *repair* workflow, a *draft* workflow, or an *application* workflow (all pre-existing, unrelated approval stores in this repository) never counts as execution consent, and vice versa.

## What the model can and cannot do

The model (whichever `ModelProvider` you've configured — `fake`, `ollama`, or `anthropic`) may generate code and explain results. It cannot:

- Decide that code is eligible for handoff (that is `gauss_pre_execution_validation.compute_handoff_readiness(...)`, a fixed deterministic function it never calls and cannot influence).
- Approve or decline an execution (only your own literal `yes`/`no` response does that).
- Alter an approved request.
- Invoke GAUSS, retry GAUSS, or repair failed code.
- Reinterpret a failure as permission to try again.

This is enforced structurally, not by convention: `gauss_execution_handoff.py` (the new module implementing all of this) never imports `gauss_conversation_engine.py`, `gauss_chat_provider.py`, or `command_doc_lookup.py`, and none of those modules import anything execution-related. A model call happens only to generate the original code and, later, to discuss already-captured evidence — never to gate, approve, or perform an execution.

## No autonomous retry, no autonomous repair

After any execution attempt — success, GAUSS error, or timeout — the evidence is shown to you and nothing else happens automatically. You can ask follow-up questions ("Why did that fail?", "How would I fix this?") and get an ordinary advisory answer, but:

- Nothing regenerates code and executes it for you.
- Nothing feeds a failure into this repository's existing repair pipeline (`gauss-ai repair <file.gss>`) automatically.
- Running a fix requires the full path again from scratch: new generated code, new deterministic validation, a new `HANDOFF_CANDIDATE` verdict, a new request, and a new explicit approval.

## How execution actually happens (reuse, not reinvention)

This milestone adds **no new process-launch code**. Every real invocation routes through the exact same production path this repository has used since `v0.32.0`/`v0.33.0`: `gauss_execution_adapter.GaussExecutionAdapter.invoke(...)`, constructed with `gauss_execution_adapter.load_real_helper()` (which lazily reaches `gauss_code_execution.execute_gauss_code`, the same real-`tgauss.exe` helper the file-based guided-repair pipeline and `v0.77.0`'s own differential-validation harness already use). A fresh, ephemeral temporary directory (`tempfile.TemporaryDirectory(prefix="gauss_ai_handoff_")`) is used as the working directory for each attempt — never your project directory, never a file it writes into your workspace. The runner never knows or cares that the request originated conversationally.

Execution evidence (`stdout`, `stderr`, exit status, timeout/timing information) is captured using this repository's existing `gauss_execution_interpreter.ExecutionEvidence` type, unmodified — the new `ConversationalExecutionResult` type composes it rather than re-defining it.

## Failure categories

Every outcome is one of exactly ten categorical states — never a single undifferentiated "failed":

`NOT_ELIGIBLE`, `DECLINED`, `APPROVAL_MISMATCH`, `STALE_REQUEST`, `ALREADY_CONSUMED`, `EXECUTION_BLOCKED`, `EXECUTION_FAILED`, `EXECUTION_TIMEOUT`, `INFRASTRUCTURE_FAILURE`, `SUCCESS`.

A GAUSS-level error (bad syntax at runtime, a mathematically invalid operation, an out-of-bounds index, ...) is `EXECUTION_FAILED` and is reported with GAUSS's own real stdout/stderr — never smoothed over, never silently retried.

## Scope and limitations

- Only a single generated code block per answer is eligible for a handoff offer. An answer with multiple fenced code blocks is out of scope for `v0.78.0` (avoids inventing multi-snippet orchestration).
- Approval state is **process-local**: it lives only in memory for the current `gauss-ai` chat session and is discarded when the session ends. There is no durable, cross-session approval database.
- Execution success never implies methodological or statistical correctness — every rendered success result says so explicitly.
- The deterministic validators this milestone depends on (`gauss_pre_execution_validation.py`) have the same known, disclosed coverage limits documented in [docs/pre-execution-validation.md](pre-execution-validation.md) and [docs/gauss-syntax-validation.md](gauss-syntax-validation.md) — unchanged by this milestone.
- A pre-existing, unrelated limitation was found incidentally during this milestone's live evaluation: `gauss_pre_execution_validation.extract_generated_calls(...)` does not extract a call wrapped directly in a bare `print f(...)` statement (only an assignment form, `y = f(...); print y;`, is recognized). This affects only how thoroughly a `print`-wrapped call is precondition/signature-checked before reaching `HANDOFF_CANDIDATE` — it is not a defect in the handoff module itself, and is out of this milestone's scope to fix.

## Example conversation

```
> Use meanc on this matrix.
[Grounded in local official GAUSS documentation: meanc]
Validation:
- Function meanc: documented; signature: compatible
- Parameter checks:
  - meanc (x): match -- the argument's literal category (matrix) matches the documented parameter type
- Syntax: validated
- Execution eligibility: eligible_for_validation
- Validation coverage: symbols=complete, signature=complete, parameter roles=complete, preconditions=not_applicable, syntax=complete, predicted output=not_applicable
- Execution handoff readiness: handoff_candidate
  - generated code is grounded and symbol-supported
  - documented call signatures are compatible
  - syntax was validated with no known violation
  - no documented precondition is known to be violated
  - validation coverage is broad
  (This code has not been executed. This is not an approval to run it.)

```gauss
y = meanc({1 2, 3 4, 5 6});
print y;
```

(This example has not been executed in this conversation.)

This code has reached HANDOFF_CANDIDATE readiness -- the strongest deterministic evidence level. Type
'run this' or 'execute this' to review the exact code and execution details and explicitly approve a
single controlled execution.

> run this
Ready for controlled execution.

Code:
```gauss
y = meanc({1 2, 3 4, 5 6});
print y;
```

Runner: GAUSS
Executable: C:\gauss26\tgauss.exe
Timeout: 30 seconds
Runs in: a new temporary directory, deleted after the run
Request digest: 1991dc63b90f2a1b6e54c44afd24ac2892a15bc3679370cccd5e57668c822f04

This code has not been executed.
Execution success does not establish methodological validity.

Approve this exact execution using GAUSS with a 30-second timeout? [yes/no]
> yes
Execution completed.

stdout:
       3.0000000
       4.0000000

stderr:
GAUSS 26.1.4 ...

GAUSS exit status: 0

This confirms runtime execution only; it does not establish methodological correctness.

> run this
[a brand-new request/approval is built here -- typing "run this" again does NOT reuse the consumed
approval above; a fresh "yes" is required before this or any other code executes again]
```

## Related documentation

- [docs/execution-handoff-readiness.md](execution-handoff-readiness.md) — how `HANDOFF_CANDIDATE` is computed (unchanged by this milestone).
- [docs/pre-execution-validation.md](pre-execution-validation.md) — the underlying eligibility/signature/precondition checks.
- [docs/conversational-code-generation.md](conversational-code-generation.md) — how code is generated and grounded in the first place.
- `planning/v0.78-controlled-execution-handoff.md` — the full design record (digest fields, dependency direction, test plan).
