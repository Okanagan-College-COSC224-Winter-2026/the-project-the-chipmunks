import pytest

def login(client, email: str, password: str):
    resp = client.post(
        "/api/auth/login",
        json={"email": email, "password": password},
    )
    return resp

def get_feedback(client, assignment_id: int):
    return client.get(f"/api/student/assignments/{assignment_id}/feedback")

def test_get_feedback_unauthenticated(client):
    resp = get_feedback(client, assignment_id=1)
    assert resp.status_code == 401

def test_get_feedback_no_reviews(client, seeded_feedback_world):
    student = seeded_feedback_world["student_no_reviews"]
    assignment_id = seeded_feedback_world["assignment_id_no_reviews"]

    login_resp = login(client, student["email"], student["password"])
    assert login_resp.status_code in (200, 204)

    resp = get_feedback(client, assignment_id=assignment_id)
    assert resp.status_code == 200

    data = resp.get_json()
    assert data["total_reviews"] == 0
    assert data["criteria_feedback"] == []
    assert "overall_avg" in data

def test_get_feedback_wrong_course(client, seeded_feedback_world):
    student = seeded_feedback_world["student_wrong_course"]
    assignment_id = seeded_feedback_world["assignment_id_in_other_course"]

    login_resp = login(client, student["email"], student["password"])
    assert login_resp.status_code in (200, 204)

    resp = get_feedback(client, assignment_id=assignment_id)
    assert resp.status_code == 403

def test_get_feedback_success_and_anonymity(client, seeded_feedback_world):
    student = seeded_feedback_world["student_with_reviews"]
    assignment_id = seeded_feedback_world["assignment_id_with_reviews"]

    login_resp = login(client, student["email"], student["password"])
    assert login_resp.status_code in (200, 204)

    resp = get_feedback(client, assignment_id=assignment_id)
    assert resp.status_code == 200

    data = resp.get_json()

    assert isinstance(data["assignment_name"], str)
    assert isinstance(data["total_reviews"], int)
    assert isinstance(data["criteria_feedback"], list)
    assert isinstance(data["overall_avg"], (int, float))

    dumped = str(data).lower()
    assert "reviewer" not in dumped
    assert "reviewer_id" not in dumped
    assert "reviewerid" not in dumped
    assert "reviewed_by" not in dumped

    for item in data["criteria_feedback"]:
        assert "question" in item
        assert "avg_score" in item
        assert "max_score" in item
        assert "comments" in item
        assert isinstance(item["comments"], list)

def test_feedback_score_aggregation(client, seeded_feedback_world):
    student = seeded_feedback_world["student_with_reviews"]
    assignment_id = seeded_feedback_world["assignment_id_with_reviews"]

    login_resp = login(client, student["email"], student["password"])
    assert login_resp.status_code in (200, 204)

    resp = get_feedback(client, assignment_id=assignment_id)
    assert resp.status_code == 200
    data = resp.get_json()

    expected = seeded_feedback_world["expected_avgs_by_question"]
    got = {c["question"]: c["avg_score"] for c in data["criteria_feedback"]}

    for q, expected_avg in expected.items():
        assert q in got
        assert pytest.approx(got[q], rel=1e-3, abs=1e-3) == expected_avg
