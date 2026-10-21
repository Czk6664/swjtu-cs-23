## ADDED Requirements

### Requirement: Ignore rules cover generated and runtime artifacts
The repository SHALL ignore frontend dependencies, frontend build output, backend build output, IDE files, operating-system metadata, runtime logs, crash logs, and local temporary files.

#### Scenario: Runtime logs are created
- **WHEN** backend or frontend startup creates `.log`, `.out.log`, `.err.log`, or runtime crash files
- **THEN** those files are ignored by Git and documented as local artifacts

#### Scenario: Build artifacts are created
- **WHEN** Maven or Vite creates `target`, `dist`, or `node_modules` output
- **THEN** those generated paths are ignored and not treated as source files

### Requirement: Delivery boundary is explicit
The project SHALL define which files are intended for course submission and which files are local-only or process-only artifacts.

#### Scenario: Reviewer checks project root
- **WHEN** a reviewer inspects the root directory
- **THEN** source files, documentation, and configuration are distinguishable from local runtime files

### Requirement: Cleanup avoids destructive removal of user work
Repository cleanup MUST NOT remove tracked source, user-authored documentation, OpenSpec artifacts, or planning content unless the user explicitly requests it.

#### Scenario: Untracked planning files exist
- **WHEN** cleanup is performed in a dirty worktree
- **THEN** the cleanup process preserves unrelated untracked planning or user files

### Requirement: Hygiene verification is repeatable
The project SHALL provide a command or documented checklist to verify that generated artifacts and logs are ignored or excluded from delivery.

#### Scenario: Hygiene check runs
- **WHEN** the hygiene verification command or checklist is executed
- **THEN** it identifies remaining delivery-noise candidates without modifying files unexpectedly
