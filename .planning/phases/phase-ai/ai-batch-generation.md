# AI Batch Generation - School Description + Grok’s Take

**Last updated:** 5 March 2026  
**Author:** Grok (team collaboration)  
**Status:** Ready for implementation — Phase AI  
**Implementation Owner:** Claude/Codex/Cursor (full spec provided)

## Purpose
This document is the **complete technical specification** for generating both:
- School Description (neutral, facts-only summary)
- Grok’s Take (analytical performance commentary using only metrics)

All generation happens via the **official xAI Batch API** using model `grok-4.1-fast-reasoning`.  
One structured prompt produces both outputs in a single JSON response.

## Functional Requirements
1. Generate both outputs in **one API call per school**.
2. Trigger School Description after **any** major data refresh.
3. Trigger Grok’s Take **only** when the underlying metrics change (via `data_hash`).
4. Store results in a new or extended table with full audit trail.
5. Support batching of hundreds/thousands of schools in a single job.
6. Handle failures gracefully with retry and logging.
7. Be fully idempotent (re-running on same data_hash does nothing).

## Non-Functional Requirements
- Cost target: ≤ $0.000215 per school (see ai-cost-analysis.md).
- Latency: Batch of 300 schools completes in < 15 minutes.
- Rate-limit safe (Batch API has no per-minute limits).
- Zero manual intervention after data ingest.
- Full observability (logs, metrics, cost tracking).

## xAI Batch API Integration Details

**Base URL:** `https://api.x.ai/v1`  
**Authentication:** Bearer token from `XAI_API_KEY` environment variable.  
**Model:** `grok-4.1-fast-reasoning` (fast-reasoning variant).  
**Endpoint for batch:** `POST /v1/batches`

### Exact Prompt Structure (must be followed exactly)
System message:  
"You are Grok. Be concise, neutral, facts-only, parent-friendly. Never hallucinate or add opinions outside the provided metrics."

User message template:  
"Using ONLY this school data:  
{metrics_json}  

Return a valid JSON object with exactly these two fields:  
- school_description: neutral parent-friendly summary (max 120 words)  
- groks_take: Grok's analytical take on performance, trends and metrics only (max 150 words)"

Response format: `{"type": "json_object"}`

### Batch Input Format (JSONL)
Each line in the uploaded file must be:
```json
{
  "custom_id": "urn-123456",
  "method": "POST",
  "url": "/v1/chat/completions",
  "body": { ...full prompt object above... }
}
