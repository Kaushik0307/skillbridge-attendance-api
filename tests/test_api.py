from tests.conftest import login


def test_student_signup_and_login(client):
    signup = client.post(
        "/auth/signup",
        json={
            "name": "Student B",
            "email": "studentb@test.com",
            "password": "Password123!",
            "role": "student",
            "institution_id": 1,
        },
    )
    assert signup.status_code == 200
    assert "access_token" in signup.json()

    login_resp = client.post("/auth/login", json={"email": "studentb@test.com", "password": "Password123!"})
    assert login_resp.status_code == 200
    assert "access_token" in login_resp.json()


def test_trainer_creates_session(client):
    token = login(client, "trainer@test.com")
    response = client.post(
        "/sessions",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "batch_id": 1,
            "title": "Python Basics",
            "date": "2026-04-20",
            "start_time": "10:00:00",
            "end_time": "12:00:00",
        },
    )
    assert response.status_code == 200
    assert "created successfully" in response.json()["message"]


def test_student_marks_own_attendance(client):
    token = login(client, "student@test.com")
    response = client.post(
        "/attendance/mark",
        headers={"Authorization": f"Bearer {token}"},
        json={"session_id": 1, "status": "present"},
    )
    assert response.status_code == 200
    assert response.json()["message"] == "Attendance marked successfully"


def test_monitoring_post_returns_405(client):
    response = client.post("/monitoring/attendance")
    assert response.status_code == 405


def test_protected_endpoint_without_token_returns_401(client):
    response = client.get("/programme/summary")
    assert response.status_code == 401


def test_monitoring_token_flow(client):
    base_token = login(client, "mo@test.com")
    monitoring_resp = client.post(
        "/auth/monitoring-token",
        headers={"Authorization": f"Bearer {base_token}"},
        json={"key": "test-monitoring-api-key"},
    )
    assert monitoring_resp.status_code == 200
    monitoring_token = monitoring_resp.json()["access_token"]

    attendance_resp = client.get(
        "/monitoring/attendance",
        headers={"Authorization": f"Bearer {monitoring_token}"},
    )
    assert attendance_resp.status_code == 200
