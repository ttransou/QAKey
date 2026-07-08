# Development TODO

Purpose: keep implementation and documentation priorities coherent with the current product state.

## Completed implementation milestones

- [x] Add deterministic ingest module (`qakey/ingest.py`)
- [x] Expose ingest preview API (`POST /api/ingest/preview`)
- [x] Wire editor bulk import flow (optional CSV/XLSX preview path)
- [x] Add ingest-focused tests (`tests/test_ingest.py`)
- [x] Add editor lifecycle workflow test coverage (`tests/test_editor_query_workflow.py`)
- [x] Add spreadsheet preview workflow test coverage (`tests/test_import_preview_workflow.py`)
- [x] Update implementation docs to reflect ingest/editor architecture
- [x] Run focused validation and full regression tests

## Active product backlog

- [ ] Add CSV/XLSX import template download files for maintainers
- [ ] Enforce editor auth hardening (session policy, CSRF, rate limits)
- [ ] Add publish-stage recent changes audit details (exportable snapshot)

## Documentation roadmap

- [x] Keep README focused as an entry point (purpose, quick start, fit, links out)
- [x] Add `docs/source-of-truth-framework.md` for maintainer operating model
- [ ] Add `docs/use-cases.md` for audience-specific scenarios
- [ ] Add `docs/operational-playbook.md` for day-to-day maintenance and governance
- [x] Add links to core docs from README "Documentation" section

## Planned content: `docs/use-cases.md`

- [ ] Small nonprofit website maintainer workflow
- [ ] Internal support desk workflow
- [ ] Large organization governance-oriented deployment pattern
- [ ] "When QAKey is a good fit" and "when it is not" examples

## Planned content: `docs/operational-playbook.md`

- [ ] Content ownership model (author, reviewer, approver)
- [ ] Record lifecycle guidance (Draft -> Active -> Inactive)
- [ ] Publish checklist (validation, review, publish, verify)
- [ ] Synonym maintenance cadence and quality checks
- [ ] Change log and rollback practices

## Documentation quality checks

- [ ] Ensure every new doc has concrete examples
- [ ] Keep terminology consistent with `docs/schema.md`
- [ ] Cross-link to existing docs: configuration, deployment, implementation
- [ ] Add a short "Start here" section at top of each new doc

## Nice-to-have (later)

- [ ] Add a simple docs index page under `docs/`
- [ ] Add screenshots/GIFs for editor workflows
- [ ] Add a 30-day rollout checklist for new teams
