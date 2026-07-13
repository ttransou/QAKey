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

## Teams App and Adapter Framework

QAKey may eventually support adapter-based deployment so the same approved Q&A knowledge base can be exposed through multiple user interfaces, including Microsoft Teams, Slack, web widgets, intranet portals, and other chat or support surfaces.

The core QAKey engine should remain channel-agnostic. Matching, fallback behavior, approved answer delivery, confidence scoring, and source-of-truth management should live in the QAKey framework itself. Adapters should only translate between a specific platform and QAKey’s query API.

For example, a Microsoft Teams adapter could allow users to ask questions within Teams while QAKey continues to resolve them against Active approved records. The Teams app would send the user’s question to QAKey, receive either a matched approved answer or a deterministic fallback response, and display that response in the Teams conversation.

A Teams implementation could support:

* one-to-one chat with the QAKey bot;
* channel-based use for shared team questions;
* adaptive-card responses for matched answers, fallback messages, and suggestions;
* links back to source documents, policies, or the QAKey editor where appropriate;
* role-aware access if connected to organizational authentication;
* feedback buttons such as “Helpful,” “Not helpful,” or “Needs review.”

Other adapters could follow the same pattern. Slack, website widgets, intranet search boxes, and internal assistant tools should all call the same QAKey API rather than creating separate logic for each channel.

The intended architecture is:

```text
User interface or platform adapter
        ↓
QAKey REST API
        ↓
QAKey matching engine
        ↓
Approved Q&A records
        ↓
Matched answer or deterministic fallback
```

This preserves QAKey’s central contract: the delivery channel may change, but the answer behavior remains controlled, deterministic, and governed by the approved source of truth.

Adapters should be treated as extensions rather than requirements. A small organization may need only the local web UI, while a larger organization may choose to expose QAKey through Teams, Slack, an internal portal, or multiple channels simultaneously. Adapters should change where QAKey appears, not how QAKey answers.


```mermaid
flowchart LR
    Teams["Microsoft Teams adapter"] --> API["QAKey REST API"]
    Slack["Slack adapter"] --> API
    Widget["Website widget"] --> API
    Portal["Internal portal"] --> API

    API --> Engine["QAKey matching engine"]
    Engine --> Records["Approved Q&A records"]
    Engine --> Fallback["Deterministic fallback"]

    Records --> Response["Approved answer"]
    Fallback --> Response
    Response --> API

    classDef neutral fill:#ffffff,stroke:#111827,color:#111827,stroke-width:2px;
    class Teams,Slack,Widget,Portal,API,Engine,Records,Fallback,Response neutral;
```

---

## “Needs human help” routing

Fallback should not always end at “try again.”

Future enhancement:

If no match, show contact route:
- Email support
- Submit ticket
- Ask the office
- Contact records manager

This could be configured by category or deployment.

Possible fallback routing examples:

I could not find an approved answer for that question.

You can:
- Try rephrasing your question
- Contact support@example.org
- Submit a support request
- Ask the records manager

This could be configured globally at first:
```yaml
fallback:
  no_match_message: >
    I could not find an approved answer for that question.

  human_help:
    enabled: true
    label: "Contact the team"
    type: "email"
    value: "support@example.org"
```
Later, routing could be category-specific:
```yaml
fallback_routes:
  default:
    label: "Contact the team"
    email: "info@example.org"

  it-support:
    label: "Submit an IT support request"
    url: "https://example.org/support"

  archives:
    label: "Contact the archives team"
    email: "archives@example.org"
```
This belongs early because it makes fallback behavior more humane and more useful.

---

## Feedback buttons on answers

Simple end-user feedback:

Was this helpful?
[Yes] [No] [Needs update]

If “No”:

What went wrong?
- Did not answer my question
- Answer seems outdated
- Instructions unclear
- Other

For the first version, do not overbuild it. Record the feedback event with:

- timestamp
- query
- matched_record_id
- canonical_question
- confidence
- feedback_type
- optional_comment

A local JSONL event log is enough:
```json
{"timestamp":"2026-07-08T15:40:00Z","type":"feedback","feedback":"needs_update","record_id":"qa-1234abcd","query":"how do i reset my login","confidence":0.71}
```
This supports your later review queue and email alerts.

---

## Usage analytics without surveillance

Very important: analytics should help maintainers improve content without over-collecting user data.

Useful metrics:

- Most asked questions
- Most common fallbacks
- Low-confidence query patterns
- Records with negative feedback
- Questions with no alternate phrasings

Avoid making this creepy or user-tracking-heavy. Avoid early collection of:

- user identity
- IP address
- session trails
- individual behavioral profiles

A good principle:
QAKey analytics should measure knowledge gaps, not surveil users.

---

## Static widget embed

For small organizations, a simple website widget could be huge:

```html
<script src="qakey-widget.js"></script>
```

Or self-hosted:
```html
<script src="/static/js/qakey-widget.js"></script>
<div id="qakey-widget" data-api="/api/query"></div>
```

Then they can embed QAKey into a website without a complex app integration.

The widget should call the same API as the main UI:

Widget → /api/query → QAEngine → approved answer or fallback

Important principle:

The widget changes the surface, not the answer behavior.

This pairs well with Teams/Slack adapters later.

---

## Demo content packs

Starter datasets for common use cases:

Small nonprofit
Historical society
School club
Internal IT support
HR FAQ
Volunteer organization
Community archive

Suggested structure:
demo-packs/

├── historical-society/

├── small-nonprofit/

├── internal-it-support/

├── volunteer-organization/

├── school-club/

└── community-archive/

Each pack could include:

- qa_records.yaml
- synonyms.yaml
- README.md
- sample_questions.md



    
