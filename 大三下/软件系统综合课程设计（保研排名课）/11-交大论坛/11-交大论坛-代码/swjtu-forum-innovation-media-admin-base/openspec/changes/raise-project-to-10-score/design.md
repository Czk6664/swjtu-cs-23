## Context

The current project is a Spring Boot + MySQL + Redis backend with a Vite multi-page frontend. The product surface now resembles a real SWJTU campus forum and most live API integration work has already been implemented under `connect-frontend-real-api-data`, with one remaining smoke-test task blocked by local database credentials.

A strict review identified several issues that affect perceived and actual delivery quality: missing root-level README/DESIGN documents, noisy runtime logs in the project root, a 1700+ line shared frontend runtime, insufficient API documentation, incomplete security evidence, and unclear test coverage. Some review claims need correction: `PostRepository` uses JPQL parameter binding rather than string-concatenated SQL, and backend DTO validation plus backend tests already exist. This change should therefore both fix real gaps and document evidence that disproves false positives.

Constraints:

- Preserve the current MPA page shell and SWJTU forum visual direction.
- Avoid replacing the frontend with a new framework during this quality pass.
- Avoid broad backend rewrites unless a security or verification gap requires it.
- Keep changes easy to review for a course project evaluator.
- Do not erase unrelated dirty worktree changes; handle delivery cleanup carefully.

## Goals / Non-Goals

**Goals:**

- Make the repository look and behave like a polished course-design submission from the first opened directory.
- Provide formal documentation for setup, architecture, API surface, security posture, testing, demo data, and known environment requirements.
- Split the frontend runtime into focused modules while preserving current page behavior and build output.
- Establish an explicit frontend rendering safety policy and verify that untrusted backend data cannot execute script.
- Expand repeatable verification so the evaluator can see builds, tests, security checks, and smoke-test evidence.
- Finish or explicitly document the remaining live-data smoke-test blocker from the previous OpenSpec change.

**Non-Goals:**

- Rebuild the frontend as a Vue/React SPA.
- Replace MySQL, Redis, Spring Security, or the current API route model.
- Add a full production CI/CD pipeline unless a lightweight script or documented command is enough for the course scope.
- Implement a full observability stack or production monitoring platform.
- Change user-facing product scope beyond what is required to improve quality, safety, documentation, and verification.

## Decisions

### Decision 1: Keep the MPA architecture and document it

The frontend already uses static HTML page shells plus a shared runtime. That is acceptable for a course project and matches the current landing work. The change SHALL document this as an intentional Vite MPA architecture rather than treating it as an accidental structure.

Alternatives considered:

- Convert to SPA: improves route structure but creates a large migration that does not directly address the strict review.
- Keep undocumented MPA: fastest, but leaves the same architecture criticism in place.

### Decision 2: Modularize the runtime without changing page contracts

The large `frontend/assets/app.js` should be split around stable responsibilities:

- route/page bootstrap
- API client and `ApiResponse` handling
- session and authorization guards
- DOM safety and shared UI helpers
- page renderers and action binders

Existing HTML pages should continue to load a single Vite entry module. The module graph can be internal, but page shell `data-page` and `data-slot` contracts must remain stable.

Alternatives considered:

- Leave one file and add comments: does not address maintainability scoring.
- Introduce a component framework: too much scope for a quality pass.

### Decision 3: Treat backend data as untrusted at the frontend boundary

Even when backend validation exists, all data rendered into the DOM must be considered untrusted. The frontend should use a clear policy:

- prefer DOM creation and `textContent` for dynamic text where practical
- when HTML templates are retained, every dynamic text interpolation must pass through a single escaping helper
- attribute values must be escaped or constrained to trusted generated values
- tests must include malicious strings in post titles, content, usernames, report reasons, and reward descriptions

Alternatives considered:

- Ban all `innerHTML`: safest but can over-expand the refactor.
- Keep current ad hoc escaping: too hard to prove to reviewers.

### Decision 4: Correct the SQL-injection finding through evidence and tests

The repository query currently uses JPQL parameter binding. The change should document this and add/extend tests that demonstrate search input is treated as data, not executable SQL. If any string-concatenated native query is found during implementation, it must be replaced with parameter binding.

Alternatives considered:

- Rewrite all repository queries: unnecessary unless unsafe patterns are discovered.
- Ignore the finding: leaves an avoidable critical-looking criticism.

### Decision 5: Add lightweight API documentation before heavy tooling

The fastest path to a better review is a clear API inventory in documentation. OpenAPI/Swagger can be added if low-risk, but the minimum acceptable result is a documented endpoint table with authentication requirements, request/response examples, and error behavior.

Alternatives considered:

- Add Springdoc immediately: useful, but dependency and configuration risk should be weighed during implementation.
- Only rely on controller code: unfriendly for review and frontend collaboration.

### Decision 6: Make repository hygiene explicit and non-destructive

The project contains logs and runtime files in the working tree. The change should update `.gitignore`, define a delivery boundary, and clean only generated/runtime artifacts that are safe to remove. It must not revert user work or planning artifacts by accident.

Alternatives considered:

- Aggressively delete all untracked files: risky in this dirty worktree.
- Only update `.gitignore`: improves future hygiene but leaves current delivery unclear.

## Risks / Trade-offs

- [Risk] Splitting `app.js` can break page bootstrapping across multiple HTML entry points. -> Mitigation: preserve a single public entry module, keep `data-page` dispatch behavior, and run Vite build plus page-shell tests.
- [Risk] XSS hardening may miss a dynamic interpolation in a rarely used admin page. -> Mitigation: add test fixtures with malicious strings across all user-controlled content categories and audit `innerHTML` assignments after refactor.
- [Risk] Repository cleanup may remove files the user still wants. -> Mitigation: only ignore generated patterns by default; document candidates before destructive cleanup during implementation.
- [Risk] The previous smoke test may remain blocked by local MySQL credentials. -> Mitigation: document the exact blocker and provide commands/env variables required to complete it; complete it if credentials are available.
- [Risk] Adding lint/format tooling can create noisy diffs. -> Mitigation: scope formatting to touched frontend runtime/test files and document commands separately.
- [Risk] API documentation may drift from controllers. -> Mitigation: generate or verify the endpoint inventory from controller mappings where practical, then keep docs tied to verification tasks.

## Migration Plan

1. Add and verify delivery documentation first so the project has a stable review frame.
2. Update ignore rules and document the delivery boundary before removing generated artifacts.
3. Refactor the frontend runtime in small module slices while keeping the same public entry and page contracts.
4. Add rendering security tests and backend safety tests before or alongside security fixes.
5. Add API documentation and verification commands.
6. Run frontend build/tests and backend tests.
7. Complete or explicitly document live-data smoke-test evidence.

Rollback strategy: if runtime modularization causes regressions, keep the old `app.js` behavior as the reference and revert only the modularization slice while preserving docs, tests, and hygiene improvements.

## Open Questions

- Should API documentation be a Markdown endpoint inventory only, or should Springdoc/OpenAPI be added if dependency installation remains low-risk?
- Should generated logs be deleted during implementation, or only ignored and documented for a later cleanup commit?
- Can the user provide local MySQL credentials to complete the final live-data smoke test, or should the smoke-test result explicitly document the blocked environment?
