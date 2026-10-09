# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 2.0.x   | :white_check_mark: |
| < 2.0.0 | :x:                |

---

## Security Principles in BetterLife

1. **Zero External Data Egress for Health Records**:
   All inference occurs on private or self-hosted model runners. No medical lab data or patient identifiers are forwarded to third-party commercial LLM endpoints.

2. **Deterministic Safety Guardrails**:
   All clinical insights and extractions are passed through a rule-based safety validation layer (`SafetyService`). Medical claims, prescriptions, and unverified diagnostic statements are blocked at the application layer.

3. **Defensive Input & Output Sanitization**:
   - File uploads (PDF/Images) are checked for size, MIME type, and sanitized before disk operations.
   - User inputs and LLM streams are sanitized via HTML sanitizers (`rehype-sanitize`) on the frontend to prevent Cross-Site Scripting (XSS).
   - SQL queries are executed exclusively through parameterized SQLAlchemy ORM models with Alembic schema versioning.

4. **Secrets Management**:
   - No credentials, private tokens, or secrets are tracked in version control.
   - Environment variables are validated at application boot using `pydantic-settings` on the backend and Zod on the frontend.

---

## Reporting a Vulnerability

If you discover a potential security vulnerability within BetterLife:
1. Please **do not** file a public GitHub issue.
2. Email the maintainer directly at `vinit.karkera@gmail.com` with:
   - A description of the vulnerability
   - Steps to reproduce or proof-of-concept
   - Potential impact
3. You will receive an acknowledgment within 48 hours, followed by updates on remediation.
