## 1. Delivery Documentation

- [x] 1.1 Create root `README.md` with project overview, stack, directory map, prerequisites, database initialization, backend startup, frontend startup, demo profile, verification commands, and troubleshooting
- [x] 1.2 Create root `DESIGN.md` documenting the Vite MPA frontend, Spring Boot layered backend, authentication model, database model, security posture, testing strategy, and major trade-offs
- [x] 1.3 Add or update API documentation with endpoint path, method, auth requirement, request body, response shape, and common errors for auth, sections, posts, growth, users, and admin APIs
- [x] 1.4 Add a delivery boundary note that distinguishes source files, generated files, runtime logs, planning artifacts, and course-report documents

## 2. Repository Hygiene

- [x] 2.1 Update `.gitignore` to cover root and nested runtime logs, crash logs, local temp files, frontend build output, frontend dependencies, backend build output, and IDE metadata
- [x] 2.2 Inventory current delivery-noise files and classify them as source, docs, generated output, runtime artifact, or user/planning content before any cleanup
- [x] 2.3 Remove or quarantine only safe generated/runtime artifacts while preserving unrelated user work and OpenSpec/planning artifacts
- [x] 2.4 Add a repeatable hygiene check or documented checklist that identifies remaining generated artifacts and delivery-noise candidates

## 3. Frontend Runtime Maintainability

- [x] 3.1 Define the frontend module map and public entrypoint so existing HTML pages still load one Vite entry while implementation moves into focused modules
- [x] 3.2 Extract routes, page titles, page detection, history sync, and navigation highlighting into a routing/bootstrap module
- [x] 3.3 Extract API client, `ApiResponse` unwrapping, JWT header injection, error normalization, and shared request helpers into an API module
- [x] 3.4 Extract token storage, user persistence, session restore, login guard, role guard, logout, and draft persistence into a session module
- [x] 3.5 Extract safe DOM helpers, HTML escaping, toast rendering, state cards, formatting helpers, and global action helpers into shared UI modules
- [x] 3.6 Move page-specific renderers and action binders into page modules while preserving `data-page` and `data-slot` contracts
- [x] 3.7 Run frontend build and existing page-shell verification after modularization to confirm page bootstrapping remains stable

## 4. Rendering Security

- [x] 4.1 Audit every `innerHTML`, `outerHTML`, and template-string rendering site in the frontend runtime and classify each dynamic interpolation as trusted, escaped, or unsafe
- [x] 4.2 Replace unsafe dynamic rendering with DOM construction, `textContent`, safe attribute assignment, or audited escaping helpers
- [x] 4.3 Add frontend malicious-content fixtures for post title, post content, comment content, username, report reason, reward description, and recommendation preview data
- [x] 4.4 Add XSS regression tests that verify malicious fixture strings render as inert text and do not create executable scripts, handlers, or unsafe links
- [x] 4.5 Document the frontend rendering policy in `DESIGN.md` or API/security documentation so reviewers can see how backend data is handled

## 5. Backend Safety And API Evidence

- [x] 5.1 Audit repository queries for native SQL, string concatenation, and unsafe dynamic query construction
- [x] 5.2 Add or extend backend tests demonstrating that hostile search input is handled as query data and does not alter repository semantics
- [x] 5.3 Verify DTO validation coverage for login, registration, posting, comments, reports, recommendation config, profile update, and admin operations
- [x] 5.4 Verify authorization tests for admin-only and moderator/admin governance endpoints, including denial for insufficient roles
- [x] 5.5 Document why current JPQL parameter binding mitigates the SQL injection finding and note any replaced unsafe query patterns if discovered

## 6. Quality Verification

- [x] 6.1 Add or extend frontend tests for API runtime behavior, session restoration, protected-action guards, page initialization, and safe rendering
- [x] 6.2 Add or update a verification matrix covering guest browsing, regular user actions, moderator governance, and admin operations
- [x] 6.3 Run `npm run build` and the frontend test commands, then record results in the verification notes
- [x] 6.4 Run targeted backend tests or full backend test suite, then record results in the verification notes
- [x] 6.5 Complete the live-data smoke test for `connect-frontend-real-api-data` if MySQL credentials are available, or document the exact blocker and required environment variables
- [x] 6.6 Re-run OpenSpec status for both this change and `connect-frontend-real-api-data` to confirm implementation readiness and any remaining blocked task

## 7. Final Review Readiness

- [x] 7.1 Review the project against the original strict scoring categories and document how each category reaches the intended 10/10 standard or what external blocker remains
- [x] 7.2 Run a final repository hygiene check and ensure root documentation points to the correct files and commands
- [x] 7.3 Produce a concise final quality summary for course submission, including security, testing, documentation, architecture, and known environment assumptions
