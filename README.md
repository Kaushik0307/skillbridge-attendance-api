# SkillBridge Attendance API

Backend API for a fictional state-level skilling programme attendance system built as a take-home assignment for the Python Developer Intern role.

## 1. Live API base URL and deployment notes

**Live API base URL:**  
`https://skillbridge-attendance-api-omkar.onrender.com`

**Swagger / OpenAPI docs:**  
`https://skillbridge-attendance-api-omkar.onrender.com/docs`

### Deployment notes
- API is deployed on **Render**
- Database is hosted on **Neon PostgreSQL**
- Environment variables are managed through platform secrets/config
- The root Render URL may briefly show a wake-up/loading screen on first open because the service is on a free tier and may need a few seconds to start
- The live API was verified through both:
  - the public Swagger docs page at `/docs`
  - direct terminal/curl style requests against the deployed URL

For the Monitoring Officer flow, the reviewer should:
1. log in using `/auth/login`
2. use the standard token to call `/auth/monitoring-token`
3. replace the token in Swagger **Authorize** with the returned scoped monitoring token
4. call `/monitoring/attendance`

## 2. Local setup instructions

### Prerequisites
- Python 3.11+
- pip

### Clone and install
```bash
git clone https://github.com/Kaushik0307/skillbridge-attendance-api.git
cd skillbridge-attendance-api
python -m venv .venv
source .venv/bin/activate   # macOS/Linux
# .venv\Scripts\activate    # Windows PowerShell
pip install -r requirements.txt
```

### Configure environment
Create a `.env` file from `.env.example`.

macOS/Linux:
```bash
cp .env.example .env
```

Windows PowerShell:
```powershell
Copy-Item .env.example .env
```

### Example local `.env` for SQLite
If you want a quick local run with SQLite:
```env
DATABASE_URL=sqlite:///./skillbridge.db
JWT_SECRET_KEY=change-this-to-a-long-random-secret
MONITORING_TOKEN_SECRET_KEY=change-this-too
MONITORING_API_KEY=my-monitoring-api-key
ACCESS_TOKEN_EXPIRE_MINUTES=1440
MONITORING_TOKEN_EXPIRE_MINUTES=60
SEED_DEFAULT_PASSWORD=Password123!
```

### Example local `.env` for PostgreSQL / Neon
If you want PostgreSQL locally or Neon:
```env
DATABASE_URL=postgresql+psycopg://username:password@host:5432/skillbridge
JWT_SECRET_KEY=change-this-to-a-long-random-secret
MONITORING_TOKEN_SECRET_KEY=change-this-too
MONITORING_API_KEY=my-monitoring-api-key
ACCESS_TOKEN_EXPIRE_MINUTES=1440
MONITORING_TOKEN_EXPIRE_MINUTES=60
SEED_DEFAULT_PASSWORD=Password123!
```

### Run the API
```bash
uvicorn src.main:app --reload
```

### Seed the database
```bash
python -m src.seed
```

### Run tests
```bash
pytest -q
```

## 3. Test accounts for all five roles

These accounts are created by the seed script. The default password is controlled by `SEED_DEFAULT_PASSWORD` and defaults to:

```text
Password123!
```

### Seeded accounts
- Institution 1: `institution1@skillbridgeapp.com`
- Institution 2: `institution2@skillbridgeapp.com`
- Trainer 1: `trainer1@skillbridgeapp.com`
- Trainer 2: `trainer2@skillbridgeapp.com`
- Trainer 3: `trainer3@skillbridgeapp.com`
- Trainer 4: `trainer4@skillbridgeapp.com`
- Student 1: `student1@skillbridgeapp.com`
- Programme Manager: `pm@skillbridgeapp.com`
- Monitoring Officer: `monitor@skillbridgeapp.com`

### Reviewer quick-start accounts
Use at least one account per role for verification:
- Institution: `institution1@skillbridgeapp.com / Password123!`
- Trainer: `trainer1@skillbridgeapp.com / Password123!`
- Student: `student1@skillbridgeapp.com / Password123!`
- Programme Manager: `pm@skillbridgeapp.com / Password123!`
- Monitoring Officer: `monitor@skillbridgeapp.com / Password123!`

## 4. How to verify the live build

The deployed API was verified successfully against the live Render URL.

### Recommended quick verification path
1. Open the docs page:  
   `https://skillbridge-attendance-api-omkar.onrender.com/docs`
2. Log in with one of the seeded accounts above
3. Copy the returned JWT
4. Click **Authorize** and paste the token
5. Test one protected endpoint for that role
6. For Monitoring Officer:
   - log in as `monitor@skillbridgeapp.com`
   - authorize with the standard login token
   - call `/auth/monitoring-token`
   - copy the returned scoped token
   - re-authorize with the scoped token
   - call `/monitoring/attendance`

### Live flows verified successfully
- login for Institution, Trainer, Student, Programme Manager, and Monitoring Officer
- Monitoring Officer standard token generation
- Monitoring Officer scoped token generation through `/auth/monitoring-token`
- `GET /monitoring/attendance` with the scoped token
- `POST /monitoring/attendance` returning `405 Method Not Allowed`
- `GET /batches/{id}/summary`
- `GET /institutions/{id}/summary`
- `GET /programme/summary`
- trainer creating a session
- student marking attendance

Protected endpoint verification was done successfully against the live deployment through both Swagger `/docs` and direct terminal/curl requests.

## 5. Sample curl commands for every endpoint

Replace `BASE_URL` and tokens as needed.

### Live example
```bash
BASE_URL=https://skillbridge-attendance-api-omkar.onrender.com
```

### Signup
```bash
curl -X POST "$BASE_URL/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Student New",
    "email": "student.new@example.com",
    "password": "Password123!",
    "role": "student",
    "institution_id": 1
  }'
```

### Login
```bash
curl -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "trainer1@skillbridgeapp.com",
    "password": "Password123!"
  }'
```

### Create batch (Trainer / Institution)
```bash
curl -X POST "$BASE_URL/batches" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <STANDARD_JWT>" \
  -d '{
    "name": "Batch Delta",
    "institution_id": 1,
    "trainer_ids": [3]
  }'
```

### Generate batch invite (Trainer)
```bash
curl -X POST "$BASE_URL/batches/1/invite" \
  -H "Authorization: Bearer <TRAINER_JWT>"
```

### Join batch (Student)
```bash
curl -X POST "$BASE_URL/batches/join" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <STUDENT_JWT>" \
  -d '{
    "token": "<INVITE_TOKEN>"
  }'
```

### Create session (Trainer)
```bash
curl -X POST "$BASE_URL/sessions" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <TRAINER_JWT>" \
  -d '{
    "batch_id": 1,
    "title": "FastAPI Basics",
    "date": "2026-04-20",
    "start_time": "10:00:00",
    "end_time": "12:00:00"
  }'
```

### Mark attendance (Student)
```bash
curl -X POST "$BASE_URL/attendance/mark" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <STUDENT_JWT>" \
  -d '{
    "session_id": 1,
    "status": "present"
  }'
```

### Session attendance list (Trainer)
```bash
curl "$BASE_URL/sessions/1/attendance" \
  -H "Authorization: Bearer <TRAINER_JWT>"
```

### Batch summary (Institution)
```bash
curl "$BASE_URL/batches/1/summary" \
  -H "Authorization: Bearer <INSTITUTION_JWT>"
```

### Institution summary (Programme Manager)
```bash
curl "$BASE_URL/institutions/1/summary" \
  -H "Authorization: Bearer <PROGRAMME_MANAGER_JWT>"
```

### Programme summary (Programme Manager)
```bash
curl "$BASE_URL/programme/summary" \
  -H "Authorization: Bearer <PROGRAMME_MANAGER_JWT>"
```

### Monitoring Officer standard login token
```bash
curl -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "monitor@skillbridgeapp.com",
    "password": "Password123!"
  }'
```

### Exchange Monitoring Officer standard JWT for scoped monitoring token
```bash
curl -X POST "$BASE_URL/auth/monitoring-token" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <MONITORING_STANDARD_JWT>" \
  -d '{
    "key": "my-monitoring-api-key"
  }'
```

### Monitoring attendance (scoped token only)
```bash
curl "$BASE_URL/monitoring/attendance" \
  -H "Authorization: Bearer <MONITORING_SCOPED_JWT>"
```

### Confirm 405 for non-GET monitoring requests
```bash
curl -X POST "$BASE_URL/monitoring/attendance"
```

## 6. Schema decisions

### `batch_trainers`
This is modeled as a separate linking table because multiple trainers can be assigned to the same batch. It keeps batch ownership flexible and avoids denormalizing trainer IDs into the `batches` table.

### `batch_invites`
Invites are modeled separately to support trainer-generated enrollment flows with expiry, auditing through `created_by`, and one-time use via the `used` flag.

### `batch_students`
A join table cleanly represents student enrollment and supports authorization checks before attendance marking.

### `attendance`
Attendance is separated from `sessions` and `batch_students` so marking and updating attendance stays explicit per student-session pair. This also keeps summaries easier to compute and audit.

### Dual-token approach for Monitoring Officer
The Monitoring Officer first authenticates like every other user and receives a standard JWT. They must then exchange that token plus a server-side API key for a second short-lived monitoring token with `scope=monitoring_read`. The monitoring endpoint only accepts this scoped token. This gives the Monitoring Officer an extra layer of access control without complicating the standard login flow for other roles.

## 7. JWT payload structures

### Standard login token
```json
{
  "user_id": 7,
  "role": "trainer",
  "iat": 1713600000,
  "exp": 1713686400
}
```

### Monitoring scoped token
```json
{
  "user_id": 23,
  "role": "monitoring_officer",
  "scope": "monitoring_read",
  "iat": 1713600000,
  "exp": 1713603600
}
```

## 8. Token rotation / revocation in a real deployment

In a real deployment, I would move from purely stateless JWTs to short-lived access tokens plus a refresh-token store, add a token identifier (`jti`) to every token, and keep a revocation table or Redis blacklist for compromised tokens. For the monitoring token specifically, I would rotate the API key using the hosting platform’s secret manager and expire all related monitoring tokens whenever the API key changes.

## 9. Validation, errors, and access control behavior

Implemented behaviors:
- All POST endpoints use Pydantic validation and return `422` on invalid payloads
- Missing or invalid bearer tokens return `401`
- Wrong role on protected routes returns `403`
- Missing foreign-key targets like a bad `batch_id` or `session_id` return `404`
- Student attendance marking for a session outside their enrollment returns `403`
- Student attendance marking for a non-active session returns `403`
- `/monitoring/attendance` returns `405` for any non-GET request
- Standard login token is not accepted for `/monitoring/attendance`; only the scoped monitoring token works there

## 10. Tests included

The project includes pytest coverage for:
1. Successful student signup and login with JWT returned
2. Trainer creating a session with required fields
3. Student marking their own attendance
4. POST to `/monitoring/attendance` returning `405`
5. Protected endpoint with no token returning `401`
6. Monitoring Officer dual-token flow

At least two tests hit a real test database (`sqlite:///./test_skillbridge.db`) instead of mocking everything.

## 11. What is fully working, what is partially done, and what was skipped

### Fully working
- Role-based signup and login
- JWT-based protected routes
- Extra scoped monitoring token flow for Monitoring Officer
- Batch creation
- Batch invite generation
- Student join-by-invite flow
- Session creation
- Attendance marking for enrolled students in active sessions
- Session attendance list
- Batch, institution, and programme summaries
- Seed script with meaningful sample data
- Pytest suite with real test database usage
- Public deployment on Render backed by Neon PostgreSQL
- Live verification through both `/docs` and terminal/curl style requests

### Partially done
- Swagger now supports Bearer auth through the `Authorize` flow, but the Monitoring Officer flow is still inherently a two-step manual process because the user must replace the standard token with the scoped monitoring token before calling `/monitoring/attendance`
- This is a prototype implementation focused on the assignment scope, not a production-grade system

### Skipped
- Token revocation store / refresh-token flow
- Alembic migrations
- Rate limiting and audit logging
- Full production observability such as structured logs, metrics, tracing, and alerts
- Frontend UI, since the assignment explicitly focused on a backend API rather than a full product UI

## 12. One security issue in the current implementation and how I would fix it

Right now, standard JWTs remain valid until expiry even if a user’s access should be revoked immediately. With more time, I would add token identifiers, refresh tokens, and a server-side revocation / denylist mechanism backed by Redis or a database table.

## 13. One thing I would do differently with more time

I would add Alembic migrations and Dockerized local development with PostgreSQL so the local, test, and production environments match more closely and schema changes are versioned cleanly.

## 14. Deployment summary

### Render / Neon setup used
1. Managed PostgreSQL instance created on Neon
2. Render web service configured with environment variables
3. Python version pinned to 3.11.9 using `.python-version`
4. Service deployed with:
```bash
uvicorn src.main:app --host 0.0.0.0 --port $PORT
```
5. Production database seeded using:
```bash
python -m src.seed
```

### Required environment variables
```env
DATABASE_URL=postgresql+psycopg://...
JWT_SECRET_KEY=...
MONITORING_TOKEN_SECRET_KEY=...
MONITORING_API_KEY=my-monitoring-api-key
ACCESS_TOKEN_EXPIRE_MINUTES=1440
MONITORING_TOKEN_EXPIRE_MINUTES=60
SEED_DEFAULT_PASSWORD=Password123!
```