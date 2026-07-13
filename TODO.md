# Development TODO

Purpose: keep implementation and documentation priorities coherent with the current product state.

## Completed implementation milestones

- [x] Add deterministic ingest module (`qakey/ingest.py`)
- [x] Expose ingest preview API (`POST /api/ingest/preview`)
- [x] Wire editor bulk import flow (optional CSV/XLSX preview path)
- [x] Add ingest-focused tests (`tests/test_ingest.py`)
- [x] Add editor lifecycle workflow test coverage (`tests/test_editor_query_workflow.py`)
- [x] Add spreadsheet preview workflow test coverage (`tests/test_import_preview_workflow.py`)
- [x] Add downloadable CSV/XLSX import templates for maintainers
- [x] Update implementation docs to reflect ingest/editor architecture
- [x] Run focused validation and full regression tests

## Active product backlog

- [ ] Enforce editor auth hardening (session policy, CSRF, rate limits)
- [x] Add publish-stage recent changes audit details (exportable snapshot)

## Documentation roadmap

- [x] Keep README focused as an entry point (purpose, quick start, fit, links out)
- [x] Add `docs/source-of-truth-framework.md` for maintainer operating model
- [x] Add `docs/use-cases.md` for audience-specific scenarios
- [x] Add `docs/operational-playbook.md` for day-to-day maintenance and governance
- [x] Add links to core docs from README "Documentation" section

## Planned content: `docs/use-cases.md`

- [x] Small nonprofit website maintainer workflow
- [x] Internal support desk workflow
- [x] Large organization governance-oriented deployment pattern
- [x] "When QAKey is a good fit" and "when it is not" examples

## Planned content: `docs/operational-playbook.md`

- [x] Content ownership model (author, reviewer, approver)
- [x] Record lifecycle guidance (Draft -> Active -> Inactive)
- [x] Publish checklist (validation, review, publish, verify)
- [x] Synonym maintenance cadence and quality checks
- [x] Change log and rollback practices

## Documentation quality checks

- [x] Ensure every new doc has concrete examples
- [x] Keep terminology consistent with `docs/schema.md`
- [x] Cross-link to existing docs: configuration, deployment, implementation
- [x] Add a short "Start here" section at top of each new doc

## Nice-to-have (later)

- [ ] Add a simple docs index page under `docs/`
- [ ] Add screenshots/GIFs for editor workflows
- [ ] Add a 30-day rollout checklist for new teams

## Future enhancements

- [ ] Add maintainer digest alerts for review-worthy events
- [ ] Add fallback contact routing for questions with no match
- [ ] Add simple feedback buttons on answers
- [ ] Add lightweight usage analytics for knowledge gaps
- [ ] Add a static website widget embed
