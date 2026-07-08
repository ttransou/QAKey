# Test Fixtures

## XLSX import workflow fixture

Place your 20 Q/A workbook at:

- `tests/fixtures/import_20_qa_pairs.xlsx`

The workflow test in `tests/test_import_preview_workflow.py` uses this file against:

- `POST /api/records/import-preview`

### Minimum required columns

Use one header row with at least:

- `canonical_question` (or `question`)
- `answer`

### Optional columns

- `status` (`Draft`, `Active`, `Inactive`)
- `alternate_phrasings` (multi-value supported)
- `tags` (multi-value supported)
- `contributor`
- `reviewer`

Multi-value fields can be separated by newlines, `|`, or `;`.

### Expected test outcome

When the workbook has 20 valid Q/A rows:

- importer returns `count == 20`
- importer returns no row-level errors
- each preview record has non-empty question and answer
