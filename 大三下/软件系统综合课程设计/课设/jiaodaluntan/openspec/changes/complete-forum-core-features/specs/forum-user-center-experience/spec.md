## ADDED Requirements

### Requirement: Users can view a complete personal center
The system SHALL provide an authenticated user center that displays profile information, campus identity status, level, points, authored posts, favorites, and browsing history.

#### Scenario: User opens personal center
- **WHEN** an authenticated user opens the personal center
- **THEN** the system displays current account data from the backend and lists the user's posts, favorites, and history with empty states where appropriate

### Requirement: Users can update profile information
The system SHALL allow authenticated users to update editable profile fields while preserving server-side validation and identity restrictions.

#### Scenario: User updates profile
- **WHEN** an authenticated user submits valid profile updates
- **THEN** the system persists the updates and refreshes the session display

#### Scenario: User submits invalid profile
- **WHEN** an authenticated user submits invalid email, overly long bio, or invalid campus data
- **THEN** the system rejects the update and shows the validation message without losing the form content

### Requirement: Users can view campus identity status
The system SHALL show whether the user's campus identity is verified, pending, rejected, or not submitted.

#### Scenario: Verified user opens profile
- **WHEN** a verified user opens the personal center
- **THEN** the system displays verified campus identity status and related school information

#### Scenario: Unverified user opens profile
- **WHEN** an unverified user opens the personal center
- **THEN** the system displays a clear action or explanation for campus identity completion

### Requirement: Users receive action feedback
The system SHALL provide visible, non-misleading feedback for important user actions including posting, commenting, favoriting, reporting, profile update, check-in, and redemption.

#### Scenario: Action succeeds
- **WHEN** a user completes a supported action successfully
- **THEN** the system shows success feedback and refreshes the affected visible data

#### Scenario: Action fails
- **WHEN** a user action fails because of validation, permission, network, or server error
- **THEN** the system shows a friendly error state or toast with the backend message
