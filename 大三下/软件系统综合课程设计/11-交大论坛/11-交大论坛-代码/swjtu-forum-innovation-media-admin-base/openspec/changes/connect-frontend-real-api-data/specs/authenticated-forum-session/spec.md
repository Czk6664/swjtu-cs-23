## ADDED Requirements

### Requirement: Frontend SHALL establish and restore authenticated forum sessions
The frontend SHALL use the real `/api/auth/register`, `/api/auth/login`, and `/api/auth/me` endpoints to create, restore, and validate the current forum session. Successful authentication responses MUST be persisted to local storage and reflected in shared page state.

#### Scenario: Login succeeds
- **WHEN** a user submits valid credentials on the login page
- **THEN** the frontend SHALL call `/api/auth/login`, persist the returned token and user payload, and navigate the user to the intended forum page

#### Scenario: Session restores on page refresh
- **WHEN** a stored token exists and a protected page or authenticated action is opened
- **THEN** the frontend SHALL call `/api/auth/me` to refresh the current user profile before rendering authenticated-only data

### Requirement: Frontend SHALL guard authenticated actions
The frontend SHALL allow anonymous users to browse public read-only pages, but MUST require a valid authenticated session before executing protected actions such as posting, commenting, liking, favoriting, checking in, redeeming rewards, or using admin tools.

#### Scenario: Anonymous user triggers a protected action
- **WHEN** an unauthenticated user clicks a protected action from any page
- **THEN** the frontend SHALL prevent the write request, notify the user that login is required, and route or link them to the login entry

#### Scenario: Authenticated user triggers a protected action
- **WHEN** a logged-in user clicks a protected action
- **THEN** the frontend SHALL include the stored token in the request and allow the action to proceed

### Requirement: Frontend SHALL handle API envelopes and authorization failures consistently
The shared runtime SHALL unwrap the backend `ApiResponse<T>` envelope and MUST surface non-200 responses, 401 responses, and 403 responses through consistent UI feedback and state cleanup rules.

#### Scenario: API returns business failure
- **WHEN** an API call returns an `ApiResponse` whose `code` is not `200`
- **THEN** the frontend SHALL stop the normal success flow and display the backend-provided message to the user

#### Scenario: Token is invalid or expired
- **WHEN** a protected API call returns `401`
- **THEN** the frontend SHALL clear the invalid session, notify the user that login has expired, and redirect or prompt for re-authentication

#### Scenario: User lacks permission
- **WHEN** an API call returns `403`
- **THEN** the frontend SHALL keep the session intact and show a permission-denied message instead of treating the user as logged out
