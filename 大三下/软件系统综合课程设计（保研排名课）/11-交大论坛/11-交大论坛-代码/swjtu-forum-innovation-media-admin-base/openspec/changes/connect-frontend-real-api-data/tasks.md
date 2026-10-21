## 1. Shared Runtime And Session

- [x] 1.1 Rebuild `frontend/assets/app.js` into a shared API runtime that unwraps `ApiResponse`, injects JWT, and handles loading, empty, and error states consistently
- [x] 1.2 Implement real login, register, session restore, logout, and `/api/auth/me` synchronization against the backend auth endpoints
- [x] 1.3 Add protected-action guards so unauthenticated users are redirected or prompted before write operations

## 2. Forum Content Pages

- [x] 2.1 Connect desktop and mobile home pages to `/api/sections` plus live feed endpoints and replace static home feed content with rendered backend data
- [x] 2.2 Connect the post detail page to `/api/posts/{id}` and `/api/posts/{id}/comments`, including live error and unavailable states
- [x] 2.3 Connect create-post and comment submission flows to live post and comment endpoints with backend success and moderation feedback
- [x] 2.4 Connect the profile page to `/api/auth/me`, `/api/posts/mine`, `/api/posts/favorites`, and `/api/posts/history`

## 3. Growth And Rewards

- [x] 3.1 Connect the growth center to `/api/growth/check-ins` and `/api/growth/points-history` with proper empty-state rendering
- [x] 3.2 Connect the growth center check-in action to `/api/growth/check-in` and refresh visible growth data after success
- [x] 3.3 Connect the rewards mall to `/api/growth/rewards` and `/api/growth/redemptions`
- [x] 3.4 Connect reward redemption actions to `/api/growth/rewards/{id}/redeem` and reflect backend validation messages in the UI

## 4. Admin And Governance

- [x] 4.1 Connect the admin overview to live pending-post, report-summary, and pending-redemption endpoints
- [x] 4.2 Connect the content governance page to live report review and post moderation endpoints
- [x] 4.3 Connect the user management pages to `/api/admin/users` plus live ban and unban actions
- [x] 4.4 Connect the recommendation strategy pages to live config, preview, and config update endpoints

## 5. Verification

- [x] 5.1 Add or update frontend verification for authenticated runtime behavior and required page shell markers
- [x] 5.2 Run frontend build and targeted backend or integration checks to verify the live-data pages work against current API contracts
- [ ] 5.3 Smoke-test the key user journey and admin journey with seeded or demo backend data, removing any remaining hard-coded mock content from those paths
