## Why

The project is close to a complete campus forum demo, but a strict review still exposes delivery-grade gaps: missing root documentation, noisy runtime artifacts, a large monolithic frontend runtime, incomplete security evidence, weak API documentation, and an unfinished smoke-test trail. This change raises the project from "runs and demos" to "clean, reviewable, secure, and defensible for a 10/10 course submission."

## What Changes

- Add formal root-level project documentation that explains the product, architecture, setup, demo accounts, API surface, verification commands, and delivery scope.
- Document the frontend MPA architecture and campus forum design decisions so the current implementation has a clear rationale.
- Tighten repository hygiene by ignoring runtime logs and generated artifacts, then separating source, docs, OpenSpec artifacts, and local runtime outputs.
- Refactor the large shared frontend runtime into focused modules without changing the existing multi-page user experience.
- Harden frontend rendering against XSS by establishing a single trusted rendering policy and adding tests for malicious backend-provided content.
- Document and verify backend SQL safety, validation, authentication, and role authorization boundaries.
- Add or extend frontend and backend verification so key guest, user, moderator, and admin paths are covered by repeatable tests or smoke checks.
- Add API documentation sufficient for frontend-backend collaboration and course review.
- Finish the outstanding live-data smoke-test evidence from `connect-frontend-real-api-data` where environment access permits, or document the exact external blocker.

## Capabilities

### New Capabilities
- `project-delivery-documentation`: Covers root README, design documentation, architecture explanation, setup guidance, API index, and review-ready delivery notes.
- `repository-hygiene`: Covers ignore rules, generated artifact boundaries, runtime log handling, and clean handoff expectations.
- `frontend-runtime-maintainability`: Covers modularizing the shared frontend runtime, preserving the existing MPA shell, and keeping page behavior stable.
- `frontend-rendering-security`: Covers safe rendering of backend data, XSS prevention rules, and malicious input verification.
- `quality-verification`: Covers test expansion, smoke-test evidence, backend security contract verification, and API documentation completeness.

### Modified Capabilities
- None.

## Impact

- Root project files: `README.md`, `DESIGN.md`, `.gitignore`, and optional review or quality notes.
- Frontend files: `frontend/assets/app.js`, new frontend runtime modules, `frontend/package.json`, `frontend/tests/*`, and page shell integration points.
- Backend files: controller/service/repository validation and security tests, API documentation support, and any minimal annotations or documentation needed to expose API contracts.
- Documentation: `docs/*`, OpenSpec change artifacts, API endpoint inventory, MPA architecture notes, and verification checklist.
- Verification: frontend build/tests, backend tests, security-focused rendering tests, and live-data smoke-test notes tied to demo backend availability.
