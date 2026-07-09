# QAKey Operational Playbook

## Start here

This guide describes the day-to-day maintainer workflow for QAKey.
It focuses on ownership, review, publishing, and rollback practices.

---

## Ownership model

- **Author** — drafts or updates the record
- **Reviewer** — approves the record for use
- **Approver / maintainer** — publishes validated changes

Keep contributor and reviewer fields current so the record history stays understandable.

---

## Record lifecycle

QAKey uses three statuses:

- **Draft** — work in progress, not meant for live answers
- **Active** — included in matching and returned to users
- **Inactive** — retained for audit/history, but not used for answers

Recommended flow:

1. Create or edit the record in Draft
2. Review the canonical question and approved answer
3. Mark the record Active when ready
4. Use Inactive when the guidance should no longer answer users

---

## Publish checklist

Before publishing:

- Confirm canonical questions are clear
- Confirm answers are approved and current
- Check reviewer assignments for Draft records
- Review the Publishing Stage panel for created, updated, sunset, deleted, and imported items
- Review the Answer feedback alerts inbox for unresolved user feedback
- Verify the staged list matches the intended change set

After publishing:

- Confirm the index rebuild completed successfully
- Spot-check a few common questions
- Verify the live answer text is correct

---

## Synonym maintenance

Keep `knowledge/synonyms.yaml` aligned with how users actually ask questions.

- Prefer stemmed canonical keys
- Add abbreviations and internal jargon
- Rebuild the index after synonym changes
- Review synonyms whenever matching quality drops

---

## Change log and rollback

- Use the editor publish workflow as the operational change log
- Sunset old guidance instead of deleting it when history matters
- Keep deleted records out of live answers only after confirming the replacement content is ready
- Undo unpublished staged changes before publishing if you need to back out a mistake
- Mark resolved feedback alerts addressed after the content change has been made

---

## Practical cadence

- Review Draft records regularly
- Publish small batches instead of large, risky changes
- Revisit synonyms after content updates
- Keep maintainers and reviewers aligned on ownership
