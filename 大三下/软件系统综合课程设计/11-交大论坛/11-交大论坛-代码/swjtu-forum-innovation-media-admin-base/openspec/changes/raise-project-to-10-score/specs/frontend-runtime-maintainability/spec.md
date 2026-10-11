## ADDED Requirements

### Requirement: Shared frontend runtime is modular
The frontend SHALL split the large shared runtime into focused ES modules for routing/bootstrap, API access, session state, DOM helpers, shared render helpers, page renderers, and action binding.

#### Scenario: Developer opens frontend runtime
- **WHEN** a developer needs to change authentication, API handling, or a specific page renderer
- **THEN** the relevant code is located in a focused module instead of a monolithic 1500+ line file

### Requirement: Existing page shell contracts remain stable
The frontend runtime MUST preserve existing HTML page contracts including `data-page`, `data-slot`, navigation links, and Vite build entry behavior.

#### Scenario: Existing page loads after refactor
- **WHEN** any current MPA page is opened through Vite
- **THEN** the same page-specific renderer initializes from the existing `data-page` value

#### Scenario: Existing tests inspect shell markers
- **WHEN** frontend shell-marker tests run
- **THEN** required `data-slot` markers remain present and compatible

### Requirement: Runtime state handling remains consistent
The frontend SHALL keep unified behavior for API errors, loading states, empty states, JWT injection, session restoration, login guards, role guards, and toast feedback.

#### Scenario: API call fails
- **WHEN** a live API request fails or returns a non-success `ApiResponse`
- **THEN** the page displays a consistent user-friendly error state without losing navigation

#### Scenario: Protected action is attempted while logged out
- **WHEN** an unauthenticated user attempts a protected action
- **THEN** the session guard redirects or prompts consistently with the existing behavior

### Requirement: Formatting and linting expectations are documented
The frontend SHALL define repeatable formatting or linting expectations for changed runtime modules.

#### Scenario: Contributor modifies frontend runtime
- **WHEN** a contributor changes runtime modules
- **THEN** the documented quality command or checklist can be used to verify readable, consistent code style
