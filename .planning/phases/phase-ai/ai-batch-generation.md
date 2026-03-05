# AI Batch Generation - School Description + Grok’s Take

**Last updated:** 5 March 2026  
**Author:** Grok (team collaboration)  
**Status:** Ready for implementation — Phase AI

## Overview
This document details the fastest, cheapest way to generate both AI outputs using the **xAI Batch API**.

One prompt → two outputs in a single JSON response.  
Triggered by the existing data ingest pipeline + new `data_hash` logic.

## Trigger Rules
- School Description: after every major refresh (GIAS weekly, Ofsted monthly, DfE annual)  
- Grok’s Take: **only** when `data_hash` changes on `school_demographics_yearly` or new Ofsted inspection

## xAI Batch API Implementation

**Model**: `grok-4.1-fast-reasoning`

### Prompt Template (shared for both outputs)
```json
{
  "model": "grok-4.1-fast-reasoning",
  "messages": [
    {
      "role": "system",
      "content": "You are Grok. Be concise, neutral, facts-only, and parent-friendly. Never hallucinate."
    },
    {
      "role": "user",
      "content": "Using ONLY this school data:\n{{metrics_json}}\n\nReturn a JSON object with exactly these two fields:\n- school_description: neutral 120-word summary\n- groks_take: Grok's analytical take on performance & trends (max 150 words, metrics only)"
    }
  ],
  "response_format": { "type": "json_object" }
}