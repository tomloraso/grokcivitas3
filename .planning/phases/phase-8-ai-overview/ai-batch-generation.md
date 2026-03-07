# AI Batch Generation - School Overview + Grok’s Take

**Last updated:** 6 March 2026
**Author:** Grok (team collaboration)
**Status:** Ready for implementation — Phase AI
**Implementation Owner:** Claude/Codex/Cursor (full spec provided)

## Purpose
This document is the **complete technical specification** for generating both:
- School Overview (neutral, facts-only "About the school" paragraph — free tier)
- Grok’s Take (analytical performance commentary using only metrics — premium-tier feature)

All generation happens via the **official xAI Batch API** using model `grok-4-1-fast-reasoning`.
Each output is generated via its own dedicated prompt and API call.

## Functional Requirements
1. Generate School Overview and Grok’s Take in **separate API calls per school**.
2. Trigger School Overview after **any** major data refresh.
3. Trigger Grok’s Take **only** when the underlying metrics change (via `data_hash`).
4. Store results in a new or extended table with full audit trail.
5. Support batching of hundreds/thousands of schools in a single job.
6. Handle failures gracefully with retry and logging.
7. Be fully idempotent (re-running on same data_hash does nothing).

## Non-Functional Requirements
- Cost target: ≤ $0.000215 per school (see ai-cost-analysis.md).
- Completion expectation: xAI Batch API is asynchronous; Civitas must tolerate provider completion over an up-to-24-hour window.
- Rate-limit safe (Batch API has no per-minute limits).
- Zero manual intervention after data ingest.
- Full observability (logs, metrics, cost tracking).

## xAI Batch API Integration Details

**Base URL:** `https://api.x.ai/v1`
**Authentication:** Bearer token from `XAI_API_KEY` environment variable.
**Model:** `grok-4-1-fast-reasoning` (fast-reasoning variant).
**Endpoint for batch:** `POST /v1/batches`

---

### Execution Semantics

- xAI batch jobs are asynchronous and should be treated as provider jobs, not request/response calls.
- The Civitas integration must split work into submit and poll/finalize steps.
- `pipeline run --all` may submit batches, but completion and persistence should happen in a later poll pass.
- The xAI console wording around completion "in 24 hrs" should be treated as the batch completion window, not as a guarantee of minute-scale processing or a per-minute rate limit.

### Prompt 1 — School Overview (free "About the school" layer)

```json
{
  "model": "grok-4-1-fast-reasoning",
  "messages": [
    {
      "role": "system",
      "content": "You write neutral, factual ‘About the school’ overviews for Civitas parents.\n\nRules:\n- Write 140-180 words in a single flowing paragraph.\n- Use only the facts supplied in the user message.\n- Include: school type, religious character (if any), age range, pupil numbers & capacity, location/postcode context, headteacher/leadership if published, admissions policy if published, Ofsted rating + date, and key demographics (FSM, EAL, SEN) if available.\n- Write in calm, welcoming, plain UK English.\n- Do NOT analyse performance, trends, strengths, weaknesses, or compare to other schools.\n- Do NOT speculate, recommend, or say anything about suitability.\n- If data is ‘Not published’, simply omit it gracefully — never say ‘not published’.\n- Output a single paragraph only."
    },
    {
      "role": "user",
      "content": "School context:\n- URN: 100000\n- Name: The Aldgate School\n- Phase: Primary\n- Type: Voluntary aided school\n- Status: Open\n- Postcode: EC3A 5DE\n- Headteacher / leader: Not published\n- Head job title: Not published\n- Age range: Not published\n- Gender intake: Not published\n- Religious character: Not published\n- Admissions policy: Not published\n- Sixth form: Not published\n- Trust / MAT: Not published\n- Local authority: Not published\n- Settlement context: Not published\n- Capacity: 245\n- Pupil count: 249\n- Boys on roll: Not published\n- Girls on roll: Not published\n- FSM percentage: 23.3%\n- EAL percentage: 60.2%\n- SEN percentage: 18.1%\n- EHCP percentage: 4.8%\n- Progress 8: Not published\n- Attainment 8: Not published\n- KS2 reading expected: 93.0%\n- KS2 maths expected: 93.0%\n- Ofsted overall effectiveness: Outstanding\n- Latest inspection date: 2024-06-12\n- IMD decile: Not published\n\nWrite a natural, factual ‘About the school’ paragraph that gives parents a clear picture of what the school is like."
    }
  ],
  "temperature": 0.1
}
```

---

### Prompt 2 — Grok’s Take (premium-tier feature)

```json
{
  "model": "grok-4-1-fast-reasoning",
  "messages": [
    {
      "role": "system",
      "content": "You are Grok. Give parents a clear, truthful, analytical take on a school’s performance using ONLY the metrics provided.\n\nRules:\n- Write 140-200 words in a single paragraph plus 2-3 short bullet highlights.\n- Focus exclusively on what the numbers and trends actually show.\n- Highlight strengths, areas to watch, and any notable patterns (e.g. FSM vs national, progress over time, Ofsted context).\n- Use a curious, straightforward, no-fluff tone.\n- Never speculate or give advice.\n- Never repeat basic facts already in the School Overview.\n- Output exactly one paragraph + short bullets."
    },
    {
      "role": "user",
      "content": "School metrics only (do not use any other information):\n- URN: 100000\n- Name: The Aldgate School\n- FSM percentage: 23.3%\n- EAL percentage: 60.2%\n- SEN percentage: 18.1%\n- EHCP percentage: 4.8%\n- KS2 reading expected: 93.0%\n- KS2 maths expected: 93.0%\n- Ofsted overall effectiveness: Outstanding\n- Latest inspection date: 2024-06-12\n- Pupil count: 249\n- Capacity: 245\n\nGive Grok’s honest take on how this school is performing based purely on the data."
    }
  ],
  "temperature": 0.2
}
```

---

### Batch Input Format (JSONL)
Each line in the uploaded file must be:
```json
{
  "custom_id": "urn-123456",
  "method": "POST",
  "url": "/v1/chat/completions",
  "body": { ...full prompt object above... }
}
