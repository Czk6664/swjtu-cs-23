## ADDED Requirements

### Requirement: Users can discover forum content by section and keyword
The system SHALL allow visitors and logged-in users to browse published posts by section, keyword, and basic ordering without requiring authentication.

#### Scenario: Visitor filters posts by section
- **WHEN** a visitor opens a section from the forum home page
- **THEN** the system displays published posts from that section and a clear empty state if no posts exist

#### Scenario: Visitor searches posts by keyword
- **WHEN** a visitor submits a keyword search
- **THEN** the system displays matching published posts with title, author, section, time, and interaction counts

### Requirement: Users can create posts with review-aware feedback
The system SHALL allow authenticated users to create posts and SHALL show whether the post is published immediately or waiting for moderation.

#### Scenario: Normal post is published
- **WHEN** an authenticated user submits a valid post that does not require review
- **THEN** the system creates the post, clears the local draft, and navigates to the post detail page

#### Scenario: Risk post enters moderation
- **WHEN** an authenticated user submits a valid post that triggers moderation rules
- **THEN** the system saves the post as pending and shows a visible waiting-for-review message instead of pretending it is public

### Requirement: Users can manage their own posts
The system SHALL allow authenticated users to view, edit, and withdraw their own posts without granting access to other users' posts.

#### Scenario: User edits own post
- **WHEN** an authenticated user edits a post they authored
- **THEN** the system updates the post and shows the latest title, content, section, tags, and status

#### Scenario: User cannot edit someone else's post
- **WHEN** an authenticated user attempts to edit a post authored by another user
- **THEN** the system rejects the action with a friendly permission message

#### Scenario: User withdraws own post
- **WHEN** an authenticated user withdraws their own post
- **THEN** the system hides the post from public lists while preserving audit-related data such as comments, reports, and operation history

### Requirement: Post detail reflects true availability
The system SHALL show post details only when the viewer is allowed to read the post and SHALL explain unavailable, pending, hidden, or deleted states.

#### Scenario: Published post detail loads
- **WHEN** a visitor opens a published post detail page
- **THEN** the system displays post content, author, section, tags, comments, and interaction actions

#### Scenario: Hidden post detail is unavailable
- **WHEN** a visitor opens a hidden or withdrawn post
- **THEN** the system shows a clear unavailable-state page rather than a blank page or stale static content
