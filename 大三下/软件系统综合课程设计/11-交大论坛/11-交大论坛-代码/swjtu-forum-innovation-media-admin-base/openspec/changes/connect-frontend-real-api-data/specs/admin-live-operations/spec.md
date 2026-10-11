## ADDED Requirements

### Requirement: Admin overview SHALL render live moderation and operations summaries
The admin overview page SHALL use real admin endpoints to render pending moderation workload, report summary data, and pending redemption workload instead of static dashboard numbers.

#### Scenario: Admin overview loads successfully
- **WHEN** an authenticated admin opens the admin overview page
- **THEN** the frontend SHALL request the required admin summary data and render live counts or lists in the overview modules

#### Scenario: A summary request fails
- **WHEN** one admin overview data request fails while others succeed
- **THEN** the frontend SHALL keep successful modules visible and show an inline error state only for the failed module

### Requirement: Content governance pages SHALL perform live moderation workflows
The content governance page SHALL load real pending posts and reports from `/api/admin/posts/pending` and `/api/admin/reports`, and MUST execute review or moderation actions through the corresponding admin endpoints.

#### Scenario: Moderator reviews a report
- **WHEN** a moderator accepts or rejects a report from the governance page
- **THEN** the frontend SHALL call the live report review endpoint and update the reviewed item state in the UI

#### Scenario: Moderator updates a pending post status
- **WHEN** a moderator approves or rejects a pending post
- **THEN** the frontend SHALL submit the moderation request to the backend and refresh the pending-post list

### Requirement: User management SHALL use live user administration endpoints
The user management pages SHALL render live user lists from `/api/admin/users` and MUST use live ban and unban endpoints for account status changes.

#### Scenario: Admin bans a user
- **WHEN** an admin confirms a ban action on the user management page
- **THEN** the frontend SHALL call the live ban endpoint and update the affected user's visible status

#### Scenario: Admin opens user management without permission
- **WHEN** a non-admin session or unauthorized request accesses the user management page
- **THEN** the frontend SHALL show a permission error state rather than leaving static user examples in place

### Requirement: Recommendation strategy SHALL use live configuration and preview data
The recommendation strategy pages SHALL load the current recommendation configuration from `/api/admin/recommendations/config`, preview data from `/api/admin/recommendations/preview`, and submit config updates through the live update endpoint.

#### Scenario: Recommendation strategy page loads
- **WHEN** an authenticated admin opens the recommendation strategy page
- **THEN** the frontend SHALL render the current weight configuration and at least one live preview result from backend data

#### Scenario: Admin updates recommendation weights
- **WHEN** an admin submits a valid recommendation configuration update
- **THEN** the frontend SHALL call the live config update endpoint and reflect the saved values returned by the backend
