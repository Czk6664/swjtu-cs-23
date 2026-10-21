## ADDED Requirements

### Requirement: Growth center SHALL render live check-in and points data
The growth center page SHALL load the authenticated user's check-in history from `/api/growth/check-ins` and points history from `/api/growth/points-history`, and MUST show backend-derived status rather than static placeholder metrics.

#### Scenario: Growth page loads successfully
- **WHEN** an authenticated user opens the growth center
- **THEN** the frontend SHALL request live growth endpoints and render check-in, points, or progress sections from returned data

#### Scenario: Growth data is empty
- **WHEN** the backend returns an empty but successful growth response
- **THEN** the frontend SHALL show an explicit empty state instead of sample growth records

### Requirement: Growth center SHALL execute live check-in actions
The growth center SHALL submit the check-in action through `/api/growth/check-in` and refresh visible growth data after a successful response.

#### Scenario: First check-in of the day succeeds
- **WHEN** an authenticated user triggers the check-in action and the backend accepts it
- **THEN** the frontend SHALL show the backend success message and update the visible growth summary or history

#### Scenario: User has already checked in today
- **WHEN** the backend rejects the check-in because the user has already checked in
- **THEN** the frontend SHALL surface that business message without duplicating the action locally

### Requirement: Rewards mall SHALL render live rewards and redemption history
The rewards mall page SHALL load available rewards from `/api/growth/rewards` and the current user's redemption history from `/api/growth/redemptions`, and MUST replace sample items with backend-provided reward data.

#### Scenario: Rewards list loads successfully
- **WHEN** an authenticated user opens the rewards mall
- **THEN** the frontend SHALL render reward cards and redemption records from live backend responses

#### Scenario: No rewards are currently available
- **WHEN** the rewards endpoint returns no active rewards
- **THEN** the frontend SHALL show a dedicated empty state for the rewards area

### Requirement: Rewards mall SHALL submit live redemption requests
The rewards mall SHALL submit reward redemption requests through `/api/growth/rewards/{id}/redeem` and MUST reflect the returned request result or failure reason in the UI.

#### Scenario: Redemption succeeds
- **WHEN** an authenticated user redeems an available reward with sufficient points
- **THEN** the frontend SHALL show the backend success message and refresh reward stock or redemption history

#### Scenario: Redemption fails due to business constraints
- **WHEN** the backend rejects the redemption because of insufficient points, no stock, or inactive reward status
- **THEN** the frontend SHALL show the returned failure message and keep the existing page state consistent
