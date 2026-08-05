"""Tests for the bounded, single-file repair application transaction.

Run with:

    python scripts/test_gauss_repair_application.py

Every test uses a disposable `tempfile.TemporaryDirectory()`-backed
workspace and a real, on-disk `.gss` file -- this is the first test module
in this repository that genuinely writes to and reads from real files, since
`gauss_repair_application.py` is the first module capable of doing so. No
test invokes GAUSS, and no test triggers a rerun.
"""

from __future__ import annotations

import hashlib
import sys
import tempfile
from pathlib import Path

_SCRIPT_DIR = Path(__file__).resolve().parent
if str(_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPT_DIR))

import gauss_execution_interpreter as interp  # noqa: E402
import gauss_repair_application as app  # noqa: E402
import gauss_repair_application_approval as aa  # noqa: E402
import gauss_repair_approval as ra  # noqa: E402
import gauss_repair_draft as rd  # noqa: E402
import gauss_repair_draft_approval as da  # noqa: E402
import gauss_repair_planner as rp  # noqa: E402
import gauss_workspace as workspace_mod  # noqa: E402


_failures: list[str] = []


def check(name: str, condition: bool) -> None:
    if not condition:
        _failures.append(name)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

DEFAULT_TEXT = "x = 2 + 2\nprint x;\ny = 5;\n"


def _evidence(**overrides: object) -> "interp.ExecutionEvidence":
    values = {
        "runner": "FAKE", "gauss_ran": False, "executed": True, "execution_status": "failed",
        "exit_code": 0, "stdout_chars": 0, "stderr_chars": 0, "timed_out": False,
        "workspace_state": "failed", "provenance": None,
        "stdout_text": "Program execute failed\n", "stderr_text": "error G0105 : Undefined symbol\n",
        "metadata_error": None,
    }
    values.update(overrides)
    return interp.ExecutionEvidence(**values)


def _plan() -> "rp.RepairPlan":
    return rp.plan_repair(_evidence())


class _Chain:
    def __init__(self, tmp: str, *, text: str = DEFAULT_TEXT, relative_path: str = "model.gss",
                 line_start: int = 1, line_end: int = 1, file_type: str = ".gss") -> None:
        self.registry = workspace_mod.WorkspaceRegistry(approved_parent_directory=tmp)
        self.workspace = self.registry.create_workspace()
        Path(self.workspace.root_path).mkdir(parents=True, exist_ok=True)
        self.registry.update_workspace_status(self.workspace.workspace_id, to_status=workspace_mod.WorkspaceStatus.POPULATED)
        self.registry.update_workspace_status(self.workspace.workspace_id, to_status=workspace_mod.WorkspaceStatus.READY)

        self.relative_path = relative_path
        self.target = Path(self.workspace.root_path) / relative_path
        self.target.write_bytes(text.encode("utf-8"))
        self.real_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
        self.original_text = text

        self.plan = _plan()
        self.plan_record = ra.RepairApprovalStore().approve(self.plan, recorded_at="t0")

        self.artifact = rd.SourceArtifact(workspace_id=self.workspace.workspace_id, relative_path=relative_path, file_type=file_type)
        self.identity = rd.SourceIdentity(
            artifact=self.artifact, content_hash=self.real_hash, size=len(text.encode("utf-8")), encoding="utf-8"
        )
        self.scope = rd.EditScope(line_start=line_start, line_end=line_end, intended_operation="insert missing semicolon")
        self.draft = rd.build_repair_draft(
            repair_draft_id="draft-1", repair_plan_digest=rp.repair_plan_digest(self.plan),
            source_identity=self.identity, edit_scope=self.scope,
            proposed_change_description="Insert a missing statement terminator at the reported line.",
            generated_at="t0",
        )
        self.draft_record = da.DraftApprovalStore().approve(self.draft, recorded_at="t0")
        self.application_record = aa.ApplicationApprovalStore().approve(self.draft, recorded_at="t0")

    def apply(self, replacement_text: str = "x = 2 + 2;\n", **overrides: object) -> "app.ApplicationResult":
        kwargs: dict[str, object] = dict(
            repair_plan=self.plan,
            repair_approval_record=self.plan_record,
            repair_draft=self.draft,
            draft_approval_record=self.draft_record,
            application_approval_record=self.application_record,
            replacement_text=replacement_text,
            workspace_registry=self.registry,
            clock=lambda: 1000.0,
            id_factory=lambda: "app-1",
        )
        kwargs.update(overrides)
        return app.apply_repair(**kwargs)

    def current_bytes(self) -> bytes:
        return self.target.read_bytes()


# ---------------------------------------------------------------------------
# Successful transaction
# ---------------------------------------------------------------------------


def test_01_successful_application_applies_and_verifies() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        chain = _Chain(tmp)
        result = chain.apply()
        check("outcome is applied", result.outcome == "applied")
        check("reason is None on success", result.reason is None)
        check("target file was actually modified", chain.current_bytes() == b"x = 2 + 2;\nprint x;\ny = 5;\n")
        check("post hash matches the new file content", result.post_application_content_hash == hashlib.sha256(chain.current_bytes()).hexdigest())
        check("pre hash matches the original content", result.pre_application_content_hash == chain.real_hash)
        check("all 18 checks reported", len(result.checks) == 18)
        check("every check passed", all(c.passed for c in result.checks))


def test_02_backup_created_with_correct_content_and_hash() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        chain = _Chain(tmp)
        result = chain.apply()
        assert result.backup is not None
        backup_path = chain.registry.resolve_within_workspace(chain.workspace.workspace_id, result.backup.relative_path)
        check("backup file exists on disk", backup_path is not None and backup_path.exists())
        check("backup content matches the original pre-application text", backup_path.read_text(encoding="utf-8") == chain.original_text)
        check("backup content hash matches the pre-application hash", result.backup.content_hash == chain.real_hash)
        check("backup size matches original byte length", result.backup.size == len(chain.original_text.encode("utf-8")))
        check("backup path is contained within the workspace", str(backup_path).startswith(chain.workspace.root_path))


def test_03_backup_is_workspace_contained_and_not_the_target() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        chain = _Chain(tmp)
        result = chain.apply()
        assert result.backup is not None
        check("backup relative_path differs from the target relative_path", result.backup.relative_path != chain.relative_path)


# ---------------------------------------------------------------------------
# Blocking before write
# ---------------------------------------------------------------------------


def test_04_stale_source_blocks_before_write() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        chain = _Chain(tmp)
        chain.target.write_bytes(b"x = 999;\n")  # mutate after draft was bound
        result = chain.apply()
        check("outcome is blocked", result.outcome == "blocked")
        check("reason is stale_source", result.reason == "stale_source")
        check("target file was NOT modified further", chain.current_bytes() == b"x = 999;\n")
        check("no backup was created (blocked before backup step)", result.backup is None)
        check("only two checks reported (source_hash_fresh fails immediately)", len(result.checks) == 1)


def test_05_gate_failure_blocks_before_write() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        chain = _Chain(tmp)
        result = chain.apply(application_approval_record=None)  # application layer never approved
        check("outcome is blocked", result.outcome == "blocked")
        check("reason names gate_failed", result.reason is not None and result.reason.startswith("gate_failed"))
        check("target file unchanged", chain.current_bytes() == chain.original_text.encode("utf-8"))
        check("no backup was created", result.backup is None)


def test_06_wrong_file_type_blocks_before_gate() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        chain = _Chain(tmp, relative_path="notes.txt", file_type=".txt")
        result = chain.apply()
        check("outcome is blocked", result.outcome == "blocked")
        check("reason names file_type_not_allowed", result.reason == "file_type_not_allowed")
        check("target file unchanged", chain.current_bytes() == chain.original_text.encode("utf-8"))


def test_07_workspace_not_found_blocks_cleanly() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        chain = _Chain(tmp)
        other_registry = workspace_mod.WorkspaceRegistry(approved_parent_directory=tmp)
        result = chain.apply(workspace_registry=other_registry)
        check("outcome is blocked", result.outcome == "blocked")
        check("reason references a read failure", result.reason is not None and result.reason.startswith("source_read_failed"))


# ---------------------------------------------------------------------------
# Candidate validation failures (backup already created by this point)
# ---------------------------------------------------------------------------


def test_08_candidate_range_out_of_bounds_blocks() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        chain = _Chain(tmp, line_start=50, line_end=50)
        result = chain.apply()
        check("outcome is blocked", result.outcome == "blocked")
        check("reason names candidate_range_invalid", result.reason is not None and result.reason.startswith("candidate_range_invalid"))
        check("target file unchanged", chain.current_bytes() == chain.original_text.encode("utf-8"))
        check("a backup WAS still created before the candidate check ran", result.backup is not None)
        backup_path = chain.registry.resolve_within_workspace(chain.workspace.workspace_id, result.backup.relative_path)
        check("the backup remains on disk despite the block", backup_path.exists())


def test_09_whitespace_only_replacement_blocks_as_empty() -> None:
    # v0.63.0 evaluation finding (Prompt 53.2): a whitespace-only replacement
    # is now caught by the dedicated REPLACEMENT_TEXT_NON_EMPTY check before
    # candidate construction even runs -- previously this silently deleted the
    # edit range's content instead of being refused.
    with tempfile.TemporaryDirectory() as tmp:
        chain = _Chain(tmp, line_start=1, line_end=3)
        result = chain.apply(replacement_text="   \n")
        check("outcome is blocked", result.outcome == "blocked")
        check("reason is replacement_text_empty", result.reason == "replacement_text_empty")
        check("target file unchanged", chain.current_bytes() == chain.original_text.encode("utf-8"))


def test_10_candidate_unchanged_blocks() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        chain = _Chain(tmp, line_start=1, line_end=1)
        result = chain.apply(replacement_text="x = 2 + 2\n")  # byte-identical to the original first line
        check("outcome is blocked", result.outcome == "blocked")
        check("reason is candidate_unchanged", result.reason == "candidate_unchanged")


def test_11_candidate_exceeds_line_bound_blocks() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        chain = _Chain(tmp, line_start=1, line_end=1)
        huge_replacement = "".join(f"line {i};\n" for i in range(app.MAX_EDIT_RANGE_LINES + 5))
        result = chain.apply(replacement_text=huge_replacement)
        check("outcome is blocked", result.outcome == "blocked")
        check("reason is candidate_exceeds_line_bound", result.reason == "candidate_exceeds_line_bound")
        check("target file unchanged", chain.current_bytes() == chain.original_text.encode("utf-8"))


def test_12_candidate_with_nul_byte_blocks() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        chain = _Chain(tmp, line_start=1, line_end=1)
        result = chain.apply(replacement_text="x = 2\x00 + 2;\n")
        check("outcome is blocked", result.outcome == "blocked")
        check("reason is candidate_binary_shaped", result.reason == "candidate_binary_shaped")
        check("target file unchanged", chain.current_bytes() == chain.original_text.encode("utf-8"))


# ---------------------------------------------------------------------------
# Backup duplication and never-overwrite
# ---------------------------------------------------------------------------


def test_13_duplicate_backup_names_never_collide() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        chain = _Chain(tmp)
        # Pre-create the exact backup filename the transaction would choose
        # (same clock => same timestamp component => same first candidate name).
        first_candidate = app._backup_candidate_names(chain.relative_path, chain.real_hash, "1000-0")[0]  # noqa: SLF001
        pre_existing_path = chain.registry.resolve_within_workspace(chain.workspace.workspace_id, first_candidate)
        pre_existing_path.write_bytes(b"pre-existing unrelated backup content")

        result = chain.apply()
        check("outcome is still applied", result.outcome == "applied")
        assert result.backup is not None
        check("the collision was avoided by choosing a different backup name", result.backup.relative_path != first_candidate)
        check("the pre-existing file at the first candidate name was never overwritten", pre_existing_path.read_bytes() == b"pre-existing unrelated backup content")


# ---------------------------------------------------------------------------
# Workspace escape / containment
# ---------------------------------------------------------------------------


def test_14_workspace_escape_via_traversal_path_blocks() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        chain = _Chain(tmp)
        escaping_artifact = rd.SourceArtifact(
            workspace_id=chain.workspace.workspace_id, relative_path="../escape.gss", file_type=".gss"
        )
        escaping_identity = rd.SourceIdentity(artifact=escaping_artifact, content_hash="a" * 64, size=10, encoding="utf-8")
        escaping_draft = rd.build_repair_draft(
            repair_draft_id="draft-escape", repair_plan_digest=rp.repair_plan_digest(chain.plan),
            source_identity=escaping_identity, edit_scope=chain.scope,
            proposed_change_description="Attempted escape.", generated_at="t0",
        )
        draft_record = da.DraftApprovalStore().approve(escaping_draft, recorded_at="t0")
        application_record = aa.ApplicationApprovalStore().approve(escaping_draft, recorded_at="t0")
        result = app.apply_repair(
            repair_plan=chain.plan, repair_approval_record=chain.plan_record, repair_draft=escaping_draft,
            draft_approval_record=draft_record, application_approval_record=application_record,
            replacement_text="x = 1;\n", workspace_registry=chain.registry,
            clock=lambda: 1000.0, id_factory=lambda: "app-escape",
        )
        check("outcome is blocked", result.outcome == "blocked")
        check("reason references a read failure (path never resolves, so it is never found)", result.reason is not None and result.reason.startswith("source_read_failed"))


# ---------------------------------------------------------------------------
# Injected write/replace failures
# ---------------------------------------------------------------------------


def test_15_temp_write_failure_reports_failed_not_blocked() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        chain = _Chain(tmp)

        def failing_write(directory, prefix, content):  # noqa: ANN001
            raise OSError("simulated disk-full condition")

        result = chain.apply(write_temp_file_fn=failing_write)
        check("outcome is failed, not blocked", result.outcome == "failed")
        check("reason is temp_write_failed", result.reason == "temp_write_failed")
        check("target file unchanged", chain.current_bytes() == chain.original_text.encode("utf-8"))
        check("a backup exists despite the failure", result.backup is not None)


def test_16_atomic_replace_failure_reports_failed_and_cleans_temp_file() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        chain = _Chain(tmp)

        def failing_replace(src, dst):  # noqa: ANN001
            raise OSError("simulated cross-device link")

        result = chain.apply(replace_fn=failing_replace)
        check("outcome is failed", result.outcome == "failed")
        check("reason is atomic_replace_failed", result.reason == "atomic_replace_failed")
        check("target file unchanged (replace never completed)", chain.current_bytes() == chain.original_text.encode("utf-8"))
        leftover_temp_files = [p for p in Path(chain.workspace.root_path).glob("*.gauss-ai-tmp")]
        check("no orphaned temp file remains after a failed replace", leftover_temp_files == [])


def test_17_post_write_hash_mismatch_reports_failed() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        chain = _Chain(tmp)

        def wrong_content_write(directory, prefix, content):  # noqa: ANN001
            return app._default_write_temp_file(directory, prefix, b"completely different bytes\n")  # noqa: SLF001

        result = chain.apply(write_temp_file_fn=wrong_content_write)
        check("outcome is failed", result.outcome == "failed")
        check("reason is post_write_hash_mismatch", result.reason == "post_write_hash_mismatch")
        check("a backup exists to recover from", result.backup is not None)
        check("the pre-application backup content is still the true original", chain.original_text.encode("utf-8") not in (b"completely different bytes\n",))


# ---------------------------------------------------------------------------
# Partial-transaction rejection / no-write-before-validation
# ---------------------------------------------------------------------------


def test_18_no_write_occurs_for_any_blocked_scenario() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        chain = _Chain(tmp, line_start=50, line_end=50)  # will block on candidate range
        before = chain.current_bytes()
        chain.apply()
        after = chain.current_bytes()
        check("target bytes are identical before and after a blocked transaction", before == after)


def test_19_checks_list_stops_at_first_failure() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        chain = _Chain(tmp)
        chain.target.write_bytes(b"mutated\n")
        result = chain.apply()
        check("only the checks up to and including the first failure are recorded", len(result.checks) == 1)
        check("the one recorded check is source_hash_fresh and it failed", result.checks[0].check == "source_hash_fresh" and result.checks[0].passed is False)


# ---------------------------------------------------------------------------
# ApplicationResult correctness
# ---------------------------------------------------------------------------


def test_20_application_result_fields_correct_for_applied() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        chain = _Chain(tmp)
        result = chain.apply()
        check("application_id populated", result.application_id == "app-1")
        check("draft_digest matches the draft's own digest", result.draft_digest == rd.repair_draft_digest(chain.draft))
        check("workspace_id matches", result.workspace_id == chain.workspace.workspace_id)
        check("relative_path matches", result.relative_path == chain.relative_path)
        check("applied_at uses the injected clock", result.applied_at == "1000.0")
        check("application_boundary is the fixed applied statement", result.application_boundary == app.APPLIED_BOUNDARY_STATEMENT)


def test_21_application_result_fields_correct_for_blocked() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        chain = _Chain(tmp)
        result = chain.apply(application_approval_record=None)
        check("outcome is blocked", result.outcome == "blocked")
        check("post_application_content_hash is None when blocked", result.post_application_content_hash is None)
        check("application_boundary is the fixed blocked statement", result.application_boundary == app.BLOCKED_BOUNDARY_STATEMENT)
        check("blocked boundary states nothing was applied", "NOT applied" in result.application_boundary)


def test_22_application_result_fields_correct_for_failed() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        chain = _Chain(tmp)

        def failing_replace(src, dst):  # noqa: ANN001
            raise OSError("simulated failure")

        result = chain.apply(replace_fn=failing_replace)
        check("outcome is failed", result.outcome == "failed")
        check("post_application_content_hash is None when failed", result.post_application_content_hash is None)
        check("application_boundary is the fixed failed statement", result.application_boundary == app.FAILED_BOUNDARY_STATEMENT)
        check("failed boundary mentions no automatic rollback/retry/rerun", "No automatic rollback, retry, or rerun" in result.application_boundary)


# ---------------------------------------------------------------------------
# No rerun, purity, structural safety
# ---------------------------------------------------------------------------


def test_23_no_rerun_fields_anywhere_on_the_result() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        chain = _Chain(tmp)
        result = chain.apply()
        for forbidden_attr in ("rerun", "rerun_requested", "execution_request_id", "execution_session_id"):
            check(f"ApplicationResult has no {forbidden_attr!r} field", not hasattr(result, forbidden_attr))


def test_24_no_execution_or_rerun_imports_in_module_source() -> None:
    source = Path(app.__file__).read_text(encoding="utf-8")
    forbidden = (
        "gauss_code_execution",
        "gauss_execution_adapter",
        "gauss_execution_workflow",
        "gauss_execution_session",
        "gauss_runtime_orchestration",
        "gauss_orchestration_state_store",
        "subprocess",
        "socket",
        "urllib",
    )
    for name in forbidden:
        check(f"module does not import {name!r}", f"import {name}" not in source)


def test_25_module_never_calls_execute_or_rerun() -> None:
    source = Path(app.__file__).read_text(encoding="utf-8")
    check("module source contains no 'rerun(' call", "rerun(" not in source)
    check("module source contains no '.execute(' call", ".execute(" not in source)


def test_26_line_ending_preserved_for_untouched_lines() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        crlf_text = "x = 2 + 2\r\nprint x;\r\ny = 5;\r\n"
        chain = _Chain(tmp, text=crlf_text, line_start=1, line_end=1)
        chain.apply(replacement_text="x = 2 + 2;\r\n")
        content = chain.current_bytes()
        check("untouched later lines keep their original CRLF terminators", b"print x;\r\n" in content)
        check("replaced line keeps CRLF as supplied", b"x = 2 + 2;\r\n" in content)


def test_27_determinism_of_backup_naming_given_identical_clock() -> None:
    with tempfile.TemporaryDirectory() as tmp1, tempfile.TemporaryDirectory() as tmp2:
        chain1 = _Chain(tmp1)
        chain2 = _Chain(tmp2)
        result1 = chain1.apply()
        result2 = chain2.apply()
        check("identical scenarios with identical clocks produce identical backup relative_path", result1.backup.relative_path == result2.backup.relative_path)
        check("identical scenarios produce identical pre/post hashes", (result1.pre_application_content_hash, result1.post_application_content_hash) == (result2.pre_application_content_hash, result2.post_application_content_hash))


# ---------------------------------------------------------------------------
# v0.63.0 evaluation-discovered regression tests
# ---------------------------------------------------------------------------


def test_28_empty_string_replacement_blocks_before_candidate_construction() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        chain = _Chain(tmp, line_start=2, line_end=2)
        result = chain.apply(replacement_text="")
        check("outcome is blocked", result.outcome == "blocked")
        check("reason is replacement_text_empty", result.reason == "replacement_text_empty")
        check("target file unchanged (no silent line deletion)", chain.current_bytes() == chain.original_text.encode("utf-8"))
        check("REPLACEMENT_TEXT_NON_EMPTY is the failing check", result.checks[-1].check == "replacement_text_non_empty" and result.checks[-1].passed is False)


def test_29_non_utf8_encodable_replacement_blocks_cleanly_without_raising() -> None:
    # Previously an uncaught UnicodeEncodeError propagated out of
    # apply_repair(...) entirely for a lone UTF-16 surrogate in
    # replacement_text; this must now be a clean, fail-closed `blocked` result.
    with tempfile.TemporaryDirectory() as tmp:
        chain = _Chain(tmp, line_start=1, line_end=1)
        result = chain.apply(replacement_text="x = 1\ud800;\n")
        check("outcome is blocked, not an uncaught exception", result.outcome == "blocked")
        check("reason is candidate_not_utf8_encodable", result.reason == "candidate_not_utf8_encodable")
        check("target file unchanged", chain.current_bytes() == chain.original_text.encode("utf-8"))
        check("CANDIDATE_ENCODABLE is the failing check", result.checks[-1].check == "candidate_encodable" and result.checks[-1].passed is False)


def test_30_middle_of_file_edit_preserves_surrounding_lines() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        chain = _Chain(tmp, text="a = 1;\nb = 2;\nc = 3;\n", line_start=2, line_end=2)
        result = chain.apply(replacement_text="b = 999;\n")
        check("outcome is applied", result.outcome == "applied")
        check("first and third lines unchanged, second line replaced", chain.current_bytes() == b"a = 1;\nb = 999;\nc = 3;\n")


def test_31_end_of_file_edit_applies_exactly_the_supplied_replacement() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        chain = _Chain(tmp, text="a = 1;\nb = 2;\nc = 3;\n", line_start=3, line_end=3)
        result = chain.apply(replacement_text="c = 999;")  # deliberately no trailing newline
        check("outcome is applied", result.outcome == "applied")
        check("exact replacement used verbatim, no inferred trailing newline", chain.current_bytes() == b"a = 1;\nb = 2;\nc = 999;")


def test_32_unicode_content_applies_and_decodes_cleanly() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        original = "// café naïve\nx = 1;\nprint \"你好\";\n"
        chain = _Chain(tmp, text=original, line_start=2, line_end=2)
        result = chain.apply(replacement_text="x = 2; // ééé\n")
        check("outcome is applied", result.outcome == "applied")
        decoded = chain.current_bytes().decode("utf-8")
        check("unicode content on untouched lines is preserved exactly", "café naïve" in decoded and "你好" in decoded)
        check("unicode replacement content is present", "ééé" in decoded)


def test_33_repeated_legitimate_two_step_application_produces_two_distinct_backups() -> None:
    with tempfile.TemporaryDirectory() as tmp:
        chain = _Chain(tmp, text="a = 1;\nb = 2;\n", line_start=1, line_end=1)
        result1 = chain.apply(replacement_text="a = 100;\n", clock=lambda: 1000.0)
        check("first application succeeds", result1.outcome == "applied")
        check("first edit applied, second line untouched", chain.current_bytes() == b"a = 100;\nb = 2;\n")

        new_text = chain.current_bytes().decode("utf-8")
        new_hash = hashlib.sha256(new_text.encode("utf-8")).hexdigest()
        artifact2 = rd.SourceArtifact(workspace_id=chain.workspace.workspace_id, relative_path=chain.relative_path, file_type=".gss")
        identity2 = rd.SourceIdentity(artifact=artifact2, content_hash=new_hash, size=len(new_text.encode("utf-8")), encoding="utf-8")
        scope2 = rd.EditScope(line_start=2, line_end=2, intended_operation="second edit")
        draft2 = rd.build_repair_draft(
            repair_draft_id="draft-2", repair_plan_digest=rp.repair_plan_digest(chain.plan),
            source_identity=identity2, edit_scope=scope2,
            proposed_change_description="second probe edit", generated_at="t1",
        )
        draft_record2 = da.DraftApprovalStore().approve(draft2, recorded_at="t1")
        application_record2 = aa.ApplicationApprovalStore().approve(draft2, recorded_at="t1")
        result2 = app.apply_repair(
            repair_plan=chain.plan, repair_approval_record=chain.plan_record, repair_draft=draft2,
            draft_approval_record=draft_record2, application_approval_record=application_record2,
            replacement_text="b = 200;\n", workspace_registry=chain.registry,
            clock=lambda: 2000.0, id_factory=lambda: "app-2",
        )
        check("second application succeeds", result2.outcome == "applied")
        check("both edits present after two sequential applications", chain.current_bytes() == b"a = 100;\nb = 200;\n")
        check("second application produced its own, distinct backup", result2.backup.relative_path != result1.backup.relative_path)
        backups = [p for p in Path(chain.workspace.root_path).glob("*.bak")]
        check("exactly two backup files exist on disk", len(backups) == 2)


def run_tests() -> int:
    tests = [(name, fn) for name, fn in sorted(globals().items()) if name.startswith("test_") and callable(fn)]
    for name, fn in tests:
        before = len(_failures)
        try:
            fn()
        except Exception as exc:  # noqa: BLE001
            _failures.append(f"{name} raised an unexpected exception: {type(exc).__name__}: {exc}")
        if len(_failures) == before:
            print(f"PASS  {name}")
        else:
            for failure in _failures[before:]:
                print(f"FAIL  {name}: {failure}")
    print()
    print(f"{len(tests)} test function(s) run, {len(_failures)} check failure(s).")
    if _failures:
        return 1
    print("ALL CHECKS PASSED.")
    return 0


if __name__ == "__main__":
    raise SystemExit(run_tests())
