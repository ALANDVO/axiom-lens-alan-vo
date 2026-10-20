# Changelog

## 1.1.0 — work-in-progress checkpoint

Partial code published for continued development. Known issues: STATUS.md.

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