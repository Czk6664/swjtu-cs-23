## ADDED Requirements

### Requirement: Users can comment on readable posts
The system SHALL allow authenticated users to comment on posts they are allowed to read and SHALL display validation or moderation feedback from the backend.

#### Scenario: User submits a valid comment
- **WHEN** an authenticated user submits a valid comment on a published post
- **THEN** the system stores the comment, refreshes the visible comment list, and updates the comment count

#### Scenario: Comment is rejected by validation
- **WHEN** an authenticated user submits an empty, too-long, or moderated comment
- **THEN** the system keeps the user on the post detail page and shows the backend validation message

### Requirement: Users can like and favorite posts
The system SHALL allow authenticated users to like and favorite published posts and SHALL keep repeated clicks idempotent.

#### Scenario: User toggles favorite
- **WHEN** an authenticated user favorites or unfavorites a published post
- **THEN** the system updates the visible favorite state and count without creating duplicate records

#### Scenario: Anonymous user attempts interaction
- **WHEN** a visitor clicks like, favorite, or comment
- **THEN** the system redirects or prompts the visitor to log in and preserves the intended return page

### Requirement: Users can report inappropriate posts
The system SHALL allow authenticated users to report published posts with a permitted reason and SHALL prevent duplicate self-report or repeat-report submissions.

#### Scenario: User reports a post
- **WHEN** an authenticated user submits a report reason for another user's post
- **THEN** the system creates a pending report and shows confirmation that administrators can review it

#### Scenario: User cannot report own post
- **WHEN** an authenticated user reports a post they authored
- **THEN** the system rejects the report with a friendly explanation

### Requirement: Browsing history is recorded for logged-in users
The system SHALL record readable post visits for authenticated users and SHALL expose the latest history in the user center.

#### Scenario: User opens post detail
- **WHEN** an authenticated user opens a readable post detail page
- **THEN** the system records or refreshes the browse history entry for that post
