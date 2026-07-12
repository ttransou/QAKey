# Future Enhancements

- Add a functional scaffold for feedback alerts to be delivered to the editor’s email as a periodic digest.

## Maintainer Alert System

### Concept

When QAKey receives unresolved feedback, no-match queries, low-confidence matches, or repeated ambiguous matches, it can notify the configured maintainer by email.

The alert should not be sent for every single event to avoid noise. Instead, QAKey should collect review items and send a digest.

Example digest summary:

- QAKey has 7 items that may need review:
  - 3 unanswered questions
  - 2 low-confidence matches
  - 1 ambiguous match pattern
  - 1 user feedback comment

### Initial Alert Trigger Event Types

- `no_match`
- `low_confidence`
- `ambiguous_match`
- `negative_feedback`
- `stale_review`

Each event type maps to a maintainer task:

| Event | Meaning | Maintainer action |
|---|---|---|
| `no_match` | QAKey could not find an approved answer | Add a new Q&A pair or synonym |
| `low_confidence` | QAKey answered, but barely passed threshold | Add alternate phrasing or improve canonical question |
| `ambiguous_match` | Multiple records were too close | Clarify records or add “do not match” guidance later |
| `negative_feedback` | User marked answer unhelpful | Review answer wording or matching |
| `stale_review` | Record is past review date | Confirm answer is still current |
