## 1. Baseline And Safety Net

- [x] 1.1 Record the current local startup contract for backend, frontend, H2 data, default admin, and demo URLs
- [x] 1.2 Add a smoke-test checklist covering visitor, normal user, and administrator journeys before changing behavior
- [x] 1.3 Verify existing frontend and backend tests pass from the current baseline
- [x] 1.4 Identify remaining static mock content on core user and admin paths and list what must become live data or explicit empty state

## 2. Backend Content Lifecycle

- [x] 2.1 Review post status handling and define public, pending, hidden, rejected, and withdrawn read rules in service tests
- [x] 2.2 Add or complete backend support for editing a user's own post with title, content, section, cover image, and tags
- [x] 2.3 Add or complete backend support for withdrawing a user's own post using soft-delete or hidden-state semantics
- [x] 2.4 Ensure users cannot edit or withdraw posts authored by other users
- [x] 2.5 Ensure hidden or withdrawn posts do not appear in public lists, search, hot feed, or section feeds
- [x] 2.6 Ensure post creation returns enough status information for the frontend to distinguish published and pending-review posts

## 3. Backend Engagement And User Center

- [x] 3.1 Verify comment creation, validation, and moderation messages are covered by controller or service tests
- [x] 3.2 Verify like and favorite operations are idempotent and return updated visible state or counts
- [x] 3.3 Verify report creation prevents self-reporting and duplicate reports with friendly API errors
- [x] 3.4 Verify browse history is recorded only for readable posts and is ordered by latest visit
- [x] 3.5 Complete profile update behavior for editable user fields and campus identity display state
- [x] 3.6 Add backend tests for invalid profile updates and session refresh after profile changes

## 4. Backend Governance Closure

- [x] 4.1 Verify pending post approval, rejection, hide, and restore operations update status consistently
- [x] 4.2 Verify report review records accepted and rejected outcomes and removes handled reports from pending queues
- [x] 4.3 Verify user ban and unban behavior prevents disabled users from logging in or writing content
- [x] 4.4 Add guardrails that prevent accidentally removing all usable administrator access
- [x] 4.5 Complete section create, edit, and unsafe delete rejection behavior for non-empty sections
- [x] 4.6 Add governance tests for unauthorized visitor and normal-user access to admin endpoints

## 5. Frontend Runtime And Core Pages

- [x] 5.1 Split or clearly modularize the shared frontend runtime into API, session, rendering, route guard, and page-handler responsibilities
- [x] 5.2 Add a reusable search and section-filter UI on home or dedicated section views backed by live post data
- [x] 5.3 Update create-post flow to show published versus pending-review outcomes without misleading success navigation
- [x] 5.4 Add edit and withdraw controls for posts owned by the current user
- [x] 5.5 Update post detail to show reliable unavailable, pending, hidden, deleted, loading, empty, and error states
- [x] 5.6 Ensure all dynamic text from posts, comments, users, rewards, reports, and sections is escaped or safely rendered

## 6. Frontend User And Engagement Experience

- [x] 6.1 Update comment submission to refresh comments and counts after success
- [x] 6.2 Update like and favorite buttons to reflect authenticated state, current state, and updated counts
- [x] 6.3 Add report submission UI with backend reason validation and duplicate/self-report feedback
- [x] 6.4 Expand the personal center to show profile, campus identity status, authored posts, favorites, and browse history
- [x] 6.5 Add profile editing UI with validation feedback and session refresh after save
- [x] 6.6 Ensure unauthenticated write actions redirect to login with an intended return path

## 7. Frontend Admin Experience

- [x] 7.1 Update admin overview to show live pending posts, report summary, user counts, and clear empty states
- [x] 7.2 Update content governance page to approve, reject, hide, restore, and refresh live queues
- [x] 7.3 Update report review UI to accept or reject reports and show backend result feedback
- [x] 7.4 Update user management UI to ban and unban users with refreshed status display
- [x] 7.5 Add section management UI for create, edit, and unsafe delete feedback
- [x] 7.6 Ensure visitors and normal users see friendly permission pages for all admin routes

## 8. Verification And Delivery

- [x] 8.1 Add frontend runtime tests for search, protected actions, unsafe text escaping, empty states, and permission states
- [x] 8.2 Add or update backend tests for post lifecycle, engagement, profile, governance, and section management requirements
- [x] 8.3 Run `mvn test` and confirm all backend tests pass
- [x] 8.4 Run `npm test` and `npm run build` and confirm frontend verification passes
- [x] 8.5 Execute the visitor smoke journey against the running local app
- [x] 8.6 Execute the normal user smoke journey against the running local app
- [x] 8.7 Execute the administrator smoke journey against the running local app
- [x] 8.8 Document remaining known limitations explicitly instead of leaving hidden mock or broken paths
