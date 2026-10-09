# Contributing to BetterLife

Thank you for your interest in contributing to BetterLife! We welcome contributions that maintain or improve the clinical precision, security, and developer experience of the platform.

---

## 1. Prerequisites

- **Python**: 3.12+ (managed with [`uv`](https://docs.astral.sh/uv/))
- **Node.js**: 20+ with `npm`
- **Make**: Standard GNU make
- **Docker**: (Optional) for running PostgreSQL/pgvector and Redis locally

---

## 2. Getting Started

Clone the repository and install all dependencies using the root `Makefile`:

```bash
git clone https://github.com/vinitkarkera/better-life.git
cd better-life

# Install backend uv virtual environment and frontend npm dependencies
make install
```

---

## 3. Local Development

Run the backend and frontend development servers in separate terminal sessions:

```bash
# Terminal 1: FastAPI Backend (http://localhost:8000)
make dev-backend

# Terminal 2: Vite React Frontend (http://localhost:5173)
make dev-frontend
```

---

## 4. Code Quality & Verification Gates

Before submitting a pull request, ensure all checks pass by running the comprehensive quality gate:

```bash
make check
```

This executes:
1. `make lint`: Backend (Ruff) + Frontend (ESLint)
2. `make format-check`: Backend (Ruff format) + Frontend (Prettier)
3. `make typecheck`: Backend (Mypy strict) + Frontend (TypeScript `tsc --noEmit`)
4. `make test`: Backend (Pytest with coverage) + Frontend (Vitest unit tests)
5. `make build`: Production Vite bundle compilation

---

## 5. Security & Dependency Auditing

Run vulnerability audits regularly:

```bash
make audit
```

- Backend dependencies are audited via `pip-audit`.
- Frontend packages are audited via `npm audit --audit-level=high`.

---

## 6. Commit & Pull Request Guidelines

- Follow [Conventional Commits](https://www.conventionalcommits.org/) (e.g., `feat:`, `fix:`, `refactor:`, `test:`, `docs:`).
- Keep changes focused and self-contained.
- Do not commit secrets, API keys, or `.env` files.
