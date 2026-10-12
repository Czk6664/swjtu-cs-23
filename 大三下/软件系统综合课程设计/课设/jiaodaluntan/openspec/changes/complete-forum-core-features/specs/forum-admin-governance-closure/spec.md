## ADDED Requirements

### Requirement: Administrators can process pending posts
The system SHALL allow administrators and authorized moderators to view pending posts and approve, reject, hide, or restore content according to role permissions.

#### Scenario: Admin approves pending post
- **WHEN** an administrator approves a pending post
- **THEN** the system marks the post as published, refreshes the pending list, and makes the post visible in public lists

#### Scenario: Unauthorized user opens governance page
- **WHEN** a normal user or visitor opens a governance page
- **THEN** the system blocks the operation and displays a friendly permission page rather than a blank screen or repeated redirect

### Requirement: Administrators can process reports
The system SHALL allow administrators and authorized moderators to review reports and record accepted or rejected outcomes.

#### Scenario: Admin accepts a report
- **WHEN** an administrator accepts a pending report
- **THEN** the system records the review decision, updates report status, and applies the configured content action when applicable

#### Scenario: Admin rejects a report
- **WHEN** an administrator rejects a pending report
- **THEN** the system records the decision and removes the report from the pending queue

### Requirement: Administrators can manage users
The system SHALL allow administrators to list users, inspect key account state, and ban or unban users without affecting administrator access.

#### Scenario: Admin bans user
- **WHEN** an administrator bans a normal user
- **THEN** the system disables that user's login/write capability and refreshes the user list status

#### Scenario: Admin cannot accidentally remove all admin access
- **WHEN** an administrator attempts an operation that would remove required administrator access
- **THEN** the system rejects the operation with a clear explanation

### Requirement: Administrators can manage sections
The system SHALL allow administrators to create, edit, and disable or delete forum sections while preventing unsafe deletion of sections that still contain posts.

#### Scenario: Admin creates section
- **WHEN** an administrator creates a section with valid name and description
- **THEN** the system stores the section and makes it available for browsing and post creation

#### Scenario: Admin deletes non-empty section
- **WHEN** an administrator attempts to delete a section containing posts
- **THEN** the system rejects the deletion and explains that existing posts must be moved, hidden, or handled first
