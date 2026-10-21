## ADDED Requirements

### Requirement: Forum home pages SHALL render live sections and live post feeds
The desktop and mobile forum home pages SHALL load section data from `/api/sections` and post feed data from `/api/posts/recommend` or `/api/posts/hot`, using the authenticated recommendation feed when a valid session exists and a public hot feed when it does not.

#### Scenario: Logged-in user opens the home page
- **WHEN** a valid session exists and the user opens a forum home page
- **THEN** the frontend SHALL request `/api/sections` and `/api/posts/recommend` and render the returned sections and posts in the home page slots

#### Scenario: Anonymous user opens the home page
- **WHEN** no valid session exists and the user opens a forum home page
- **THEN** the frontend SHALL request `/api/sections` and a public feed endpoint and render a readable home page without requiring login

### Requirement: Post detail pages SHALL load live post and comment data
The post detail page SHALL retrieve the selected post from `/api/posts/{id}` and its comments from `/api/posts/{id}/comments`, and MUST reflect real interaction counters and moderation visibility from backend data.

#### Scenario: Post detail loads successfully
- **WHEN** a user opens a valid post detail page
- **THEN** the frontend SHALL render the post body, author metadata, counters, and comment list using the backend response data

#### Scenario: Post does not exist or is inaccessible
- **WHEN** the post detail request fails with a not-found or forbidden response
- **THEN** the frontend SHALL replace the content area with an explicit error or unavailable state instead of leaving sample content in place

### Requirement: Forum write flows SHALL use live post and comment endpoints
The create-post page and comment interactions SHALL submit through `/api/posts` and `/api/posts/{id}/comments`, and the frontend MUST show the backend's real moderation or success message after submission.

#### Scenario: User publishes a new post
- **WHEN** an authenticated user submits a valid post form
- **THEN** the frontend SHALL call `/api/posts`, display the backend response message, and update navigation flow based on the created post result

#### Scenario: User comments on a post
- **WHEN** an authenticated user submits a valid comment
- **THEN** the frontend SHALL call `/api/posts/{id}/comments` and refresh or append the live comment list after success

### Requirement: Profile pages SHALL display live personal forum data
The profile page SHALL combine `/api/auth/me`, `/api/posts/mine`, `/api/posts/favorites`, and `/api/posts/history` to show the current user's forum profile, authored posts, favorites, and browse history.

#### Scenario: Profile page loads for a logged-in user
- **WHEN** an authenticated user opens the profile page
- **THEN** the frontend SHALL render the current user profile and at least one live personal-content section from backend data

#### Scenario: Profile page opens without authentication
- **WHEN** an unauthenticated visitor opens the profile page
- **THEN** the frontend SHALL block personal data loading and guide the visitor to log in before accessing the page
