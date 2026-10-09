# ADR 0001: Self-Hosted Ollama Inference with Hierarchical Fallback and Deterministic Guardrails

## Status
Accepted

## Date
2026-10-09

## Context
BetterLife processes sensitive health data (laboratory blood tests, patient vitals, metabolic markers). Relying on third-party commercial LLM APIs (OpenAI, Anthropic, Google Gemini) introduces:
1. **Data Sovereignty & Privacy Risks**: Medical reports containing protected health information (PHI) leaving dedicated infrastructure.
2. **Vendor Lock-in & Rate Limits**: Unpredictable cost surges, token limits, and third-party downtime.
3. **Clinical Hallucination Dangers**: Unconstrained models hallucinating medication dosages or issuing diagnostic guarantees.

## Decision
1. **Self-Hosted Ollama Endpoint**: All AI model inference is hosted privately via Ollama (`https://ollama.calmalpha.in/`). No proprietary external AI APIs are invoked in production.
2. **Hierarchical Model Cascade**: The `ModelManager` orchestrates automatic graceful degradation across models:
   - Primary: `gemma4:e4b` (optimized for medical entity extraction and reasoning)
   - Secondary: `phi4-mini:latest` (lightweight conversational fallback)
   - Tertiary: `granite4.1:3b` / `qwen3.5:4b-mlx`
3. **Deterministic Safety Guardrail (`SafetyService`)**: LLM outputs do not flow straight to clinicians or patients. Outputs are inspected by an offline regex/rule-based guardrail that:
   - Blocks any attempt to prescribe medications, drug dosages, or unapproved treatment regimens.
   - Forbids definitive diagnostic declarations (enforcing differential considerations instead).
   - Verifies citation grounding against ingested clinical guideline chunks (ADA, AHA, KDIGO, WHO).
4. **Deterministic Regex Extraction Fallback**: If the model output is malformed or the inference server is temporarily unreachable, the extraction engine falls back immediately to deterministic regular expression parsers to maintain 100% platform availability.

## Consequences
### Positive
- Zero external data egress; PHI is contained entirely on private infrastructure.
- High platform availability even during network disruptions or model crashes.
- Zero API billing or per-token SaaS subscription costs.
- Deterministic safety guarantees enforceable at runtime without prompt-drift vulnerability.

### Trade-offs
- Inference throughput is bounded by self-hosted GPU/CPU cluster capacity.
- Model weights and updates must be managed and monitored internally.
