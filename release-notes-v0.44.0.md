# v0.44.0 - Safe Workspace File Reading Workflow

## Added

- Explicit workspace-bound reads for supported text files
- Path, type, size, and binary-content validation
- Structured file-read evidence
- Provenance and checksum reporting
- Workflow and agent guidance

## Safety

- No arbitrary filesystem access
- No automatic output-file reading
- No binary-file interpretation
- Metadata remains distinct from content
- File contents do not prove methodology validity

## Testing

```
$ python scripts/test_gauss_workspace_file_reader.py
25 test function(s) run, 0 check failure(s).
ALL CHECKS PASSED.

$ python scripts/test_workspace_file_read_integration.py
6 test function(s) run, 0 check failure(s).
ALL CHECKS PASSED.
```

31/31 new tests passing. Zero regressions across `scripts/test_gauss_workspace.py` (24/24), `scripts/test_workspace_execution_integration.py` (18/18), `scripts/test_gauss_execution_session.py` (26/26), `scripts/test_gauss_execution_workflow.py` (60/60), and `scripts/test_gauss_runtime_orchestration.py` (95/95).

`python scripts/check_evaluation_tracking.py --json` → 0 errors, `overall_pass: true`. `python scripts/check_release_readiness.py --json` → `default_pass: true`, `overall_pass: true`.

## Limitations

- Allowlisted text formats only
- Size and encoding limits apply
- No PDFs, images, spreadsheets, archives, or executables
- No uploads or persistent artifact storage
