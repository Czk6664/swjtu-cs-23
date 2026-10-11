## ADDED Requirements

### Requirement: Verification matrix covers key roles
The project SHALL provide a verification matrix for guest, regular user, moderator, and admin journeys.

#### Scenario: Evaluator checks role coverage
- **WHEN** the verification documentation is reviewed
- **THEN** it lists the key pages, APIs, and expected outcomes for each supported role

### Requirement: Frontend tests cover runtime contracts
The frontend SHALL include repeatable tests for page shell markers, API runtime behavior, session behavior, safe rendering, and key page initialization.

#### Scenario: Frontend tests run
- **WHEN** the frontend verification command is executed
- **THEN** it checks both static page contracts and runtime behavior relevant to live API integration

### Requirement: Backend tests cover security and validation contracts
The backend SHALL include or maintain tests for authentication, authorization, validation, repository query safety, and key service/controller behavior.

#### Scenario: SQL safety concern is reviewed
- **WHEN** repository search behavior is tested with hostile input
- **THEN** the test demonstrates input is handled as data and does not alter query semantics

#### Scenario: Admin endpoint is accessed by non-admin
- **WHEN** a non-admin user attempts an admin-only operation in tests
- **THEN** the backend denies the operation

### Requirement: API documentation is verified against controllers
The project SHALL provide an API inventory that is checked against current controller mappings or generated from current backend routes.

#### Scenario: Controller endpoint changes
- **WHEN** a controller route is added, removed, or changed
- **THEN** the API documentation check or checklist identifies the documentation update needed

### Requirement: Live-data smoke-test status is explicit
The project SHALL complete the guest/user/admin live-data smoke test when the local backend and database are available, or document the exact environment blocker and commands needed to finish it.

#### Scenario: Database credentials are available
- **WHEN** the backend can connect to MySQL with demo seed enabled
- **THEN** the smoke test verifies guest browsing, student login actions, and admin governance pages against live data

#### Scenario: Database credentials are unavailable
- **WHEN** the smoke test cannot run because local database credentials are unavailable
- **THEN** the verification notes identify the blocker, failed endpoint, required environment variables, and remaining validation step
