# Clinical Evidence Intelligence Platform — Build Plan

## Purpose

Build a domain-specific healthcare AI workload that demonstrates:

- multimodal/document intelligence
- structured clinical extraction
- longitudinal data modeling
- evidence-grounded RAG
- model orchestration
- safety controls
- evaluation
- provenance/auditability
- production-oriented backend engineering

This project should later run as a **reference workload on Nuvorix**.

**Important:** use synthetic/publicly usable data. Do not claim diagnosis, clinical validation, regulatory compliance, or real patient care.

---

# 1. Product Goal

```text
Clinical Document
 ↓
Parsing / OCR
 ↓
Structured Clinical Extraction
 ↓
Patient Timeline
 ↓
Evidence Retrieval
 ↓
AI Analysis
 ↓
Safety / Rule Validation
 ↓
Evidence-Cited Summary
 ↓
Audit Trail
```

---

# 2. Document Ingestion

Support at least:

- PDF
- text
- images where practical

Pipeline:

```text
Upload
 ↓
Validation
 ↓
Parsing / OCR
 ↓
Page segmentation
 ↓
Clinical extraction
```

Preserve source provenance.

---

# 3. Structured Clinical Schema

Example:

```json
{
  "patient": {"id": "demo-001"},
  "observations": [],
  "medications": [],
  "conditions": [],
  "lab_results": [],
  "dates": []
}
```

Every extracted value should retain:

- source document
- page
- text span where feasible
- model/version
- confidence

---

# 4. Longitudinal Timeline

Represent repeated observations over time.

Example:

```text
2024-01-10  CBC
2024-05-18  CBC
2024-09-22  Biochemistry
2025-01-04  Follow-up
```

Support comparisons:

- rising
- falling
- stable
- new
- missing

The objective is to demonstrate longitudinal reasoning, not diagnosis.

---

# 5. Evidence RAG

Build a trusted reference knowledge base:

```text
Guideline / Reference
 ↓
Chunk
 ↓
Embedding
 ↓
Vector DB
 ↓
Retrieval
 ↓
Evidence Context
```

Every AI-generated finding that relies on retrieved evidence should expose:

```text
Claim
Source document
Page
Relevant excerpt/chunk
```

---

# 6. Model Abstraction

Use provider/model abstraction instead of hardcoded model-specific code.

Support categories such as:

- text LLM
- multimodal model
- embedding model

Track model/version metadata for every analysis.

---

# 7. Safety Architecture

Use:

```text
Model Output
 ↓
Schema Validation
 ↓
Rule Checks
 ↓
Evidence Check
 ↓
Unsafe / Uncertain?
 ├── Yes → Human Review
 └── No  → Structured Result
```

The model must not:

- prescribe medication
- claim diagnosis
- make irreversible clinical decisions
- invent citations

---

# 8. Evaluation

Create synthetic labeled cases.

Measure:

- field-level precision/recall
- extraction exact match
- citation correctness
- groundedness
- hallucination rate
- trend-detection accuracy
- unsafe-output rate

Separate deterministic regression tests from real-model evaluation.

Publish only measured results.

---

# 9. Backend

Recommended stack:

- Python
- FastAPI
- PostgreSQL
- pgvector
- Redis
- SQLAlchemy
- Pydantic
- `uv`

Suggested APIs:

```text
POST /documents
GET /documents/{id}

POST /patients
GET /patients/{id}

POST /patients/{id}/analyze
GET /patients/{id}/timeline

POST /knowledge-bases
POST /knowledge-bases/{id}/query

GET /analyses/{id}
GET /audit/events
```

---

# 10. UI

Pages:

- dashboard
- document viewer
- patient timeline
- evidence explorer
- analysis result
- audit trail

Most important visual:

```text
Clinical Finding
      ↓
Evidence
      ↓
Source Document + Page
      ↓
Model / Provenance
```

---

# 11. MLOps

Track:

- model version
- prompt version
- embedding model
- dataset version
- evaluation version
- execution id

Later integrate with Nuvorix so Clinical Evidence Intelligence becomes a reference AI workload.

---

# 12. Deployment

Start locally with Docker Compose.

Later support Kubernetes.

Expected components:

```text
FastAPI
Worker
PostgreSQL
pgvector
Redis
Model gateway
```

---

# 13. Definition of Done

- [x] document upload works
- [x] structured extraction works
- [x] provenance is stored
- [x] timeline works
- [x] RAG works
- [x] evidence citations work
- [x] safety checks work
- [x] evaluation suite works
- [x] audit trail works
- [x] Docker Compose works
- [x] README clearly states limitations
- [x] no clinical claims are made
