Below is a structured approach to planning and implementing this project. It is broken into multiple layers: (1) A detailed blueprint, (2) A set of high-level iterative chunks, (3) A refined breakdown of each chunk into smaller steps, and (4) A series of prompts for a code-generation LLM to follow in a test-driven, incremental manner. Each prompt builds on the previous one, ensuring that there is no orphaned or hanging code.

---

## 1. Detailed Step-by-Step Blueprint

### 1.1 Project Initialization & Architecture
1. Create two main folders (or repositories, depending on preference):  
   • backend (Python FastAPI)  
   • frontend (React)

2. Establish a shared CI/CD pipeline that:  
   • Installs dependencies  
   • Runs lint checks and tests  
   • Builds Docker images for each service  

3. Containerize both the backend and frontend using Docker.  
   • Dockerfile for the FastAPI backend (including Uvicorn/Gunicorn)  
   • Dockerfile for the React frontend (building a static bundle served by an Nginx container or deployed to a service like Netlify)

4. Initialize a PostgreSQL database (can be a Docker container). Ensure the schema matches the TRD.

5. Plan hosting and orchestration details (e.g., AWS ECS/EKS, GCP Cloud Run / GKE, or on-premise Kubernetes).

### 1.2 Database Schema & Models
Use the TRD to set up the following tables (with recommended columns and constraints):
• USERS  
• COMPLIANCE_TASKS  
• TASK_DOCUMENTS  
• DOCUMENTS  
• AUDIT_LOG  
• COMPLIANCE_RECORDS (if needed, or potentially replace with more granular entity-based tables)  
• LP_DETAILS  
• LP_DRAWDOWNS  

Implement Alembic (or similar) for database migrations:
• One migration for the initial schema.  
• Include indexes for commonly queried fields (such as deadlines, user_ids).

### 1.3 Authentication & RBAC
1. Use FastAPI security features (OAuth2PasswordBearer) or a custom JWT approach.  
2. Implement password hashing (e.g., using passlib).  
3. Implement multi-factor authentication (e.g., TOTP-based).  
4. Introduce role-based access control (Fund Manager, Compliance Officer, LP, etc.) to limit access to certain routes.

### 1.4 Backend Modules
Structure your FastAPI application with clear route groupings:

• /api/auth: Contains endpoints for login, logout, token refresh, MFA setup.  
• /api/users: User management endpoints (create, update, retrieve users, etc.).  
• /api/tasks: Compliance task management (CRUD, dependent tasks, state transitions, etc.).  
• /api/documents: Document repository endpoints (upload, list, search, link to tasks).  
• /api/reports: Generation of real-time compliance status, activity logs, custom CSV/PDF exports.  
• /api/integrations: Interaction with Google Drive, email, calendar, Slack/WhatsApp, and any banking/accounting APIs.  
• /api/audit-logs: Logging user/system actions for detailed audit.

### 1.5 Task & Workflow Management
1. Store compliance tasks in COMPLIANCE_TASKS with references to assignee, reviewer, etc.  
2. For dependent tasks, implement logic to check if the parent task is Completed before the child can transition to in-progress states.  
3. Implement recurring tasks by storing a recurrence pattern (e.g., “Monthly,” “Quarterly,” “Yearly”).

### 1.6 Document Repository
1. Integrate Google Drive or local storage (depending on environment/requirements) for storing documents.  
2. Provide endpoints to:  
   • Upload a new document and store metadata (in DOCUMENTS)  
   • Search/delete documents  
   • Link documents to tasks (TASK_DOCUMENTS table)

### 1.7 Notification & Integration
1. Set up Slack/WhatsApp/email notifications whenever tasks change state or approach a deadline.  
2. Use a CRON-like approach (Celery, RQ, or APScheduler) for recurring reminders.  
3. Integrate with external accounting/banking APIs if needed for financial oversight.

### 1.8 Reporting & Audit Trails
1. Create custom endpoints to provide real-time compliance status across tasks, with filtering by category (SEBI, RBI, IT/GST, etc.).  
2. Generate PDF/CSV exports as needed.  
3. Log every operation (CRUD, login, file upload) in AUDIT_LOG with user_id and timestamp.

### 1.9 Frontend (React)
1. Use Create React App (or Vite) to scaffold the project.  
2. Set up React Router for SPA navigation.  
3. Use a state management solution (Redux or Zustand) to store user sessions and global data.  
4. Build the following UI modules:  
   • Login screen (MFA support)  
   • Admin dashboard (overview of tasks, logs, calendar)  
   • Task management interface (task list, detail view, create/edit form)  
   • Document repository interface (upload, search, link to tasks)  
   • Reporting & analytics view (charts/lists of compliance data)  
   • LP onboarding screens (list, create/edit, drawdown info)  

### 1.10 Testing & Deployment
1. Write unit tests for each FastAPI route using Pytest.  
2. Write frontend tests using Jest and React Testing Library.  
3. Perform end-to-end tests with frameworks like Cypress or Playwright (optional).  
4. Configure a CI/CD pipeline that runs all tests on each commit.  
5. Deploy to a chosen environment (e.g., AWS, GCP, on-prem) with container orchestration.

---

## 2. High-Level Iterative Chunks

Below is an incremental plan that builds upon itself:

1. [Chunk A] Project Setup & CI/CD  
2. [Chunk B] Database Setup & User Model  
3. [Chunk C] Basic Auth & RBAC (with Tests)  
4. [Chunk D] Compliance Task Module (with Tests)  
5. [Chunk E] Document Repository Module (with Tests)  
6. [Chunk F] Audit Logging & Reporting (with Tests)  
7. [Chunk G] External Integrations (Slack/Email/Google Drive)  
8. [Chunk H] React Frontend Fundamentals (Routing, Login, MFA UX)  
9. [Chunk I] React Task & Document Management UI  
10. [Chunk J] Continuous QA, Final Integration & Deployment

---

## 3. Refined Breakdown of Each Chunk

This section breaks each chunk into smaller steps to ensure a safe and testable increment.

### Chunk A: Project Setup & CI/CD
1. Initialize Git repositories (backend, frontend).  
2. Add Docker configurations (Dockerfile, docker-compose).  
3. Create a minimal FastAPI “hello world” endpoint.  
4. Configure linting (Flake8/Black for Python, ESLint/Prettier for JS).  
5. Configure a CI workflow (GitHub Actions, GitLab CI, or Jenkins) to run linting and minimal tests.

### Chunk B: Database Setup & User Model
1. Install and configure SQLAlchemy, Alembic (or similar migration tool).  
2. Write the initial migration for the USERS table.  
3. Implement a basic User model class in FastAPI.  
4. Add minimal tests to ensure the table is created and basic user creation works.

### Chunk C: Basic Auth & RBAC (with Tests)
1. Implement password hashing and JWT authentication.  
2. Implement roles (Fund Manager, Compliance Officer, LP, etc.) in the user table.  
3. Create endpoints for user registration, login, logout, token refresh.  
4. Write tests to verify that:  
   • Users can register and log in.  
   • Auth tokens are issued.  
   • Certain endpoints require specific roles.

### Chunk D: Compliance Task Module (with Tests)
1. Create the COMPLIANCE_TASKS table with relevant fields (deadline, recurrence, state).  
2. Write endpoints:  
   • Create a task  
   • Retrieve tasks (filter by date, assignee, state)  
   • Update task states (open → completed, etc.)  
   • Manage dependency relationships  
3. Implement unit tests to validate the logic and state transitions.

### Chunk E: Document Repository Module (with Tests)
1. Set up the DOCUMENTS table plus the TASK_DOCUMENTS join table.  
2. Implement file upload logic (perhaps storing locally at first).  
3. Write endpoints for:  
   • Uploading documents  
   • Listing documents (with search/filter)  
   • Linking documents to tasks  
4. Write tests to confirm:  
   • Documents are stored or linked properly  
   • Upload constraints (e.g., file type, size) are enforced

### Chunk F: Audit Logging & Reporting (with Tests)
1. Implement the AUDIT_LOG table and write a small service that records every user action.  
2. Integrate it into endpoints so each CRUD call logs automatically.  
3. Implement at least one reporting endpoint (e.g., number of tasks completed, overdue tasks, etc.).  
4. Write tests that confirm logs are created and the reporting endpoint filters data correctly.

### Chunk G: External Integrations (Slack/Email/Google Drive)
1. Provide a configuration-driven approach to enable/disable Slack, email, or WhatsApp notifications.  
2. Implement logic to send a notification once a task transitions states or is near its deadline.  
3. Integrate the Google Drive API for file storage (migrating from local storage if needed).  
4. Write integration tests (or mocks) to ensure that notifications are dispatched correctly.

### Chunk H: React Frontend Fundamentals (Routing, Login, MFA UX)
1. Scaffold a new React app and set up React Router.  
2. Build a login screen that calls the FastAPI /api/auth endpoints.  
3. Incorporate an MFA flow once the user logs in (e.g., a TOTP code input).  
4. Write basic React tests (Jest + React Testing Library) for the login flow.

### Chunk I: React Task & Document Management UI
1. Create a task listing page (fetch tasks from /api/tasks).  
2. Task detail page with the ability to update states or attach documents.  
3. Document repository page with upload/search functionality.  
4. Write tests (and snapshot tests for UI) ensuring correct rendering and interactions.

### Chunk J: Continuous QA, Final Integration & Deployment
1. Integrate end-to-end tests for user flows (Cypress, Playwright, or similar).  
2. Ensure all features (Auth, Tasks, Documents, Integrations) work together.  
3. Optimize performance, finalize security checks (HTTPS, CORS rules).  
4. Deploy to production environment and confirm logs/monitoring are in place.

---

## 4. Test-Driven Implementation Prompts for a Code-Generation LLM

Below is a series of prompts that can be given to your chosen code-generation LLM. Each section is separated with markdown code fences and is labeled as text. Every prompt references and builds on previous steps, ensuring no orphaned or hanging code.  

---

### Prompt A: Project Setup & CI/CD

```text
You are building the foundational project setup for a FastAPI + React application. Follow a test-driven approach. 

Requirements:
1. Initialize a backend directory with:
   - A minimal FastAPI "hello world" endpoint.
   - A Dockerfile to run FastAPI with Uvicorn.
   - Linting (Black/Flake8) configured.
   - A simple Pytest file that confirms a GET request to the root endpoint returns "Hello World".

2. Initialize a frontend directory with:
   - A minimal React app created via Create React App (or Vite).
   - ESLint + Prettier configured.
   - A Dockerfile to build and serve the static site (e.g., from Nginx).
   - A minimal test (Jest + React Testing Library) that checks for “Hello React” in the App component.

3. Create a GitHub Actions (or similar) CI pipeline that:
   - Installs dependencies for both backend and frontend.
   - Runs all tests.
   - Builds Docker images for both backend and frontend.

Step-by-step:
- Write the test files first (for both backend and frontend).
- Then implement just enough code to pass these tests.
- Provide the Docker settings (Dockerfile, docker-compose as needed).

Implement this and ensure that everything can be run locally with:
   docker-compose up
```

---

### Prompt B: Database Setup & User Model

```text
You have completed the initial project scaffolding with minimal tests for the backend and frontend. Next, set up the database and create a basic User table.

Requirements:
1. Use PostgreSQL (through docker-compose).
2. Install and configure SQLAlchemy and Alembic for the FastAPI backend.
3. Create an initial Alembic migration that generates the USERS table as per the TRD:
   - user_id (primary key, int or UUID)
   - name
   - email
   - role
   - password_hash
   - mfa_enabled
   - phone (nullable)
   - created_at
   - updated_at
4. Write a User model class that maps to the USERS table.
5. Add a test that:
   - Inserts a User record (via the FastAPI endpoint or direct DB session).
   - Confirms that the record is inserted in the database.

Step-by-step:
- Write the test first to confirm the database insert.
- Then write the migration and model code.
- Finally, confirm the test passes.
```

---

### Prompt C: Basic Auth & RBAC (with Tests)

```text
Now that you have a USERS table and a working database, you will add authentication and role-based access control.

Requirements:
1. Password hashing using passlib (bcrypt or argon2).
2. JWT authentication flow:
   - POST /api/auth/login to receive an access token.
   - Access token used in Authorization header on subsequent requests.
3. A separate route that requires authentication (e.g., /api/users/me) to return the current user’s info.
4. Enforce basic roles (e.g., "Fund Manager", "Compliance Officer", "LP") in endpoints. For now, just demonstrate one protected endpoint that only "Fund Manager" can call.
5. Add tests that:
   - Attempt to access a protected route without a token (should fail).
   - Access it with a valid token (should pass).
   - Attempt to call a role-protected route with the wrong role (should fail).

Step-by-step:
- Write tests to capture the above scenarios.
- Implement the authentication logic, then the RBAC checks.
- Ensure you store hashed passwords in the DB.
- Confirm all tests pass.
```

---

### Prompt D: Compliance Task Module (with Tests)

```text
Add the COMPLIANCE_TASKS table and implement endpoints for managing tasks.

Requirements:
1. Table columns:
   - compliance_task_id (PK)
   - description
   - deadline
   - recurrence
   - dependent_task_id (FK to self)
   - state (Open, Pending, Review Required, Completed, Overdue, etc.)
   - assignee_id (FK to USERS)
   - reviewer_id (FK to USERS, nullable)
   - approver_id (FK to USERS, nullable)
   - category (e.g., SEBI, RBI, IT/GST)
   - created_at
   - updated_at
2. Endpoints /api/tasks:
   - POST / (create a new task)
   - GET / (retrieve tasks, filter by status, category, or assignee)
   - PATCH /{task_id} (update state, or other fields)
   - For now, skip complex recurrence logic; just store the value.
   - Task dependency logic: if dependent_task_id is not complete, do not allow transition to “Completed.”
3. Test coverage:
   - Creating tasks works and sets default state to “Open.”
   - Retrieving tasks with filters.
   - State transitions obey dependency constraints.
   - Role-based checks: only certain roles can create tasks (e.g., "Compliance Officer" or "Fund Manager").

Step-by-step:
- Write tests for each scenario (create, fetch, update states, fail on dependency).
- Implement the model, migrations, and endpoints in your FastAPI app.
- Confirm all tests pass.
```

---

### Prompt E: Document Repository Module (with Tests)

```text
Now, introduce the DOCUMENTS and TASK_DOCUMENTS tables for file handling.

Requirements:
1. Add the new tables (DOCUMENTS, TASK_DOCUMENTS) via Alembic migrations.
2. Create endpoints on /api/documents:
   - POST /upload (upload a file, store file path, metadata)
   - GET / (list all documents with filters)
   - POST /{document_id}/link-to-task (associate a document with a compliance task)
3. For now, store uploaded files locally. (You will integrate cloud storage later.)
4. Write tests to ensure:
   - Document upload is restricted by role.
   - Document listings can be filtered by category, status, or name.
   - Linking a document to a task is successful and correctly appears in a query for that task.

Step-by-step:
- Write the test for uploading a file.
- Write the code to handle local file storage and metadata in the DB.
- Add linking logic and confirm test coverage.
```

---

### Prompt F: Audit Logging & Reporting (with Tests)

```text
Add the AUDIT_LOG table and at least one reporting feature.

Requirements:
1. Alembic migration for AUDIT_LOG:
   - log_id (PK)
   - user_id
   - activity
   - timestamp
   - details (nullable)
2. Whenever certain endpoints are called (task creation, document upload, or login), log an entry in AUDIT_LOG.
3. Add a minimal reporting endpoint (GET /api/reports/tasks-stats) that returns:
   - Number of tasks created
   - Number of tasks completed
   - Number of tasks overdue
4. Tests:
   - Confirm that each relevant endpoint triggers an audit log entry.
   - Check that the reporting endpoint returns the correct stats.

Step-by-step:
- Write tests that intercept calls to endpoints and ensure logs are created.
- Implement the logging logic, likely via a helper function invoked in each relevant route.
- Create the reporting endpoint and confirm test coverage.
```

---

### Prompt G: External Integrations (Slack/Email/Google Drive)

```text
Begin adding external integrations for file storage and notifications.

Requirements:
1. Google Drive integration:
   - Switch from local storage to uploading documents to Google Drive.
   - Save the Google Drive file ID or URL in the DOCUMENTS table.
2. Slack / Email notifications:
   - On task creation or state change, send a Slack message / email (configurable).
   - Use environment variables or a config file to store Slack webhooks, SMTP credentials, etc.
3. Tests:
   - Mock external services to avoid real API calls in CI.
   - Confirm that attempting to upload a document uses the Google Drive API methods.
   - Confirm that creating / updating tasks triggers a Slack or email notification function.

Step-by-step:
- Write tests with mocks for these external dependencies.
- Implement the integration logic behind feature flags or environment variables.
- Confirm test coverage for both success and failure cases.
```

---

### Prompt H: React Frontend Fundamentals (Routing, Login, MFA UX)

```text
Create the basic React framework for user login, including MFA flow.

Requirements:
1. Use React Router for basic navigation.
2. Create a “Login” page that:
   - Sends credentials to /api/auth/login
   - On success, if MFA is enabled, show an MFA code input.
   - On code submission, finalize login and store the JWT in local storage / Redux store.
3. Main layout after login:
   - Basic navigation with protected routes (redirect to login if not authenticated).
4. Tests (Jest + React Testing Library):
   - For the login form, ensure it calls the login endpoint.
   - For MFA steps, ensure correct flow if “mfa_enabled” is true.

Step-by-step:
- Write the test for the login form and MFA scenario.
- Implement the components, services (fetch API), and routing.
- Ensure that the tests pass by mocking the backend responses.
```

---

### Prompt I: React Task & Document Management UI

```text
Add front-end pages for compliance tasks and document repository.

Requirements:
1. Task list page:
   - Fetch tasks from /api/tasks
   - Display them in a table with state, deadline, assignee
   - Filter by category / state
2. Task detail page:
   - Show details for a single task
   - Allow state transitions (if permitted by the user’s role)
   - Show linked documents and a button to link more
3. Document management page:
   - Display all documents
   - Let users upload new documents
   - Option to link documents to tasks
4. Tests:
   - For the task list page, ensure tasks are fetched and displayed.
   - For the document upload, ensure the correct request is made to the backend.
   - For linking documents to tasks, ensure the UI triggers the correct endpoint.

Step-by-step:
- Write UI tests for each feature.
- Implement the components and service calls to the FastAPI endpoints.
- Confirm successful test runs and that the UI matches expected behavior.
```

---

### Prompt J: Continuous QA, Final Integration & Deployment

```text
Wrap everything together, ensuring final QA and deployment readiness.

Requirements:
1. Full end-to-end tests with a tool like Cypress or Playwright:
   - Simulate logging in, creating tasks, uploading documents, verifying Slack/Email notifications, etc.
2. Security checks:
   - Ensure HTTPS is used.
   - Double-check role-based restrictions on every route.
3. Performance checks:
   - Evaluate database indexing.
   - Confirm the architecture can scale if needed.
4. Deployment:
   - Provide a final Docker Compose or Kubernetes manifest.
   - Confirm all services (FastAPI + React + Postgres) run in the target environment.

Step-by-step:
- Write E2E tests that replicate real user flows.
- Address any discovered bugs and run final regression.
- Deploy to your chosen environment, verifying logs, memory usage, and stability.
```

---

By following these steps—and using the prompts above—you can maintain a disciplined, safe, and test-driven progression for your project, ensuring that each stage is robust before moving on to the next.