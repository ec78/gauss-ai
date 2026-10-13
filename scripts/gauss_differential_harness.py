"""Differential GAUSS syntax-validation harness (v0.77.0).

Compares this repository's deterministic syntax verdict
(`gauss_pre_execution_validation.validate_syntax`) against real GAUSS's own
acceptance/rejection of the same snippet, across the three corpus families
built by `build_differential_corpus.py` (plus a fourth, fresh-model-output
family from a live Ollama stress batch). See
`planning/v0.77.0-differential-syntax-validation.md` and
`docs/differential-syntax-validation.md` for the full design and
methodology.

THIS MODULE CAN INVOKE REAL GAUSS, but only through its own `main()`, and
only when BOTH of the same two explicit gates `test_gauss_execution_adapter_
real.py` already established are present simultaneously:

    1. The command-line flag --run-real-gauss
    2. The environment variable GAUSS_AI_ALLOW_REAL_EXECUTION=1

Real invocation is never performed by importing this module, by
`classify_gauss_outcome`/`classify_agreement` (both pure functions), or by
`run_corpus_item`/`run_corpus` when called with a fake `gauss_runner`
(exactly how every automated test in this file's own test module exercises
them). No conversational module imports this file, and this file never
imports any conversational module (`gauss_conversation_engine`,
`gauss_ai_chat`, `gauss_chat_provider`) -- it is evaluation infrastructure
only, per this milestone's own guardrails.

Real GAUSS invocation is routed through the SAME production path
`test_gauss_execution_adapter_real.py` already uses --
`gauss_execution_adapter.GaussExecutionAdapter` + `load_real_helper()` -- so
this module never spawns a subprocess itself and never duplicates
process-management logic (v0.77.0 Phase 3's own explicit requirement).

Syntax-oracle classification (Phase 3): a real GAUSS `execution_status` of
"failed" is further classified using `gauss_error_catalog.lookup_error(...)`
-- a matched, catalogued `PARSE_SYNTAX` error code means real GAUSS rejected
the snippet for syntax/parsing reasons; a matched, catalogued NON-syntax
category (`MATRIX_DIMENSION`, `RUNTIME_COMPUTATION`, `ARGUMENT_VALIDATION`,
`INDEXING_SUBSCRIPT`, `TYPE_MISMATCH`, `NUMERICAL`, `FILE_IO`,
`PACKAGE_OR_LIBRARY`) means the failure is real but NOT syntax evidence
(e.g. a dimension mismatch or an undefined-symbol runtime error is not
invalid syntax). An error code with NO catalog entry is recorded honestly
(best-effort outcome, never dropped) but tagged `classification_basis`
`"uncatalogued:..."` -- `classify_agreement(...)` below treats any
"uncatalogued" evidence as unusable for asserting AGREE/DISAGREE (-> always
`INCONCLUSIVE`), which is this module's concrete implementation of Phase 3's
"fail closed when uncertain," without inventing a numeric confidence score
(a categorical basis label only, per this repository's own deterministic-
state discipline).
"""

from __future__ import annotations

import argparse
import datetime as _datetime
import enum
import json
import os
import platform
import re
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

import gauss_error_catalog as catalog  # noqa: E402
import gauss_pre_execution_validation as validation_mod  # noqa: E402

_REPO_ROOT = _SCRIPT_DIR.parent
_CORPUS_DIR = _REPO_ROOT / "evaluations" / "differential_corpus"
_RESULTS_DIR = _REPO_ROOT / "evaluations" / "differential_runs"

#: v0.84.0: formerly a byte-for-byte copy of the engine's two comment
#: regexes, kept as a copy so this module never reached into the engine's
#: private `_strip_comments_for_analysis`. Those regexes ran before strings
#: were known (planning v0.84 §2.2), and the stripper is now the PUBLIC
#: `gauss_pre_execution_validation.strip_comments(...)`, so the reason for a
#: copy is gone: this delegates, and can never drift from the engine.
def strip_comments_for_analysis(code: str) -> str:
    return validation_mod.strip_comments(code)


# ---------------------------------------------------------------------------
# Corpus loading
# ---------------------------------------------------------------------------


def load_jsonl(path: Path) -> list[dict]:
    items: list[dict] = []
    if not path.exists():
        return items
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if line:
                items.append(json.loads(line))
    return items


def load_full_corpus(corpus_dir: Path = _CORPUS_DIR) -> list[dict]:
    """Loads all four corpus family files (Phase 4-6, plus the Phase 15
    fresh-stress-batch file) that exist under `corpus_dir` -- a missing file
    (e.g. `model_output_fresh.jsonl` before the live stress batch has been
    run) is silently treated as zero items for that family, never an error."""
    items: list[dict] = []
    for filename in ("docs_valid.jsonl", "mutations.jsonl", "model_output_historical.jsonl", "model_output_fresh.jsonl"):
        items.extend(load_jsonl(corpus_dir / filename))
    return items


# ---------------------------------------------------------------------------
# Real-GAUSS outcome classification (Phase 3)
# ---------------------------------------------------------------------------


class RealGaussOutcome(str, enum.Enum):
    ACCEPTED = "accepted"
    REJECTED_SYNTAX_OR_PARSE = "rejected_syntax_or_parse"
    RUNTIME_ERROR = "runtime_error"
    TIMEOUT = "timeout"
    INFRASTRUCTURE_FAILURE = "infrastructure_failure"


#: A real GAUSS error-code marker, e.g. "error G0063" -- same shape
#: `gauss_code_execution._GAUSS_ERROR_CODE_RE` already detects presence of;
#: this pattern additionally CAPTURES the code so it can be looked up in
#: `gauss_error_catalog`.
_ERROR_CODE_CAPTURE_RE = re.compile(r"\berror\s+(g\d{4})\b", re.IGNORECASE)

#: Catalogued categories that represent a real GAUSS failure but NOT syntax
#: evidence (Phase 3: "Do not incorrectly treat every GAUSS error as syntax
#: rejection" -- e.g. a dimension mismatch or an undefined symbol is a
#: runtime-computation-phase failure, not a parse-phase one).
_NON_SYNTAX_CATEGORIES = frozenset({
    catalog.GaussErrorCategory.RUNTIME_COMPUTATION,
    catalog.GaussErrorCategory.MATRIX_DIMENSION,
    catalog.GaussErrorCategory.NUMERICAL,
    catalog.GaussErrorCategory.FILE_IO,
    catalog.GaussErrorCategory.PACKAGE_OR_LIBRARY,
    catalog.GaussErrorCategory.INDEXING_SUBSCRIPT,
    catalog.GaussErrorCategory.ARGUMENT_VALIDATION,
    catalog.GaussErrorCategory.TYPE_MISMATCH,
})


@dataclass(frozen=True)
class GaussOutcomeClassification:
    outcome: str
    matched_error_codes: tuple[str, ...]
    #: Categorical evidence-basis label -- "catalogued:<CODE>:<CATEGORY>",
    #: "execution_status:<status>", or "uncatalogued[:<CODE>|:no_error_code_
    #: detected]". NEVER a numeric confidence score (this repository's own
    #: deterministic-state discipline) -- `classify_agreement(...)` reads
    #: only whether this string starts with "uncatalogued" to decide whether
    #: the evidence is usable at all.
    classification_basis: str


def classify_gauss_outcome(raw_result: dict[str, Any]) -> GaussOutcomeClassification:
    """Pure function -- reads only the already-captured `raw_result` dict
    (the same shape `AdapterOutcome.raw_result` carries), performs no I/O,
    calls no model, launches no process. Fully unit-testable with a
    hand-built dict; every test in `test_gauss_differential_harness.py`'s
    "Differential classifier" section uses fabricated dicts, never real
    GAUSS."""
    execution_status = raw_result.get("execution_status")
    stdout = raw_result.get("stdout") or ""
    stderr = raw_result.get("stderr") or ""
    errors = raw_result.get("errors") or []
    combined_text = "\n".join([stdout, stderr, *(str(e) for e in errors)])
    matched_codes = tuple(sorted({
        catalog.normalize_error_code(m) for m in _ERROR_CODE_CAPTURE_RE.findall(combined_text)
    }))

    if execution_status == "timed_out":
        return GaussOutcomeClassification(RealGaussOutcome.TIMEOUT.value, matched_codes, "execution_status:timed_out")

    if execution_status in ("blocked", "skipped", "error", None):
        return GaussOutcomeClassification(
            RealGaussOutcome.INFRASTRUCTURE_FAILURE.value, matched_codes, f"execution_status:{execution_status!r}",
        )

    if execution_status == "completed":
        return GaussOutcomeClassification(RealGaussOutcome.ACCEPTED.value, matched_codes, "execution_status:completed")

    if execution_status == "failed":
        for code in matched_codes:
            entry = catalog.lookup_error(code)
            if entry is not None and entry.category == catalog.GaussErrorCategory.PARSE_SYNTAX:
                return GaussOutcomeClassification(
                    RealGaussOutcome.REJECTED_SYNTAX_OR_PARSE.value, matched_codes, f"catalogued:{code}:PARSE_SYNTAX",
                )
        for code in matched_codes:
            entry = catalog.lookup_error(code)
            if entry is not None and entry.category in _NON_SYNTAX_CATEGORIES:
                return GaussOutcomeClassification(
                    RealGaussOutcome.RUNTIME_ERROR.value, matched_codes, f"catalogued:{code}:{entry.category.value}",
                )
        if matched_codes:
            return GaussOutcomeClassification(
                RealGaussOutcome.RUNTIME_ERROR.value, matched_codes, f"uncatalogued:{matched_codes[0]}",
            )
        return GaussOutcomeClassification(RealGaussOutcome.RUNTIME_ERROR.value, (), "uncatalogued:no_error_code_detected")

    return GaussOutcomeClassification(
        RealGaussOutcome.INFRASTRUCTURE_FAILURE.value, matched_codes, f"execution_status:{execution_status!r}_unrecognized",
    )


# ---------------------------------------------------------------------------
# Agreement classification (Phase 2)
# ---------------------------------------------------------------------------


class AgreementClass(str, enum.Enum):
    AGREE_ACCEPT = "agree_accept"
    AGREE_REJECT = "agree_reject"
    FALSE_POSITIVE = "false_positive"
    FALSE_NEGATIVE = "false_negative"
    INCONCLUSIVE = "inconclusive"


def classify_agreement(validator_status: str, gauss: GaussOutcomeClassification) -> str:
    """Pure function. `validator_status` is one of `gauss_pre_execution_
    validation.SyntaxStatus`'s four values -- `PARTIAL`/`UNKNOWN` NEVER
    collapse into `VALIDATED`/`INVALID` here (Phase 2's explicit
    requirement): only a clean `VALIDATED`/`INVALID` verdict, paired with
    USABLE real-GAUSS evidence, can ever produce `AGREE_ACCEPT`/
    `AGREE_REJECT`/`FALSE_POSITIVE`/`FALSE_NEGATIVE`. Everything else is
    `INCONCLUSIVE` -- including `TIMEOUT`/`INFRASTRUCTURE_FAILURE` (no real
    verdict was actually obtained) and any "uncatalogued" evidence basis
    (fail closed rather than guess)."""
    if gauss.classification_basis.startswith("uncatalogued"):
        return AgreementClass.INCONCLUSIVE.value
    if gauss.outcome in (RealGaussOutcome.TIMEOUT.value, RealGaussOutcome.INFRASTRUCTURE_FAILURE.value):
        return AgreementClass.INCONCLUSIVE.value
    if validator_status not in (validation_mod.SyntaxStatus.VALIDATED.value, validation_mod.SyntaxStatus.INVALID.value):
        return AgreementClass.INCONCLUSIVE.value

    validator_accepts = validator_status == validation_mod.SyntaxStatus.VALIDATED.value
    gauss_accepts = gauss.outcome in (RealGaussOutcome.ACCEPTED.value, RealGaussOutcome.RUNTIME_ERROR.value)
    gauss_rejects_syntax = gauss.outcome == RealGaussOutcome.REJECTED_SYNTAX_OR_PARSE.value

    if validator_accepts and gauss_accepts:
        return AgreementClass.AGREE_ACCEPT.value
    if not validator_accepts and gauss_rejects_syntax:
        return AgreementClass.AGREE_REJECT.value
    if not validator_accepts and gauss_accepts:
        return AgreementClass.FALSE_POSITIVE.value
    if validator_accepts and gauss_rejects_syntax:
        return AgreementClass.FALSE_NEGATIVE.value
    return AgreementClass.INCONCLUSIVE.value  # unreachable given the four combinations above, kept for safety


# ---------------------------------------------------------------------------
# Differential result / runner (Phase 7)
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class DifferentialResult:
    id: str
    origin: str
    snippet: str
    validator_status: str
    validator_issues: tuple[str, ...]
    gauss_outcome: str
    gauss_error_code: str | None
    agreement_class: str
    stdout: str | None
    stderr: str | None
    notes: str


GaussRunner = Callable[[str, str], dict[str, Any]]
"""A callable `(request_identity, code) -> raw_result_dict`, the same shape
`AdapterOutcome.raw_result` carries. `RealGaussRunner` below is the only
production implementation; every test uses a fake."""


def run_corpus_item(item: dict, *, gauss_runner: GaussRunner) -> DifferentialResult:
    # v0.84.0: the RAW snippet, exactly as the engine now passes each block
    # -- `validate_syntax(...)` lexes it itself, and its comment rules need
    # the comments still present.
    syntax_result = validation_mod.validate_syntax(item["snippet"])
    raw_result = gauss_runner(item["id"], item["snippet"])
    gauss_classification = classify_gauss_outcome(raw_result)
    agreement = classify_agreement(syntax_result.status, gauss_classification)
    return DifferentialResult(
        id=item["id"],
        origin=item["origin"],
        snippet=item["snippet"],
        validator_status=syntax_result.status,
        validator_issues=tuple(issue.message for issue in syntax_result.issues),
        gauss_outcome=gauss_classification.outcome,
        gauss_error_code=gauss_classification.matched_error_codes[0] if gauss_classification.matched_error_codes else None,
        agreement_class=agreement,
        stdout=raw_result.get("stdout"),
        stderr=raw_result.get("stderr"),
        notes=gauss_classification.classification_basis,
    )


def run_corpus(items: list[dict], *, gauss_runner: GaussRunner) -> tuple[DifferentialResult, ...]:
    return tuple(run_corpus_item(item, gauss_runner=gauss_runner) for item in items)


# ---------------------------------------------------------------------------
# Real GAUSS runner (production only -- constructed only inside main()'s
# double-gated path)
# ---------------------------------------------------------------------------


class RealGaussRunner:
    """Thin wrapper around `gauss_execution_adapter.GaussExecutionAdapter` +
    `load_real_helper()` -- the SAME production path `test_gauss_execution_
    adapter_real.py` already uses. Never spawns a subprocess itself."""

    def __init__(self, *, executable_path: str, timeout_seconds: float = 30.0) -> None:
        import gauss_execution_adapter as ga  # local import: only reached inside the double-gated path

        self._ga = ga
        self._adapter = ga.GaussExecutionAdapter(helper=ga.load_real_helper())
        self._executable_path = executable_path
        self._timeout_seconds = timeout_seconds

    def __call__(self, request_identity: str, code: str) -> dict[str, Any]:
        with tempfile.TemporaryDirectory(prefix="gauss_ai_differential_") as tmp_dir:
            request = self._ga.AdapterRequest(
                request_identity=request_identity,
                code=code,
                script_path=None,
                working_directory=tmp_dir,
                output_directory=None,
                executable_path=self._executable_path,
                gauss_version=None,
                timeout_seconds=self._timeout_seconds,
                allow_output_files=False,
            )
            outcome = self._adapter.invoke(request)
            if not outcome.invoked:
                category = outcome.failure_category.value if outcome.failure_category else "unknown"
                return {
                    "execution_status": "blocked",
                    "executed": False,
                    "stdout": None,
                    "stderr": None,
                    "errors": [f"adapter rejected before invocation: {category} -- {outcome.rejection_reason}"],
                }
            return outcome.raw_result or {"execution_status": "error", "executed": False, "errors": ["no raw_result"]}


# ---------------------------------------------------------------------------
# Aggregate reporting (Phase 8/20)
# ---------------------------------------------------------------------------


def summarize(results: tuple[DifferentialResult, ...]) -> dict[str, Any]:
    def _counts(subset: tuple[DifferentialResult, ...]) -> dict[str, Any]:
        agreement_counts: dict[str, int] = {}
        validator_status_counts: dict[str, int] = {}
        gauss_outcome_counts: dict[str, int] = {}
        for r in subset:
            agreement_counts[r.agreement_class] = agreement_counts.get(r.agreement_class, 0) + 1
            validator_status_counts[r.validator_status] = validator_status_counts.get(r.validator_status, 0) + 1
            gauss_outcome_counts[r.gauss_outcome] = gauss_outcome_counts.get(r.gauss_outcome, 0) + 1
        return {
            "total": len(subset),
            "agreement_class_counts": agreement_counts,
            "validator_status_counts": validator_status_counts,
            "gauss_outcome_counts": gauss_outcome_counts,
            "false_negatives": [r.id for r in subset if r.agreement_class == AgreementClass.FALSE_NEGATIVE.value],
            "false_positives": [r.id for r in subset if r.agreement_class == AgreementClass.FALSE_POSITIVE.value],
        }

    origins = sorted({r.origin for r in results})
    return {
        "combined": _counts(results),
        "by_origin": {origin: _counts(tuple(r for r in results if r.origin == origin)) for origin in origins},
    }


def render_markdown_summary(summary: dict[str, Any], *, label: str) -> str:
    lines = [f"# Differential Syntax Validation Summary -- {label}", ""]
    for scope_name, scope in (("Combined", summary["combined"]), *((f"Origin: {k}", v) for k, v in summary["by_origin"].items())):
        lines.append(f"## {scope_name}")
        lines.append(f"- total: {scope['total']}")
        lines.append(f"- agreement classes: {scope['agreement_class_counts']}")
        lines.append(f"- validator status: {scope['validator_status_counts']}")
        lines.append(f"- real GAUSS outcome: {scope['gauss_outcome_counts']}")
        if scope["false_negatives"]:
            lines.append(f"- **FALSE NEGATIVES ({len(scope['false_negatives'])})**: {scope['false_negatives']}")
        if scope["false_positives"]:
            lines.append(f"- **FALSE POSITIVES ({len(scope['false_positives'])})**: {scope['false_positives']}")
        lines.append("")
    return "\n".join(lines)


def write_run_artifacts(results: tuple[DifferentialResult, ...], *, label: str) -> Path:
    date_str = _datetime.date.today().isoformat()
    out_dir = _RESULTS_DIR / f"{date_str}-{label}"
    out_dir.mkdir(parents=True, exist_ok=True)
    with (out_dir / "results.jsonl").open("w", encoding="utf-8", newline="\n") as handle:
        for r in results:
            handle.write(json.dumps({
                "id": r.id, "origin": r.origin, "snippet": r.snippet,
                "validator_status": r.validator_status, "validator_issues": list(r.validator_issues),
                "gauss_outcome": r.gauss_outcome, "gauss_error_code": r.gauss_error_code,
                "agreement_class": r.agreement_class, "stdout": r.stdout, "stderr": r.stderr, "notes": r.notes,
            }, ensure_ascii=False))
            handle.write("\n")
    summary = summarize(results)
    (out_dir / "summary.md").write_text(render_markdown_summary(summary, label=label), encoding="utf-8", newline="\n")
    (out_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8", newline="\n")
    return out_dir


# ---------------------------------------------------------------------------
# main() -- doubly-gated real-GAUSS CLI entry point
# ---------------------------------------------------------------------------

ENV_VAR_NAME = "GAUSS_AI_ALLOW_REAL_EXECUTION"
FLAG_NAME = "--run-real-gauss"
_VERIFIED_PLATFORM = "Windows"
_SUPPORTED_EXECUTABLE_BASENAMES = frozenset({"tgauss", "tgauss.exe"})


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-real-gauss", action="store_true", dest="run_real_gauss")
    parser.add_argument("--executable-path", default=None)
    parser.add_argument("--label", default="run")
    parser.add_argument("--timeout-seconds", type=float, default=30.0)
    parser.add_argument("--corpus-dir", default=str(_CORPUS_DIR))
    args = parser.parse_args(argv if argv is not None else sys.argv[1:])

    flag_present = args.run_real_gauss
    env_present = os.environ.get(ENV_VAR_NAME) == "1"
    if not (flag_present and env_present):
        print(f"SKIPPED: both {FLAG_NAME} and {ENV_VAR_NAME}=1 are required simultaneously. No GAUSS was touched.")
        return 0

    if platform.system() != _VERIFIED_PLATFORM:
        print(f"PREFLIGHT FAILED: this harness only proceeds on {_VERIFIED_PLATFORM}.")
        return 0
    if not args.executable_path or Path(args.executable_path).name.lower() not in _SUPPORTED_EXECUTABLE_BASENAMES:
        print("PREFLIGHT FAILED: --executable-path must be an existing terminal tgauss/tgauss.exe path.")
        return 0
    if not Path(args.executable_path).exists():
        print(f"PREFLIGHT FAILED: executable path does not exist: {args.executable_path}")
        return 0

    items = load_full_corpus(Path(args.corpus_dir))
    if not items:
        print(f"No corpus items found under {args.corpus_dir}.")
        return 1

    print("=" * 72)
    print(f"REAL GAUSS EXECUTION IS ENABLED. Running {len(items)} corpus item(s).")
    print("=" * 72)

    runner = RealGaussRunner(executable_path=args.executable_path, timeout_seconds=args.timeout_seconds)
    results = run_corpus(items, gauss_runner=runner)
    out_dir = write_run_artifacts(results, label=args.label)
    print(f"Results written to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
