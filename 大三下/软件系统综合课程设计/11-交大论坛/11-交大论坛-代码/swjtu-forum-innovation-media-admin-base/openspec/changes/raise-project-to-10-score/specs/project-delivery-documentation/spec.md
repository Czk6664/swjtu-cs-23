## ADDED Requirements

### Requirement: Root README documents project operation
The project SHALL provide a root-level `README.md` that explains the forum purpose, technology stack, directory structure, setup prerequisites, backend startup, frontend startup, database initialization, demo profile usage, verification commands, and known local environment requirements.

#### Scenario: Evaluator opens project root
- **WHEN** an evaluator opens the repository root
- **THEN** `README.md` provides enough information to understand and run the system without relying on chat history or private notes

#### Scenario: Backend requires environment variables
- **WHEN** the README describes backend startup
- **THEN** it lists required environment variables including `JWT_SECRET`, database settings, and Redis settings

### Requirement: Design document explains architecture and decisions
The project SHALL provide a root-level `DESIGN.md` that explains the frontend MPA architecture, backend layered architecture, authentication model, database model, security posture, testing strategy, and major trade-offs.

#### Scenario: Architecture criticism is reviewed
- **WHEN** an evaluator questions why the frontend uses a Vite MPA structure
- **THEN** `DESIGN.md` explains the page-shell plus shared-runtime model as an intentional architecture

#### Scenario: Security posture is reviewed
- **WHEN** an evaluator looks for SQL injection, XSS, validation, and authorization evidence
- **THEN** `DESIGN.md` summarizes the concrete safeguards and points to tests or implementation locations

### Requirement: API documentation supports frontend-backend collaboration
The project SHALL document the main external API endpoints with path, method, authentication requirement, request body, response shape, and common error behavior.

#### Scenario: Frontend developer needs endpoint contract
- **WHEN** a developer wants to call login, posts, comments, growth, or admin endpoints
- **THEN** the API documentation provides the route, method, auth requirement, and expected JSON contract

### Requirement: Delivery notes distinguish source from generated output
The project SHALL document which directories and files are source, generated output, local runtime artifacts, planning artifacts, and optional course-report documents.

#### Scenario: Repository contains local artifacts
- **WHEN** generated logs or local runtime files exist in the working tree
- **THEN** the documentation explains that they are not part of the source delivery and identifies their ignore or cleanup policy
