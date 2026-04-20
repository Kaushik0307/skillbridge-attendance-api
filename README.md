# SkillBridge Attendance API

Backend API for a fictional state-level skilling programme attendance system built as a take-home assignment for the Python Developer Intern role.

## 1. Live API base URL and deployment notes

**Live base URL:** Add your deployed URL here after deploying to Render / Railway / Fly.io.

Example:
```bash
https://your-skillbridge-api.onrender.com
```

**Deployment note:** This repository is deployment-ready. The final step is to provision PostgreSQL (Neon recommended), set the environment variables on the hosting platform, run the seed script once, and update this README with the live base URL.

## 2. Local setup instructions

### Prerequisites
- Python 3.11+
- pip

### Clone and install
```bash
git clone <your-repo-url>
cd skillbridge_submission
python -m venv .venv
source .venv/bin/activate   # macOS/Linux
# .venv\Scripts\activate    # Windows
pip install -r requirements.txt
```

### Configure environment
```bash
cp .env.example .env
```

If you want a quick local run, you can keep SQLite by setting:
```env
DATABASE_URL=sqlite:///./skillbridge.db
```

If you want PostgreSQL locally or on Neon, use:
```env
DATABASE_URL=postgresql://username:password@host:5432/skillbridge
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
- Institution 1: `institution1@skillbridge.local`
- Institution 2: `institution2@skillbridge.local`
- Trainer 1: `trainer1@skillbridge.local`
- Trainer 2: `trainer2@skillbridge.local`
- Trainer 3: `trainer3@skillbridge.local`
- Trainer 4: `trainer4@skillbridge.local`
- Student 1: `student1@skillbridge.local`
- Programme Manager: `pm@skillbridge.local`
- Monitoring Officer: `monitor@skillbridge.local`

For submission, list at least one account per role in the final version of this README after seeding your production database.

## 4. Sample curl commands for every endpoint

Replace `BASE_URL` and tokens as needed.

```bash
BASE_URL=http://127.0.0.1:8000
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
    "email": "trainer1@skillbridge.local",
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
  -d '{"token": "<INVITE_TOKEN>"}'
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
    "email": "monitor@skillbridge.local",
    "password": "Password123!"
  }'
```

### Exchange Monitoring Officer standard JWT for scoped monitoring token
```bash
curl -X POST "$BASE_URL/auth/monitoring-token" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <MONITORING_STANDARD_JWT>" \
  -d '{"key": "replace-with-monitoring-api-key"}'
```

### Monitoring attendance (scoped token only)
```bash
curl "$BASE_URL/monitoring/attendance" \
  -H "Authorization: Bearer <MONITORING_SCOPED_JWT>"
```

### Live deployment login example
Replace the placeholder with the deployed URL once the app is live:
```bash
curl -X POST "https://your-skillbridge-api.onrender.com/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "trainer1@skillbridge.local",
    "password": "Password123!"
  }'
```

## 5. Schema decisions

### `batch_trainers`
This is modeled as a separate linking table because multiple trainers can be assigned to the same batch. It keeps batch ownership flexible and avoids denormalizing trainer IDs into the `batches` table.

### `batch_invites`
Invites are modeled separately to support trainer-generated enrollment flows with expiry, auditing (`created_by`), and one-time use via the `used` flag.

### `batch_students`
A join table cleanly represents student enrollment and supports authorization checks before attendance marking.

### Dual-token approach for Monitoring Officer
The Monitoring Officer first authenticates like every other user and receives a standard JWT. They must then exchange that token plus a server-side API key for a second short-lived monitoring token with `scope=monitoring_read`. The monitoring endpoint only accepts this scoped token. This gives the Monitoring Officer an extra layer of access control without complicating the standard login flow for other roles.

## 6. JWT payload structures

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
  "user_id": 9,
  "role": "monitoring_officer",
  "scope": "monitoring_read",
  "iat": 1713600000,
  "exp": 1713603600
}
```

## 7. Token rotation / revocation in a real deployment

In a real deployment, I would move from purely stateless JWTs to short-lived access tokens plus a refresh-token store, add a token identifier (`jti`) to every token, and keep a revocation table or Redis blacklist for compromised tokens. For the monitoring token specifically, I would rotate the API key using the hosting platform’s secret manager and expire all related tokens on rotation.

## 8. Validation, errors, and access control behavior

Implemented behaviors:
- All POST endpoints use Pydantic validation and return `422` on invalid payloads.
- Missing or invalid bearer tokens return `401`.
- Wrong role on protected routes returns `403`.
- Missing foreign-key targets like a bad `batch_id` or `session_id` return `404`.
- Student attendance marking for a session outside their enrollment returns `403`.
- `/monitoring/attendance` returns `405` for non-GET methods.

## 9. Tests included

The project includes pytest coverage for:
1. Successful student signup and login with JWT returned
2. Trainer creating a session with required fields
3. Student marking their own attendance
4. POST to `/monitoring/attendance` returning `405`
5. Protected endpoint with no token returning `401`
6. Monitoring Officer dual-token flow

At least two tests hit a real test database (`sqlite:///./test_skillbridge.db`) instead of mocking everything.

## 10. What is fully working, partially done, and skipped

### Fully working
- Role-based signup and login
- JWT-based protected routes
- Extra scoped monitoring token flow
- Batch creation, invite generation, batch join flow
- Session creation
- Attendance marking for enrolled students in active sessions
- Session attendance list
- Batch, institution, and programme summaries
- Seed script with meaningful sample data
- Pytest test suite

### Partially done
- Deployment is prepared but must be completed with your own hosting account and live environment variables.
- The README includes placeholder base URL text that should be replaced after deployment.

### Skipped
- Token revocation store / refresh-token flow
- Alembic migrations
- Rate limiting and audit logging
- Full production observability (structured logs, metrics, tracing)

## 11. One security issue in the current implementation and how I would fix it

Right now, standard JWTs remain valid until expiry even if a user’s access should be revoked immediately. With more time, I would add token identifiers, refresh tokens, and a server-side revocation / denylist mechanism backed by Redis or a database table.

## 12. One thing I would do differently with more time

I would add Alembic migrations and Dockerized local development with PostgreSQL so the local, test, and production environments match more closely and schema changes are versioned cleanly.

## 13. Suggested deployment steps for submission

### Render / Railway / Fly.io
1. Create a managed PostgreSQL instance (Neon is fine).
2. Set `DATABASE_URL`, `JWT_SECRET_KEY`, `MONITORING_TOKEN_SECRET_KEY`, `MONITORING_API_KEY`, and `SEED_DEFAULT_PASSWORD` in platform secrets.
3. Deploy the repo as a web service.
4. Start command:
```bash
uvicorn src.main:app --host 0.0.0.0 --port $PORT
```
5. Run seed once after deployment:
```bash
python -m src.seed
```
6. Update this README with the real base URL and final seeded role accounts.
