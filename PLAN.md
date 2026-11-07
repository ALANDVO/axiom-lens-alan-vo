# Product development plan

Each round completes one feature or repair. Future items are planned, not implemented claims.

## Current round

binary-analysis-basic

## Roadmap

### core-skeleton — Core FastAPI/React skeleton with auth and database

Status: done

Acceptance:
- FastAPI app runs with SQLite persistence
- React + Vite frontend builds and serves
- OIDC Keycloak authentication with demo mode
- Docker Compose with backend, frontend, Keycloak, and volumes
- Health checks and basic API endpoints work

Implementation: `backend/app/main.py`, `backend/app/api/`, `backend/app/core/`, `backend/app/models/`, `backend/app/services/`, `backend/requirements.txt`, `frontend/package.json`, `frontend/src/`, `compose.yaml`, `backend/Dockerfile`, `frontend/Dockerfile`

Tests: `backend/tests/test_main.py`, `backend/tests/test_auth.py`, `frontend/src/test/`

### binary-analysis-basic — Basic binary file analysis (metadata, strings, ELF/PE/Mach-O info)

Status: done

Acceptance:
- Upload binary file for analysis via POST /api/v1/analyses/upload
- Automatic background analysis with status tracking (pending -> running -> completed/failed)
- Extract file info (size, type, hash), strings, and format-specific metadata (ELF header, sections, symbols)
- Trigger analysis on existing records via POST /api/v1/analyses/{id}/analyze
- Results stored in analysis.result JSON field and viewable via GET /api/v1/analyses/{id}
- Export results as JSON from frontend

Implementation: `backend/app/services/binary_analyzer.py`, `backend/app/api/routes/analyses.py`, `backend/requirements.txt`

Tests: `backend/tests/test_analyses.py`

### binary-analysis-workflow — Binary analysis workflow with AI insights

Status: planned

Acceptance:
- Upload binary file for analysis
- View pseudocode, strings, symbols, calls
- AI-assisted explanation of functions (opt-in, labeled advisory)
- Export analysis results

### javascript-analysis-workflow — JavaScript/Electron application analysis workflow

Status: planned

Acceptance:
- Analyze JavaScript/Electron app directory or ASAR
- View modules, imports, Electron boundaries
- Trace IPC and native addon relationships
- Export analysis results

### process-comparison-workflow — Process behavior comparison workflow

Status: planned

Acceptance:
- Capture process terminal output and filesystem observations
- Compare two process runs for differences
- Explain content, exit outcome, and temporal differences
- Export comparison results

