"""
Tests for assignments endpoints
"""

import json
import datetime


def test_teacher_can_create_assignment(test_client, make_admin):
    """
    GIVEN a teacher user
    WHEN they create a new assignment via POST /assignment
    THEN the assignment should be created successfully
    """
    make_admin(email="admin@example.com", password="admin", name="adminuser")

    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "admin@example.com", "password": "admin"}),
        headers={"Content-Type": "application/json"},
    )

    class_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "History 101"}),
        headers={"Content-Type": "application/json"},
    )

    class_id = class_response.json["class"]["id"]

    # Use a far-future date so this test stays valid over time
    future_due = datetime.datetime(2099, 12, 31, 23, 59, 59).isoformat()

    assignment_response = test_client.post(
        "/assignment/create_assignment",
        data=json.dumps(
            {
                "courseID": class_id,
                "name": "Essay 1",
                "rubric": "Quality of writing",
                "due_date": future_due,
            }
        ),
        headers={"Content-Type": "application/json"},
    )

    assert assignment_response.status_code == 201
    assert assignment_response.json["msg"] == "Assignment created"
    assert assignment_response.json["assignment"]["name"] == "Essay 1"
    assert assignment_response.json["assignment"]["rubric"] == "Quality of writing"
    assert assignment_response.json["assignment"]["due_date"] == "2099-12-31T23:59:59"


def test_create_assignment_missing_fields(test_client, make_admin):
    """
    GIVEN a teacher user
    WHEN they try to create an assignment with missing fields
    THEN the API should return a 400 error
    """
    make_admin(email="admin@example.com", password="admin", name="adminuser")

    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "admin@example.com", "password": "admin"}),
        headers={"Content-Type": "application/json"},
    )

    response = test_client.post(
        "/assignment/create_assignment",
        data=json.dumps({"name": "Essay 1", "rubric": "Quality of writing"}),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 400
    assert response.json["msg"] == "courseID and name are required"

    response = test_client.post(
        "/assignment/create_assignment",
        data=json.dumps({"courseID": 1, "rubric": "Quality of writing"}),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 400
    assert response.json["msg"] == "courseID and name are required"


def test_non_assigned_teacher_cannot_create_assignment(test_client, make_admin):
    """
    GIVEN a teacher user who is not assigned to the class
    WHEN they try to create an assignment for that class
    THEN the API should return a 403 error
    """
    make_admin(email="teacher@example.com", password="teacher", name="teacheruser")
    make_admin(email="otherteacher@example.com", password="otherteacher", name="otherteacheruser")

    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )

    class_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "Math 101"}),
        headers={"Content-Type": "application/json"},
    )
    class_id = class_response.json["class"]["id"]

    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "otherteacher@example.com", "password": "otherteacher"}),
        headers={"Content-Type": "application/json"},
    )

    response = test_client.post(
        "/assignment/create_assignment",
        data=json.dumps({"courseID": class_id, "name": "Homework 1", "rubric": "Accuracy"}),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 403
    assert response.json["msg"] == "Forbidden: you are not the teacher of this class"


def test_nonexistent_class_cannot_create_assignment(test_client, make_admin):
    """
    GIVEN a teacher user
    WHEN they try to create an assignment for a non-existent class
    THEN the API should return a 404 error
    """
    make_admin(email="teacher@example.com", password="teacher", name="teacheruser")

    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )

    response = test_client.post(
        "/assignment/create_assignment",
        data=json.dumps({"courseID": 999, "name": "Homework 1", "rubric": "Accuracy"}),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 404
    assert response.json["msg"] == "Class not found"


def test_unauthenticated_user_cannot_create_assignment(test_client):
    """
    GIVEN an unauthenticated user
    WHEN they try to create an assignment
    THEN the API should return a 401 error
    """
    response = test_client.post(
        "/assignment/create_assignment",
        data=json.dumps({"class_id": 1, "name": "Homework 1", "rubric": "Accuracy"}),
        headers={"Content-Type": "application/json"},
    )
    assert response.status_code == 401


def test_teacher_can_edit_assignment_before_due_date(test_client, make_admin):
    """
    GIVEN a teacher user
    WHEN they edit an assignment before its due date
    THEN the assignment should be updated successfully
    """
    make_admin(email="teacher@example.com", password="teacher", name="teacheruser")

    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )

    class_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "Science 101"}),
        headers={"Content-Type": "application/json"},
    )
    class_id = class_response.json["class"]["id"]

    # Use far-future dates so the test doesn't break in later years
    initial_due = datetime.datetime(2099, 12, 31, 23, 59, 59).isoformat()
    edited_due = datetime.datetime(2099, 11, 30, 23, 59, 59).isoformat()

    assignment_response = test_client.post(
        "/assignment/create_assignment",
        data=json.dumps(
            {
                "courseID": class_id,
                "name": "Lab Report 1",
                "rubric": "Completeness",
                "due_date": initial_due,
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    assignment_id = assignment_response.json["assignment"]["id"]

    edit_response = test_client.patch(
        f"/assignment/edit_assignment/{assignment_id}",
        data=json.dumps({"name": "Updated Lab Report 1", "rubric": "Thoroughness", "due_date": edited_due}),
        headers={"Content-Type": "application/json"},
    )
    assert edit_response.status_code == 200
    assert edit_response.json["msg"] == "Assignment updated"
    assert edit_response.json["assignment"]["name"] == "Updated Lab Report 1"
    assert edit_response.json["assignment"]["rubric"] == "Thoroughness"
    assert edit_response.json["assignment"]["due_date"] == "2099-11-30T23:59:59"


def test_teacher_can_edit_assignment_description_html(test_client, make_admin):
    """
    GIVEN a teacher user
    WHEN they edit an assignment to add description_html
    THEN the assignment should be updated with the HTML description
    """
    make_admin(email="teacher@example.com", password="teacher", name="teacheruser")

    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )

    class_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "English 101"}),
        headers={"Content-Type": "application/json"},
    )
    class_id = class_response.json["class"]["id"]

    future_due = datetime.datetime(2099, 12, 31, 23, 59, 59).isoformat()

    assignment_response = test_client.post(
        "/assignment/create_assignment",
        data=json.dumps(
            {
                "courseID": class_id,
                "name": "Essay 1",
                "rubric": "Quality",
                "due_date": future_due,
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    assignment_id = assignment_response.json["assignment"]["id"]

    edit_response = test_client.patch(
        f"/assignment/edit_assignment/{assignment_id}",
        data=json.dumps({"description_html": "<h1>Assignment Instructions</h1><p>Write an essay.</p>"}),
        headers={"Content-Type": "application/json"},
    )
    assert edit_response.status_code == 200
    assert edit_response.json["assignment"]["description_html"] == "<h1>Assignment Instructions</h1><p>Write an essay.</p>"


def test_teacher_cannot_edit_assignment_after_due_date(test_client, make_admin):
    """
    GIVEN a teacher user
    WHEN they try to edit an assignment after its due date
    THEN the API should return a 403 error
    """
    make_admin(email="teacher@example.com", password="teacher", name="teacheruser")

    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )

    class_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "Art 101"}),
        headers={"Content-Type": "application/json"},
    )
    class_id = class_response.json["class"]["id"]

    assignment_response = test_client.post(
        "/assignment/create_assignment",
        data=json.dumps(
            {
                "courseID": class_id,
                "name": "Painting 1",
                "rubric": "Creativity",
                "due_date": (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)).isoformat(),
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    assignment_id = assignment_response.json["assignment"]["id"]

    edit_response = test_client.patch(
        f"/assignment/edit_assignment/{assignment_id}",
        data=json.dumps({"name": "Updated Painting 1"}),
        headers={"Content-Type": "application/json"},
    )
    assert edit_response.status_code == 403
    assert edit_response.json["msg"] == "Cannot edit: assignment is past due date"


def test_non_assigned_teacher_cannot_edit_assignment(test_client, make_admin):
    """
    GIVEN a teacher user who is not assigned to the class
    WHEN they try to edit an assignment for that class
    THEN the API should return a 403 error
    """
    make_admin(email="teacher@example.com", password="teacher", name="teacheruser")
    make_admin(email="otherteacher@example.com", password="teacher", name="otherteacheruser")

    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "otherteacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )

    class_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "Music 101"}),
        headers={"Content-Type": "application/json"},
    )
    class_id = class_response.json["class"]["id"]

    assignment_response = test_client.post(
        "/assignment/create_assignment",
        data=json.dumps({"courseID": class_id, "name": "Composition 1", "rubric": "Originality"}),
        headers={"Content-Type": "application/json"},
    )
    assignment_id = assignment_response.json["assignment"]["id"]

    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )

    edit_response = test_client.patch(
        f"/assignment/edit_assignment/{assignment_id}",
        data=json.dumps({"name": "Updated Composition 1"}),
        headers={"Content-Type": "application/json"},
    )
    assert edit_response.status_code == 403
    assert edit_response.json["msg"] == "Forbidden: you are not the teacher of this class"


def test_delete_assignment(test_client, make_admin):
    """
    GIVEN a teacher user
    WHEN they delete an assignment
    THEN the assignment should be deleted successfully
    """
    make_admin(email="teacher@example.com", password="teacher", name="teacheruser")

    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )

    class_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "Physics 101"}),
        headers={"Content-Type": "application/json"},
    )
    class_id = class_response.json["class"]["id"]

    assignment_response = test_client.post(
        "/assignment/create_assignment",
        data=json.dumps(
            {
                "courseID": class_id,
                "name": "Homework 1",
                "rubric": "Correctness",
                "due_date": (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)).isoformat(),
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    assignment_id = assignment_response.json["assignment"]["id"]

    delete_response = test_client.delete(
        f"/assignment/delete_assignment/{assignment_id}",
        headers={"Content-Type": "application/json"},
    )
    assert delete_response.status_code == 200
    assert delete_response.json["msg"] == "Assignment deleted"


def test_delete_assignment_after_due_date(test_client, make_admin):
    """
    GIVEN a teacher user
    WHEN they try to delete an assignment after its due date
    THEN the API should return a 403 error
    """
    make_admin(email="teacher@example.com", password="teacher", name="teacheruser")

    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )

    class_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "Economics 101"}),
        headers={"Content-Type": "application/json"},
    )
    class_id = class_response.json["class"]["id"]

    assignment_response = test_client.post(
        "/assignment/create_assignment",
        data=json.dumps(
            {
                "courseID": class_id,
                "name": "Market Analysis",
                "rubric": "Data Interpretation",
                "due_date": (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)).isoformat(),
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    assignment_id = assignment_response.json["assignment"]["id"]

    delete_response = test_client.delete(
        f"/assignment/delete_assignment/{assignment_id}",
        headers={"Content-Type": "application/json"},
    )
    assert delete_response.status_code == 403
    assert delete_response.json["msg"] == "Cannot delete: assignment is past due date"


def test_non_assigned_teacher_cannot_delete_assignment(test_client, make_admin):
    """
    GIVEN a teacher user who is not assigned to the class
    WHEN they try to delete an assignment for that class
    THEN the API should return a 403 error
    """
    make_admin(email="teacher@example.com", password="teacher", name="teacheruser")
    make_admin(email="otherteacher@example.com", password="teacher", name="otherteacheruser")

    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "otherteacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )

    class_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "Geography 101"}),
        headers={"Content-Type": "application/json"},
    )
    class_id = class_response.json["class"]["id"]

    assignment_response = test_client.post(
        "/assignment/create_assignment",
        data=json.dumps(
            {
                "courseID": class_id,
                "name": "Geography Assignment",
                "rubric": "Map Skills",
                "due_date": (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=7)).isoformat(),
            }
        ),
        headers={"Content-Type": "application/json"},
    )
    assignment_id = assignment_response.json["assignment"]["id"]

    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )

    delete_response = test_client.delete(
        f"/assignment/delete_assignment/{assignment_id}",
        headers={"Content-Type": "application/json"},
    )
    assert delete_response.status_code == 403
    assert delete_response.json["msg"] == "Forbidden: you are not the teacher of this class"


def test_unauthenticated_user_cannot_delete_assignment(test_client):
    """
    GIVEN an unauthenticated user
    WHEN they try to delete an assignment
    THEN the API should return a 401 error
    """
    delete_response = test_client.delete(
        "/assignment/delete_assignment/1",
        headers={"Content-Type": "application/json"},
    )
    assert delete_response.status_code == 401


def test_delete_nonexistent_assignment(test_client, make_admin):
    """
    GIVEN a teacher user
    WHEN they try to delete a non-existent assignment
    THEN the API should return a 404 error
    """
    make_admin(email="teacher@example.com", password="teacher", name="teacheruser")

    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )

    delete_response = test_client.delete(
        "/assignment/delete_assignment/999",
        headers={"Content-Type": "application/json"},
    )
    assert delete_response.status_code == 404
    assert delete_response.json["msg"] == "Assignment not found"


def test_get_assignments_by_class_id(test_client, make_admin):
    """
    GIVEN a teacher user
    WHEN they request assignments for a specific class
    THEN the API should return the list of assignments for that class
    """
    make_admin(email="teacher@example.com", password="teacher", name="teacheruser")

    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )

    class_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "Literature 101"}),
        headers={"Content-Type": "application/json"},
    )
    class_id = class_response.json["class"]["id"]

    assignment_names = ["Poetry Analysis", "Novel Review", "Drama Essay"]
    for name in assignment_names:
        test_client.post(
            "/assignment/create_assignment",
            data=json.dumps(
                {
                    "courseID": class_id,
                    "name": name,
                    "rubric": "Content Quality",
                    "due_date": (datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=10)).isoformat(),
                }
            ),
            headers={"Content-Type": "application/json"},
        )

    assignments = test_client.get(f"/assignment/{class_id}")
    assert assignments.status_code == 200
    assert len(assignments.json) == 3

    returned_names = [assignment["name"] for assignment in assignments.json]
    for name in assignment_names:
        assert name in returned_names


def test_get_assignments_by_class_id_no_assignments(test_client, make_admin):
    """
    GIVEN a teacher user
    WHEN they request assignments for a class with no assignments
    THEN the API should return an empty list
    """
    make_admin(email="teacher@example.com", password="teacher", name="teacheruser")

    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )

    class_response = test_client.post(
        "/class/create_class",
        data=json.dumps({"name": "Philosophy 102"}),
        headers={"Content-Type": "application/json"},
    )
    class_id = class_response.json["class"]["id"]

    assignments = test_client.get(f"/assignment/{class_id}")
    assert assignments.status_code == 200
    assert len(assignments.json) == 0


def test_get_assignments_by_class_id_nonexistent_class(test_client, make_admin):
    """
    GIVEN a teacher user
    WHEN they request assignments for a non-existent class
    THEN the API should return a 404 error
    """
    make_admin(email="teacher@example.com", password="teacher", name="teacheruser")

    test_client.post(
        "/auth/login",
        data=json.dumps({"email": "teacher@example.com", "password": "teacher"}),
        headers={"Content-Type": "application/json"},
    )

    assignments = test_client.get("/assignment/999")
    assert assignments.status_code == 404
    assert assignments.json["msg"] == "Class not found"


def test_unauthenticated_user_cannot_get_assignments(test_client):
    """
    GIVEN an unauthenticated user
    WHEN they try to get assignments for a class
    THEN the API should return a 401 error
    """
    assignments = test_client.get("/assignment/1")
    assert assignments.status_code == 401
