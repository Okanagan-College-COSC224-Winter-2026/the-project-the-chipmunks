# Ayman's Presentation Script — PR #72

---

## Introduction (30 seconds)

> "Hi everyone, I'm Ayman. I worked on two backend tasks for our peer review application:
> **Task 1** is the Admin User Management Dashboard, and **Task 2** is the Teacher Assignment Analytics with CSV Export.
> Both are Flask REST API endpoints with full test coverage."

---

## Task 1: Admin User Management Dashboard — US26 (2-3 minutes)

> "For my first task, I built the full admin user management system. This lets an admin
> manage all user accounts in the application through a set of REST API endpoints."

### What I Built

> "Here are the endpoints I implemented — all protected so only admins can access them:"

| Method   | Endpoint                          | What It Does                          |
|----------|-----------------------------------|---------------------------------------|
| `GET`    | `/admin/users`                    | List all users with pagination, search, and role filter |
| `POST`   | `/admin/users/create`             | Create a new user (student, teacher, or admin) |
| `PUT`    | `/admin/users/<id>`               | Update a user's name, email, or role  |
| `PUT`    | `/admin/users/<id>/role`          | Change just a user's role             |
| `PATCH`  | `/admin/users/<id>/deactivate`    | Soft-delete (deactivate) a user       |
| `PATCH`  | `/admin/users/<id>/reactivate`    | Reactivate a deactivated user         |
| `DELETE` | `/admin/users/<id>`               | Permanently delete a user             |

### Key Features I Want to Highlight

> "A few things I'm proud of in this implementation:"

1. **Input Validation** — I used Marshmallow schemas (`AdminUserCreateSchema`, `AdminUserUpdateSchema`) to validate all incoming data before it touches the database.
2. **Safety Checks** — An admin cannot demote themselves or delete their own account, which prevents accidentally locking yourself out.
3. **Search & Pagination** — The list endpoint supports `?search=`, `?role=`, `?page=`, and `?per_page=` query params so the frontend can display users efficiently.
4. **Soft Delete** — Instead of only hard-deleting, I added deactivate/reactivate so accounts can be temporarily disabled.

### Testing

> "I wrote 245 lines of tests in `test_admin_users.py` covering all the endpoints — creating users, updating, deleting, role changes, duplicate email checks, self-demotion prevention, and 404 handling. All tests pass."

---

## Task 2: Teacher Assignment Analytics & CSV Export — US7/US8 (2-3 minutes)

> "For my second task, I extended the teacher controller to give teachers analytics
> about how their assignments are going, plus the ability to export everything as a CSV."

### What I Built

| Method | Endpoint                                        | What It Does                              |
|--------|-------------------------------------------------|-------------------------------------------|
| `GET`  | `/teacher/assignments/<id>/analytics`           | Per-criterion averages, completion rate, outlier detection |
| `GET`  | `/teacher/assignments/<id>/export`              | Download all review data as a CSV file    |

### Analytics Endpoint — Deep Dive

> "The analytics endpoint returns a JSON object with:"

- **Completion rate** — what percentage of students have submitted their reviews
- **Per-criterion averages** — for each rubric question, the average score and how many responses
- **Outlier detection** — any reviews that are more than 2 standard deviations from the mean get flagged, so teachers can spot suspicious or unusual reviews

> "For outlier detection, I used Python's `statistics` module to calculate the mean and
> standard deviation across all scores, then flagged any review where the total score
> deviates by more than 2x the standard deviation."

### CSV Export Endpoint

> "The export endpoint generates a downloadable CSV file with columns:
> `review_id`, `reviewer_id`, `reviewee_id`, `criterion`, `score`, `max_score`, `comment`.
> Teachers can open this in Excel or Google Sheets to do their own analysis."

### Testing

> "I wrote 317 lines of tests in `test_analytics.py` — 8 test cases covering:
> analytics with no reviews, single review, multiple reviews, outlier detection,
> CSV export format, empty exports, and 404 handling. All 8 pass."

---

## Summary (30 seconds)

> "To wrap up — I built **7 admin endpoints** and **2 analytics endpoints**, totaling
> about **900+ lines of new code** across controllers and test files. Everything is
> backend-only with Flask, uses JWT authentication for security, and has full test coverage.
> That's it — any questions?"

---

## Quick Demo Commands (if live demo needed)

```bash
# Run just my tests
cd flask_backend
python -m pytest tests/test_admin_users.py -v
python -m pytest tests/test_analytics.py -v
```
