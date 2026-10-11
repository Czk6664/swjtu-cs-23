## ADDED Requirements

### Requirement: Core user journeys are smoke-tested
The system SHALL provide a repeatable smoke-test checklist or automated script covering visitor, normal user, and administrator journeys against the local runnable application.

#### Scenario: Visitor journey passes
- **WHEN** the smoke test runs the visitor journey
- **THEN** it verifies home page load, section navigation, search, and post detail access without authentication

#### Scenario: User journey passes
- **WHEN** the smoke test runs the normal user journey
- **THEN** it verifies login or registration, post creation, comment submission, like, favorite, report, profile, and logout

#### Scenario: Admin journey passes
- **WHEN** the smoke test runs the administrator journey
- **THEN** it verifies admin login, pending post handling, report handling, user management, section management, and protected-route behavior

### Requirement: Local origins work consistently
The system SHALL support local development and demo access through both `localhost` and `127.0.0.1` for the configured frontend ports.

#### Scenario: Browser uses 127.0.0.1
- **WHEN** the frontend is opened from `http://127.0.0.1:5173`
- **THEN** authenticated API requests succeed with the same behavior as `http://localhost:5173`

### Requirement: Pages have reliable loading, empty, and error states
The system SHALL display explicit loading, empty, and error states for dynamic data areas and SHALL NOT leave users with blank pages or stale mock content.

#### Scenario: API returns empty list
- **WHEN** a page requests data and the backend returns an empty list
- **THEN** the page displays a friendly empty state with the next available action

#### Scenario: API returns error
- **WHEN** a page request fails due to permission, validation, server, or network error
- **THEN** the page displays a readable error message and a recovery action when possible

### Requirement: Runtime avoids unsafe dynamic rendering
The system SHALL escape or safely render backend-provided text in all dynamic page areas.

#### Scenario: Malicious content is returned
- **WHEN** backend data contains HTML or script-like text in title, content, comments, username, reward, or report fields
- **THEN** the frontend renders it as text and does not execute it as HTML or JavaScript
