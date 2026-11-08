# Changelog

## 1.5.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.4.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

## 1.3.0 — work-in-progress checkpoint

### Added
- Basic binary analysis functionality (`backend/app/services/binary_analyzer.py`)
- Binary file upload with automatic background analysis (`POST /api/v1/analyses/upload`)
- Analysis trigger endpoint for existing records (`POST /api/v1/analyses/{id}/analyze`)
- File info extraction (size, type, SHA256 hash, modification time)
- File type detection via python-magic (MIME type, description)
- Printable strings extraction with configurable limits
- ELF binary analysis via readelf (header, sections, symbols)
- PE binary analysis via pefile/objdump (header, sections, imports, exports)
- Mach-O binary analysis via otool (header, libraries)
- Analysis status progression: pending → running → completed/failed
- Results stored in Analysis.result JSON field
- New dependencies: python-magic, pefile

### Fixed
- All existing tests continue to pass (28 backend, 6 frontend)

### Known Issues
- Binary analyzer requires system tools (readelf, objdump, otool) for full functionality
- Large binaries may take time to analyze; consider timeout handling

## 1.1.1 — Fix analysis filter query parameter

### Fixed
- Correct query parameter name for status filter in analysis list API (was `status_filter`, now `status` to match route alias)
- Fix failing test `test_list_analyses_filters` that used incorrect parameter name


## 1.1.0 — work-in-progress checkpoint
# Axiom Lens - Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-10-20

### Added
- Initial release of Axiom Lens
- FastAPI backend with SQLite persistence
- React + TypeScript + Vite frontend
- OIDC Keycloak authentication with demo mode
- Docker Compose orchestration (backend, frontend, Keycloak)
- Analysis management (create, list, view, update, delete)
- Three analysis workflows: Binary, JavaScript/Electron, Process
- Health checks and version endpoints
- Audit logging
- Responsive professional UI with Tailwind-inspired CSS

### Security
- HttpOnly SameSite cookies for session management
- CSRF protection on state-changing operations
- PKCE for OIDC authorization code flow
- Demo mode restricted to localhost only
- Non-root Docker containers

### Infrastructure
- Multi-stage Docker builds
- Nginx reverse proxy for frontend
- Persistent volumes for database and Keycloak
- Health checks on all services

Wall time: 0.01 seconds

---

Alan Vo · [alanvo.net](https://alanvo.net) · [X: @alanvoasi](https://x.com/alanvoasi)
