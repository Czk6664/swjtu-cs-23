# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

`jiaodaluntan` is a campus forum system for course-design/demo use. The repository is split into:

- `backend/`: Spring Boot 3.2 + Spring Security + Spring Data JPA API server
- `frontend/`: Vite multi-page frontend (plain HTML/JS page bundles, not a single `src/` SPA)

The backend is the system of record. The frontend talks to it through the Vite dev proxy (`/api` -> `http://localhost:8080`) and backend responses are wrapped in a shared `ApiResponse` shape.

There is no repository README at the root today, so this file is the main orientation document for future Claude instances.

## Common commands

Run commands from the `jiaodaluntan/` directory unless noted otherwise.

### Frontend

```bash
cd frontend
npm install
npm run dev
npm run build
npm run preview
```

Notes:
- The Vite dev server runs on port `5173`.
- This frontend is configured as `appType: 'mpa'` in `frontend/vite.config.js`; each feature page is a separate HTML entry, not a router-driven SPA.

### Backend

```bash
cd backend
mvn spring-boot:run
mvn test
mvn -Dtest=ClassName test
mvn -Dtest=ClassName#methodName test
mvn clean package
```

Notes:
- Backend runs on port `8080` with context path `/api`.
- The default profile needs no environment variables. `backend/src/main/resources/application.yml` defaults the datasource to a local H2 file (`jdbc:h2:file:./data/swjtu-forum-local`, MySQL compatibility mode) and provides a default `JWT_SECRET` (`swjtu-forum-local-secret-key-change-before-public-deploy`). Set `JWT_SECRET` only to override it before a public deploy.
- On startup `LocalDataBootstrapRunner` auto-seeds an admin (`admin` / `admin123456`), the standard sections, and a welcome post into the local H2 database (gated by `app.bootstrap.enabled`, default `true`).
- Redis is configured in `application.yml` with `localhost` defaults but is not required for the default local run.
- MySQL is an optional deployment mode via the Spring `mysql` profile (`application-mysql.yml`): `mvn spring-boot:run -Dspring-boot.run.profiles=mysql` (expects `DB_USERNAME`/`DB_PASSWORD`, and you should set a real `JWT_SECRET`).
- A separate demo-seed mode exists via the `demo` profile (`application-demo.yml`), which uses its own H2 file (`swjtu-forum-demo`) and runs `DemoSeedService`/`DemoSeeder`: `mvn spring-boot:run -Dspring-boot.run.profiles=demo`.

### Full-stack local development

There is a one-click launcher at the repo root (`start.ps1`, PowerShell) that frees ports `8080`/`5173`, starts both services, and polls backend readiness. Backend port is configurable (`-BackendPort`), and the Vite proxy follows it via the `BACKEND_PORT` env var.

To run manually, start backend first, then frontend:

```bash
cd backend && mvn spring-boot:run
cd frontend && npm run dev
```

Open the Vite-served page entry you need.

## Architecture

### Big picture

This is a split frontend/backend monolith for a campus forum product with four major business areas:

- forum content flows: posts, comments, likes, favorites, browse history, reports
- growth/gamification: check-in, points, rewards, redemption requests
- recommendation/discovery: hot feed, search, tag-based recommendation, “not interested” feedback
- admin/moderation: post review, comment moderation, user ban/unban, section management, report summaries, recommendation weight tuning

### Backend structure

Backend entry point:
- `backend/src/main/java/com/swjtu/forum/ForumApplication.java`

Main backend layering:
- `controller/`: REST endpoints
- `service/`: business logic and transaction boundaries
- `repository/`: Spring Data JPA persistence
- `entity/`: JPA model objects
- `dto/`: request/response payloads
- `security/`: JWT auth filter, security config, auth failure handlers
- `exception/`: API exceptions and global exception mapping
- `config/`: startup wiring — `LocalDataBootstrapRunner` (default local H2 seeding of admin/sections/welcome post) and demo-seed wiring (`DemoSeedRunner`, `DemoSeedProperties`)

Important backend patterns:
- Security is stateless JWT-based. `backend/src/main/java/com/swjtu/forum/security/SecurityConfig.java` permits anonymous access for login/register and GET reads on posts/sections; most writes require authentication.
- Method-level authorization is used for moderator/admin actions with `@PreAuthorize`.
- Controllers generally return `ApiResponse<T>`; global error translation lives in `backend/src/main/java/com/swjtu/forum/exception/GlobalExceptionHandler.java`.
- `PostController` owns the public content API surface, but its implementation is split: `PostService` handles forum CRUD/interactions while `GrowthDiscoveryService` handles search, recommendations, and disinterest signals, and `ReportService` handles post reports.
- `GrowthController` is the user-facing growth domain: interests, check-in, points history, rewards, redemption history.
- `AdminController` is the operational backend for moderation, user management, section management, reward review, report review, recommendation tuning, and the analytics dashboard (`GET /admin/analytics`, served by `AnalyticsService`).
- `AdminOpsService` is the admin-side write path for content, comments, users, sections, and operation logs.
- `NotificationController` + `NotificationService` own the in-app notification center; domain services call `notify*` as side effects (reply/comment, report decision, level-up, redemption review, new follower).
- `FollowService` (exposed via `UserController` `/users/{id}/follow*`) owns the social graph; followed-author posts feed a social-signal boost inside `GrowthDiscoveryService`'s recommendation scoring.
- Concurrency-sensitive counters use atomic conditional UPDATEs (`RewardItemRepository.decrementStock`, `UserRepository.deductPoints`) rather than read-modify-write, to prevent oversell / negative balances.

### Data model shape

The relational model in `backend/src/main/resources/schema.sql` centers on:

- `users`
- `sections`
- `tags`
- `posts`
- `comments`
- interaction tables for tags, likes, favorites, browse history, and disinterest
- growth tables such as `daily_check_in`, `points_history`, `reward_items`, `redemption_requests`
- admin/reporting tables such as `reports`, `report_review_logs`, `operation_logs`, and `recommendation_configs`
- social/notification tables: `notifications` (per-user in-app notifications) and `user_follows` (directed follow graph, unique on follower+following)

When changing backend behavior, verify whether cached counters and derived fields are updated in the same service method (`post_count`, like/comment/favorite counts, `heat_score`, user points/exp, reward stock).

### Frontend structure

The frontend is not organized under `frontend/src/`. Instead, each page is its own entry directory referenced in `frontend/vite.config.js`, for example:

- `home_recommended/`
- `post_details/`
- `create_post/`
- `profile_overview/`
- `growth_center/`
- `rewards_mall/`
- `admin_overview/`
- `content_governance/`
- `user_management/`
- `recommendation_strategy/`

Treat this as a Vite multi-page app with shared static assets in `frontend/assets/` and page-specific scripts/styles colocated with each page entry.

A key frontend pattern is that `frontend/assets/app.js` acts as the shared runtime for all page entries. It centralizes:
- route mapping between page keys and `code.html` entries
- `localStorage` auth state (`token`, `userInfo`, draft state)
- the common `/api` fetch wrapper and `ApiResponse` handling
- page bootstrapping based on `document.body.dataset.page`
- shared UI actions, toasts, modal flows, and admin/user interactions

When debugging frontend behavior, check both the page-specific HTML entry and `frontend/assets/app.js` before assuming logic is local to that page.

### Integration points

- Frontend requests should target `/api/...`; Vite proxies that to the backend in local dev.
- Backend base path is `/api`, so direct backend routes are effectively `/api/auth/...`, `/api/posts/...`, `/api/growth/...`, `/api/admin/...`, etc.
- Anonymous browsing is supported for read-only forum content, while interactive features depend on JWT-authenticated requests.
- Recommendation behavior depends on both post engagement data and user tag preferences; admin pages can tune recommendation weights through backend APIs.
- The frontend expects successful backend responses in the existing envelope shape and treats `code !== 200` as an error in `frontend/assets/app.js`.

## Operational details

- `backend/src/main/resources/application.yml` is environment-variable-driven (datasource, Redis, logging, port, JWT secret), but every value has a default. The default datasource is a local H2 file in MySQL compatibility mode, so the app starts with zero env vars set.
- The `mysql` profile (`application-mysql.yml`) switches the datasource to MySQL (`swjtu_forum`) and disables the H2 console; it is the optional formal-deployment mode.
- Spring JPA is configured with `ddl-auto: update`, but `schema.sql` is still the clearest source of intended schema shape.
- `backend/src/main/resources/application-demo.yml` enables guarded demo seeding on its own H2 file (`swjtu-forum-demo`). `DemoSeedService` / `DemoSeeder` create demo users, sections, posts, rewards, redemption cases, and moderation data for presentation scenarios. This is separate from the default `LocalDataBootstrapRunner` seeding, which runs on the default (no-profile) local H2 database.
- The repo already contains built frontend artifacts (`frontend/dist/`) and installed dependencies (`frontend/node_modules/`); avoid treating them as source of truth.
- The backend also contains `target/` outputs and surefire reports from prior runs; prefer `src/main` and `src/test` over generated files.

## Working guidance for future edits

- Prefer reading the backend service layer before changing controller behavior; core business rules are concentrated there.
- When a feature touches moderation, recommendation, reporting, or growth, check multiple services rather than assuming one controller maps to one service.
- When editing the frontend, start from `frontend/vite.config.js` to identify the actual page entry used by the flow you are changing.
- Preserve the existing API envelope (`ApiResponse`) and role model (`USER` / `MODERATOR` / `ADMIN`) unless the task explicitly changes them.
