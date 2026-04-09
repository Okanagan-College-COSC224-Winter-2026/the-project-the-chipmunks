# API Endpoint Summary

This document summarizes all API endpoints documented across the user stories and indicates which endpoints are implemented vs. proposed.

## Implemented Endpoints

### Authentication (UC28, UC29)

| Endpoint | Method | Use Case | Status | Description |
|----------|--------|----------|--------|-------------|
| `/auth/login` | POST | UC28 | ✅ Implemented | User login, returns JWT token |
| `/auth/register` | POST | UC29 | ✅ Implemented | Create new user account |
| `/auth/logout` | POST | N/A | ✅ Implemented | Logout (JWT cleanup) |

### User Management (UC30)

| Endpoint | Method | Use Case | Status | Description |
|----------|--------|----------|--------|-------------|
| `/user/` | GET | UC30 | ✅ Implemented | Get current authenticated user info |
| `/user/` | PUT | N/A | ✅ Implemented | Update current user information |
| `/user/<id>` | GET | N/A | ✅ Implemented | Get user by ID (self or admin) |
| `/user/<id>` | DELETE | N/A | ✅ Implemented | Delete user (self or admin) |
| `/user/password` | PATCH | N/A | ✅ Implemented | Changes the current user's password |

## Authentication Requirements

All protected endpoints require:

- **HTTPOnly Cookie**: JWT token is automatically included by the browser
- **Credentials**: All fetch requests must include `credentials: 'include'`
- **Admin endpoints**: User must have `role = 'admin'`

Obtain JWT token via `POST /auth/login` with valid credentials. The token is automatically stored in an HTTPOnly cookie.

# API Endpoint Summary (generated)

This summary is generated from `docs/dev-guidelines/endpoints.json` (generatedAt: 2025-10-24). It reflects the backend routes currently implemented under `backend/src/routes`.

- Source of truth for shapes and notes: `endpoints.json`
- Most endpoints are protected and require an Authorization header

## Authentication and access

- **Protected routes**: Require HTTPOnly cookie with JWT token (automatically sent by browser when `credentials: 'include'` is specified)
- **Login**: Call `POST /auth/login` with JSON body `{ email, password }` to obtain user info and set HTTPOnly cookie
- **Public routes**: `GET /ping`, `POST /auth/register`, `POST /auth/login`
- **Legacy note**: Old documentation may reference `Authorization: Bearer <token>` headers - these are no longer used

---

## Public endpoints

| Method | Path   | Headers                                   | Response                        | Notes |
|--------|--------|-------------------------------------------|----------------------------------|-------|
| POST   | `/auth/login` | `Content-Type: application/json` | `200 { role, user_id, name, msg }` or `400/401` | Sets HTTPOnly cookie with JWT token. Frontend must use `credentials: 'include'`. |
| POST   | `/auth/register` | `Content-Type: application/json` | `201 { msg, user: {...} }` or `400` | Creates student account. Body: `{ name, email, password }`. |
| GET    | `/ping` | —                                         | `{ message: 'pong!' }`          | Lightweight healthcheck. |

---

## Protected endpoints

All endpoints in this section require the HTTPOnly JWT cookie. Frontend requests must include `credentials: 'include'`.

| Method | Path | Params | Query | Body | Response | Status | Notes |
|--------|------|--------|-------|------|----------|--------|-------|
| GET | `/assignment/:class_id` | `{ class_id: number }` | — | — | `Array<Assignment>` | ✅Implemented |Returns all assignments for a course. |
| POST | `/class/members` | — | — | `{ id: number }` | `Array<User { id, name, email }>` | ✅Implemented | Uses `User_Course` to look up members. |
| GET | `/class/classes` | — | — | — | `Array<Course>` | ✅Implemented | Currently returns classes for student / Instructor |
| GET | `/student/grades` | — | — | — | `{ student_id: number, courses: Array<CourseGrade> }` | ✅Implemented | Returns per-course grade averages for the authenticated student. |
| GET | `/class/browse_classes` | — | — | — | `Array<Course>` | ✅Implemented | Returns all classes |
| POST | `/assignment/create_assignment` | — | — | `{ courseID: number, name: string, rubric: string, due_date?: string }` | `{ msg: string, assignment: Assignment }` | ✅Implemented | Creates assignment and returns created id. |
| PATCH | `/assignment/edit_assignment/:assignment_id` | `{ assignment_id: string }` | — | `{ name: string, rubric: string, due_date: string }` | `{ msg: string, assignment: Assignment }` | ✅Implemented | Edits assignment and returns updated assignment |
| DELETE | `/assignment/delete_assignment/:assignment_id` | `{ assignment_id: string }` | — | — | `{ msg: string}` | ✅Implemented | Deletes assignment and returns message |
| POST | `/class/create_class` | — | — | `{ name: string }` | `201 { message: 'Class created', id }` or `400 { message: 'Class already exists' }` | ✅Implemented | Creates a class for the given teacher |
| POST | `/rubric/create_criteria` | — | — | `{ id: number, rubricID: number, question: string, scoreMax: number, hasScore: boolean }` | `{ message: string, id: number }` | Not Implemented: TODO | Creates a `Criteria_Description` row. Field `id` is taken from body. |
| POST | `/criterion/create_criterion` | — | — | `{ reviewID: number, criterionRowID: number, grade: number, comments: string }` | `{ message: string, id: number }` | Not Implemented: TODO | Creates one `Criterion` (row within a Review). |
| POST | `/group/create_group` | — | — | `{ id: number, name: string, assignmentID: number }` | `{ message: string, id: number }` | Not Implemented: TODO | Creates `CourseGroup`; route swallows DB errors and logs them. |
| POST | `/review/create_review` | — | — | `{ assignmentID: number, reviewerID: number, revieweeID: number }` | `{ message: string, id: number }` | Not Implemented: TODO | Links reviewer and reviewee for an assignment. |
| POST | `/rubric/create_rubric` | — | — | `{ id: number, assignmentID: number, canComment: boolean }` | `{ message: string, id: number }` | Not Implemented: TODO | Destroys existing rubric with same id before creating new one. |
| GET | `/rubric/criteria` | — | `{ rubricID: string }` | — | `400 if missing` or `Array<Criteria_Description>` | Not Implemented: TODO | Query param parsed with `parseInt` before DB lookup. |
| POST | `/group/delete_group` | — | — | `{ groupID: number }` | `{ message: string, id: number, groupMembers: update result }` | Not Implemented: TODO | Sets members' `groupID` to `-1` then destroys the `CourseGroup`. |
| GET | `/class/get_className/:classID` | `{ classID: number }` | — | — | `404 if not found; else { className: string }` | Not Implemented: TODO | Finds Course by id and returns its name. |
| GET | `/review/` | — | `{ assignmentID: string, reviewerID: string, revieweeID: string }` | — | `400/404` or `{ grades: number[] }` | Not Implemented: TODO | Aggregates grade fields from `Criterion` rows. |
| GET | `/rubric/` | — | `{ rubricID: string }` | — | `400/404` or `{ id, assignmentID, canComment }` | Not Implemented: TODO | Returns a simplified rubric object. |
| GET | `/group/list_all_groups/:assignmentID` | `{ assignmentID: number }` | — | — | `Array<CourseGroup>` | Not Implemented: TODO | Finds all `CourseGroup` rows where `assignmentID` matches. |
| GET | `/group/list_group_members/:assignmentID/:groupID` | `{ assignmentID: number, groupID: string }` | — | — | `Array<Group_Member>` | Not Implemented: TODO | `groupID` treated as string in route typing. |
| GET | `/group/list_stu_groups/:assignmentID/:studentID` | `{ assignmentID: number, studentID: number }` | — | — | `300 { msg: 'student has no group' }` or `Array<Group_Member>` | Not Implemented: TODO | Returns peers in the student's group. |
| GET | `/group/list_ua_groups/:assignmentID` | `{ assignmentID: number }` | — | — | `Array<Group_Member>` | Not Implemented: TODO | Unassigned students for an assignment (`groupID === -1`). |
| GET | `/group/next_groupid` | — | — | — | `number` | Not Implemented: TODO | Count of groups with `id > 0` (Sequelize `count` with `Op.gt`). |
| POST | `/group/save_groups` | — | — | `{ groupID: number, userID: number, assignmentID: number }` | `{ message: 'successful DB post!' }` or `401` | Not Implemented: TODO | Updates `Group_Member` rows to set `groupID` for a user in an assignment. |
| POST | `/class/enroll_students` | — | — | `{ class_id: number, students: string (CSV) }` | `{ msg: string }` | ✅Implemented | Enrolls specified students on the csv to the course, if student doesn't exist it creates it. TODO: change the default password to random and email it to the user. |
| GET | `/user/user_id` | — | — | — | `number` | Not Implemented: TODO | Reads `app.session[token].id`. Handler assumes session contains token; no explicit 401 check. |

---

### CLI Commands

| Command | Description |
|---------|-------------|
| `flask add_sample_reviews` | Seeds peer review data (reviewers, rubrics, criteria, scores) for testing the student grade display. Requires `flask add_users` and `flask add_sample_courses` first. |

---
### Peer Review Submission (US1/US11)

| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| POST | `/api/reviews/submit` | JWT (student) | Submit a rubric-based peer review. Body: `{ assignment_id: int, reviewee_id: int, criteria: [{ criteria_description_id: int, grade: int, comments: str }] }`. Validates against self-reviews, duplicates, and group membership. Returns `201 { review_id }`. |
| GET | `/assignment/<assignment_id>/rubric` | JWT | Returns the rubric and its criteria for a given assignment. Response: `{ rubric_id: int, assignment_id: int, criteria: [{ id, question, score_max, has_score, can_comment }] }`. |

### Student Feedback (US12)

| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| GET | `/student/assignments/<assignment_id>/feedback` | JWT (student) | Returns aggregated anonymous peer feedback for the logged-in student for a given assignment. Includes per-criterion average scores and anonymous comments. Response: `{ assignment_id, student_id, total_reviews_received, criteria: [{ criterion_id, criterion_name, average_score, score_max, review_count, comments }] }`. |

### Notes

- Parameter types in curly braces are the expected types; some routes accept strings for numeric IDs and cast internally.
- For stability, prefer sending numeric IDs as numbers where indicated.
- If any discrepancy arises between this document and `endpoints.json`, treat `endpoints.json` as canonical.
- `CourseGrade` response shape used by `/student/grades`:
  `{ course_id, course_name, grade, max_score, graded_assignments, total_assignments, has_grades }`

## Peer Review Submission (US1/US11)

### POST /api/reviews/submit

**Description:** Submit a peer review with rubric scores and optional comments.

**Auth:** `@jwt_required()` — reviewer identified via `get_jwt_identity()`

**Request Body:**
```json
{
  "assignment_id": 1,
  "reviewee_id": 2,
  "criteria": [
    {
      "criteria_description_id": 1,
      "grade": 4,
      "comments": "Good work"
    }
  ]
```

**Responses:**
- `201` — Review created successfully, returns `{ "review_id": int }`
- `400` — Reviewer == reviewee (self-review blocked)
- `401` — Not authenticated
- `409` — Duplicate review (same reviewer + reviewee + assignment)

---

### GET /api/assignments/<assignment_id>/rubric

**Description:** Get the rubric and criteria for an assignment.

**Auth:** `@jwt_required()`

**Response (200):**
```json
{
  "rubric_id": 1,
  "assignment_id": 1,
  "criteria": [
    {
      "id": 1,
      "question": "Communication",
      "score_max": 5,
      "has_score": true,
      "can_comment": true
    }
  ]
}
```

**Responses:**
- `200` — Rubric found
- `401` — Not authenticated
- `404` — Assignment or rubric not found

---

## Student Feedback Viewing (US12)

### GET /student/assignments/<assignment_id>/feedback

**Description:** Get aggregated anonymous peer review feedback for the logged-in student on a specific assignment.

**Auth:** `@jwt_required()` — student identified via `get_jwt_identity()`

**Response (200 — with reviews):**
```json
{
  "assignment_name": "Peer Review Assignment 1",
  "total_reviews": 2,
  "criteria_feedback": [
    {
      "question": "Communication",
      "avg_score": 4.5,
      "max_score": 5,
      "comments": ["Good communicator", "Excellent communication"]
    }
  ],
  "overall_avg": 4.0
}
```

**Response (200 — no reviews yet):**
```json
{
  "assignment_name": "Peer Review Assignment 1",
  "total_reviews": 0,
  "criteria_feedback": [],
  "overall_avg": 0.0
}
```

**Responses:**
- `200` — Feedback returned (may be empty)
- `401` — Not authenticated
- `404` — Assignment not found

**Privacy:** Reviewer identities are never included in the response.

### Feature B: File Attachments on Reviews & Conclusions

| Endpoint | Method | Auth | Description |
|----------|--------|------|-------------|
| /review/<id>/upload | POST | Student | Upload files with peer review submission |
| /review/<id>/files | GET | Any | List files attached to a review |
| /review/file/<file_id> | GET | Any | Download a review file |
| /assignment/<id>/conclusion/upload | POST | Teacher | Upload conclusion file |
| /assignment/<id>/conclusion/files | GET | Any | List conclusion files for assignment |
---

## Assignment File Attachment Endpoints

### POST /assignment/<id>/upload
**Description:** Upload a PDF attachment to an assignment.  
**Authentication:** @jwt_required() – Teacher only  
**Request Type:** multipart/form-data  
**File Field:** file  

**Validation:**
- File must be PDF
- Maximum size: 10MB

**Response (200 OK):**
```json
{
  "message": "File uploaded successfully",
  "filename": "assignment_spec.pdf",
  "size": "2.4MB"
}

---

## Admin User Management (US26)

| Method | URL | Auth | Description |
|--------|-----|------|-------------|
| GET | `/admin/users` | JWT (admin) | Paginated list of all users. Query params: `page` (default 1), `role` (filter by role), `search` (name/email substring). Returns `{ users, page, per_page, total, pages }`. |
| POST | `/admin/users/create` | JWT (admin) | Create a new user. Body: `{ name, email, password, role, must_change_password? }`. Returns `201 { msg, user }` or `409` on duplicate email. |
| PUT | `/admin/users/<id>` | JWT (admin) | Update user name, email, or role. Returns `200 { msg, user }` or `404`. Admins cannot demote themselves. |
| PATCH | `/admin/users/<id>/deactivate` | JWT (admin) | Soft-deactivate a user (sets `is_active = false`). Admins cannot deactivate themselves. Returns `200 { msg }` or `400/404`. |
| PATCH | `/admin/users/<id>/reactivate` | JWT (admin) | Reactivate a previously deactivated user. Returns `200 { msg }` or `404`. |

---

## Password Management (Feature C)

### PUT /user/password

**Description:** Change authenticated user's password.

**Auth:** `@jwt_required()` — Any authenticated role

**Request Body:**
```json
{
  "current_password": "password123",
  "new_password": "MySecure#1"
}
