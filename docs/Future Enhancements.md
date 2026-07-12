# Future Enhancements

- Add a functional scaffold for feedback alerts to be delivered to the editor’s email as a periodic digest.

## Maintainer Alert System

### Concept

QAKey may eventually support email alerts or digest notifications when review-worthy events accumulate. These events could include unmatched questions, low-confidence matches, ambiguous matches, user feedback, and stale records needing review.

The purpose is to support maintainers who do not check the editor every day. Rather than silently collecting unresolved feedback, QAKey can notify the configured maintainer that content may need review. Alerts should be digest-based by default to avoid noise and should direct maintainers back to the review queue in the editor.

This supports QAKey’s accessibility principle: keeping approved answers current should not depend on a maintainer remembering to manually inspect the system.

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

---

