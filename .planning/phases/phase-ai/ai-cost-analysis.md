# AI Cost Analysis - School Description + Grok’s Take

**Last updated:** 5 March 2026  
**Author:** Grok (team collaboration)  
**Status:** Ready for implementation — Phase AI

## Overview

This document quantifies the expected cost of generating the two AI layers (see AI-2 and AI-3):

1. **School Description** — neutral, facts-only summary (Locrating-style)  
2. **Grok’s Take** — analytical performance commentary using only the metrics (premium layer)

Both outputs are produced together in **one structured JSON response** via the xAI Batch API.

## Current Pricing (March 2026)

- **Model**: `grok-4.1-fast-reasoning` via xAI Batch API  
- **Input**: $0.10 per million tokens  
- **Output**: $0.25 per million tokens  
- Batch discount applied automatically

## Cost per School Generation

**Average token usage** (based on our Gold-layer metrics JSON):  
- Input tokens: ~1,200  
- Output tokens: ~380  
- **Total cost per generation (both outputs)**: **$0.000215** (0.0215 cents)

**One-time full generation** for all ~25,000 schools: **~$5.40**

## Annual Cost Projections

| Scenario                              | Avg regenerations per school/year | Total annual cost |
|---------------------------------------|-----------------------------------|-------------------|
| Optimistic (strict `data_hash` triggers) | 2.5                              | **$13 – $18**    |
| **Realistic (recommended target)**    | 4                                 | **$21 – $30**    |
| Conservative (no optimisations)       | 8                                 | **$43 – $55**    |

**Expected steady-state annual cost**: **$20 – $35**

## Token Usage Assumptions
- Input: Full school metrics JSON + structured prompt template  
- Output: Clean JSON object containing both fields  
- Prompt caching (future) can cut input cost by 60–75%

## Why the Cost Stays So Low
- School Description: regenerates only after major data refreshes  
- Grok’s Take: regenerates **only** when `data_hash` changes (DfE once/year + rare Ofsted)

## Cost-Reduction Roadmap
1. Immediate: Implement `data_hash` change detection + Batch API  
2. Short-term: Enable xAI prompt caching + admin cost dashboard  
3. Medium-term: Cache near-identical takes  
4. Long-term: Explore cheaper models

## Recommendations
- Proceed immediately with the Batch API implementation (see AI-6)  
- Store `generated_at`, `model_version`, `input_tokens`, `data_hash` for auditability

## References
- `.planning/phases/phase-ai/AI-2-school-overview-summary.md`  
- `.planning/phases/phase-ai/AI-3-groks-take-premium-analysis.md`  
- `.planning/phased-delivery.md`  
- xAI API pricing (March 2026)

---
Approved for implementation once reviewed.