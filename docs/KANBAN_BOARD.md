# US20 — Project Board & Roadmap

> **Peer Evaluation App — The Chipmunks**
> Feature: *Student Course Grade on Course Card*

---

## Roadmap & Timeline

```
  Jan 16          Jan 21              Feb 10     Feb 11                  Feb 12
    |               |                   |          |                       |
    v               v                   v          v                       v
 ┌──────┐     ┌──────────┐       ┌──────────┐ ┌───────────────────┐ ┌──────────────────────┐
 │SETUP │     │  INFRA   │       │ BACKEND  │ │ TESTING & DOCS    │ │ FRONTEND & DEPLOY    │
 │      │     │          │       │          │ │                   │ │                      │
 │Title │     │Dev test  │       │Schemas   │ │Endpoint tests     │ │GradeBadge component  │
 │update│     │run       │       │Grades svc│ │REST endpoint      │ │Dashboard integration │
 │      │     │Screenshot│       │          │ │Endpoint docs      │ │PR reviews & merges   │
 │      │     │directory │       │          │ │User stories update│ │                      │
 └──────┘     └──────────┘       └──────────┘ └───────────────────┘ └──────────────────────┘
   Phase 1       Phase 2           Phase 3         Phase 4                Phase 5
```

---

## Kanban Board

### BACKLOG
```
┌─────────────────────────────────────────┐
│                                         │
│            (no items remaining)         │
│                                         │
└─────────────────────────────────────────┘
```

### IN PROGRESS
```
┌─────────────────────────────────────────┐
│                                         │
│            (no items remaining)         │
│                                         │
└─────────────────────────────────────────┘
```

### IN REVIEW
```
┌─────────────────────────────────────────┐
│                                         │
│            (no items remaining)         │
│                                         │
└─────────────────────────────────────────┘
```

### DONE
```
┌─────────────────────────────────────────┐
│                                         │
│  [x] PR #20  Grade schemas & service    │
│  [x] PR #21  Endpoint tests             │
│  [x] PR #22  REST endpoint              │
│  [x] PR #23  Docs & user stories        │
│  [x] PR #25  GradeBadge component       │
│  [x] PR #26  Dashboard integration      │
│                                         │
└─────────────────────────────────────────┘
```

---

## Sprint Breakdown

### Phase 3 — Backend (Feb 10)

<details>
<summary><strong>PR #20 — Grade Schemas & Aggregation Service</strong></summary>

| Field | Detail |
|-------|--------|
| **Author** | Simon Velez |
| **Branch** | `feature/us20-student-grades-dev2` |
| **Merged** | Feb 12, 2026 |
| **Status** | Merged |

**Files Changed (3 files, +90 lines)**
| File | Changes |
|------|---------|
| `flask_backend/api/models/schemas.py` | +18 — Grade response schemas |
| `flask_backend/api/services/student_grades_service.py` | +72 — Aggregation logic for per-course scores |
| `example/example.txt` | new file |

**What it does:**
- Defines serialization schemas for grade data
- Implements aggregation service that calculates per-course average from peer review scores
- Provides the data layer that the REST endpoint consumes

</details>

---

### Phase 4 — Testing & Documentation (Feb 11)

<details>
<summary><strong>PR #21 — Student Grades Endpoint Tests</strong></summary>

| Field | Detail |
|-------|--------|
| **Author** | Ayman (aymanBH04) |
| **Branch** | `feature-us20` |
| **Merged** | Feb 12, 2026 |
| **Status** | Merged |

**Files Changed (3 files, +490 lines)**
| File | Changes |
|------|---------|
| `flask_backend/api/__init__.py` | +2 — Register student blueprint |
| `flask_backend/api/controllers/student_controller.py` | +88 — `GET /student/grades` controller |
| `flask_backend/tests/test_student_grades.py` | +400 — Comprehensive test suite |

**What it does:**
- Registers the student API blueprint
- Creates the controller for the grades endpoint
- 400 lines of tests covering: authenticated access, grade aggregation, edge cases, error handling

</details>

<details>
<summary><strong>PR #22 — Student Grades REST Endpoint</strong></summary>

| Field | Detail |
|-------|--------|
| **Author** | Shondiiee (mkpoojitha) |
| **Branch** | `feature/student-grades-endpoint` |
| **Merged** | Feb 12, 2026 |
| **Status** | Merged |

**Files Changed (1 file, +1/-1)**
| File | Changes |
|------|---------|
| `flask_backend/api/controllers/student_controller.py` | +1/-1 — Endpoint refinement |

**What it does:**
- Refines the `GET /student/grades` endpoint
- Returns per-course aggregated peer review scores for the authenticated student

</details>

<details>
<summary><strong>PR #23 — Documentation & User Stories Update</strong></summary>

| Field | Detail |
|-------|--------|
| **Author** | mkpoojitha-dotcom |
| **Branch** | `Testing/Review` |
| **Merged** | Feb 11, 2026 |
| **Status** | Merged |

**Files Changed (2 files, +5/-1)**
| File | Changes |
|------|---------|
| `docs/dev-guidelines/ENDPOINT_SUMMARY.md` | +4 — Added `GET /student/grades` to endpoint docs |
| `docs/user_stories.md` | +1/-1 — Marked US20 as **Complete** |

**What it does:**
- Documents the new grades endpoint in the API reference
- Updates user story US20 status from In-Progress to Complete

</details>

---

### Phase 5 — Frontend & Integration (Feb 12)

<details>
<summary><strong>PR #25 — GradeBadge Frontend Component</strong></summary>

| Field | Detail |
|-------|--------|
| **Author** | Daniel Cuevas |
| **Branch** | `ahmed-feat` |
| **Merged** | Feb 12, 2026 |
| **Status** | Merged |

**What it does:**
- Initial commit of the GradeBadge component for course cards
- Preparatory work before full dashboard integration

</details>

<details>
<summary><strong>PR #26 — Dashboard Integration</strong></summary>

| Field | Detail |
|-------|--------|
| **Author** | Daniel Cuevas |
| **Branch** | `daniel-feat` |
| **Merged** | Feb 12, 2026 |
| **Status** | Merged |

**Files Changed (6 files, +251/-14)**
| File | Changes |
|------|---------|
| `frontend/src/components/GradeBadge.css` | +96 — Styling with color-coded grades (green/yellow/red) |
| `frontend/src/components/GradeBadge.tsx` | +50 — Grade badge React component |
| `frontend/src/pages/Home.css` | +15/-1 — Dashboard layout adjustments |
| `frontend/src/pages/Home.tsx` | +68/-5 — Integrated GradeBadge into course cards |
| `frontend/src/types.d.ts` | +21/-1 — Grade-related TypeScript interfaces |
| `frontend/src/util/api.ts` | +15 — API call to `GET /student/grades` |

**What it does:**
- Displays student's average grade per course with color coding:
  - Green: 70%+
  - Yellow: 50–69%
  - Red: below 50%
- Handles empty, partial, and loading states
- Uses app CSS variables for consistent styling
- Cleaned up unused `api_addition.ts`

</details>

---

## Team Contributions

```
 ┌────────────────────────────────────────────────────────────────────────────┐
 │                        TEAM CONTRIBUTION MAP                              │
 │                                                                           │
 │  BACKEND                    TESTING                    FRONTEND           │
 │  ════════                   ═══════                    ════════           │
 │                                                                           │
 │  Simon Velez                Ayman (aymanBH04)          Daniel Cuevas      │
 │  ┌──────────────────┐       ┌──────────────────┐       ┌────────────────┐ │
 │  │ schemas.py    +18│       │ test_student_    │       │ GradeBadge.tsx │ │
 │  │ student_grades_  │       │ grades.py   +400 │       │            +50 │ │
 │  │ service.py    +72│       │ student_         │       │ GradeBadge.css │ │
 │  │                  │       │ controller.py +88│       │            +96 │ │
 │  │  Total: +90 lines│       │                  │       │ Home.tsx    +68 │ │
 │  └──────────────────┘       │  Total: +490 lines│      │ api.ts      +15 │ │
 │                             └──────────────────┘       │ types.d.ts  +21 │ │
 │                                                        │                │ │
 │  DOCUMENTATION                                         │ Total: +251    │ │
 │  ═════════════                                         │         lines  │ │
 │                                                        └────────────────┘ │
 │  mkpoojitha / Shondiiee                                                   │
 │  ┌──────────────────┐                                                     │
 │  │ ENDPOINT_SUMMARY │                                                     │
 │  │            .md +4│                                                     │
 │  │ user_stories     │                                                     │
 │  │           .md +1 │                                                     │
 │  │ student_         │                                                     │
 │  │ controller.py +1 │                                                     │
 │  │                  │                                                     │
 │  │  Total: +6 lines │                                                     │
 │  └──────────────────┘                                                     │
 │                                                                           │
 │  ┌─────────────────────────────────────────────────────────────────────┐  │
 │  │  TOTAL PROJECT STATS:  15 files changed  |  +837 lines  |  6 PRs   │  │
 │  └─────────────────────────────────────────────────────────────────────┘  │
 └────────────────────────────────────────────────────────────────────────────┘
```

---

## Acceptance Criteria Status

| # | Criteria | Status |
|---|----------|--------|
| 1 | Student has a total grade, the course card displays it prominently | Done |
| 2 | Grade data updates as new scores are recorded | Done |
| 3 | Course cards indicate when grade data is unavailable | Done |

---

## Architecture Flow

```
  Student Browser                    Flask Backend                  Database
  ══════════════                     ═════════════                  ════════

  ┌────────────┐    GET /student    ┌─────────────────┐          ┌─────────┐
  │  Home.tsx   │───── /grades ────>│ student_         │─ query ─>│ Reviews │
  │  (Dashboard)│                   │ controller.py    │          │ Courses │
  │             │                   │                  │          │ Scores  │
  │  ┌────────┐│    JSON response   │  ┌────────────┐ │  rows    └─────────┘
  │  │Grade   ││<───────────────────│  │student_    │ │<──────────────┘
  │  │Badge   ││                    │  │grades_     │ │
  │  │ 85% A  ││                    │  │service.py  │ │
  │  └────────┘│                    │  └────────────┘ │
  └────────────┘                    │  ┌────────────┐ │
                                    │  │schemas.py  │ │
                                    │  └────────────┘ │
                                    └─────────────────┘
```

---

## PR Merge Order

```
  PR #20 ──> PR #21 ──> PR #22 ──> PR #23 ──> PR #25 ──> PR #26
    │           │          │          │           │          │
  Schemas    Tests     Endpoint    Docs       Badge     Dashboard
  +Service              Refine    Update     Component  Integration
    │           │          │          │           │          │
  Simon      Ayman     Shondiiee  mkpoojitha  Daniel     Daniel
    │           │          │          │           │          │
    v           v          v          v           v          v
  ───[Feb 10]────[Feb 11]───────────────────[Feb 12]──────────>
       Day 1       Day 2                      Day 3
```

---

> **US20 — COMPLETE**
> All 6 pull requests merged. Feature shipped Feb 12, 2026.
