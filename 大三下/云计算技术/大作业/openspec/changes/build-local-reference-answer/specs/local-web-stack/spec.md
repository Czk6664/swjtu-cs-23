## ADDED Requirements

### Requirement: Local project structure
The final project SHALL create a self-contained local application tree under `cloud-computing-final-project/` on the D drive workspace.

#### Scenario: Project tree is created
- **WHEN** implementation is complete
- **THEN** `cloud-computing-final-project/backend`, `cloud-computing-final-project/frontend`, and `cloud-computing-final-project/docker-compose.yml` exist with runnable local application files

### Requirement: Flask backend API
The backend SHALL expose a Flask API with `/api/ping` returning JSON status information and SHALL demonstrate Redis connectivity.

#### Scenario: Ping endpoint succeeds
- **WHEN** a user requests `GET /api/ping`
- **THEN** the backend returns a JSON response containing `status: "ok"`

#### Scenario: Redis-backed endpoint succeeds
- **WHEN** the backend container can reach Redis through the compose network
- **THEN** at least one endpoint records or reads a value from Redis and logs the request for screenshot evidence

### Requirement: Frontend identity page
The frontend SHALL serve an Nginx static page that visibly includes 程泽凯，王晨羽, 2023112621,2023114337, and 2023-04班.

#### Scenario: Frontend page shows identity
- **WHEN** the local frontend is opened in a browser
- **THEN** the first visible page includes the required name, student ID, and class

### Requirement: Docker build configuration
The local stack SHALL include Dockerfiles for backend and frontend plus Docker Compose for backend, frontend, and Redis.

#### Scenario: Compose stack starts locally
- **WHEN** `docker compose up --build` is run from `cloud-computing-final-project/`
- **THEN** backend, frontend, and Redis services start and can communicate through service names

### Requirement: Mirror-source friendly dependency installation
The Docker and dependency configuration SHALL prefer configurable mirror sources for Python package installation.

#### Scenario: Python dependencies use mirror argument
- **WHEN** the backend Docker image is built
- **THEN** the build supports a configurable `PIP_INDEX_URL` argument with a China-friendly default mirror
