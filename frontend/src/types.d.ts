interface Course {
  id: number;
  teacherID: number;
  name: string;
}

interface User {
  id: number;
  name: string;
  email: string;
  role: 'student' | 'teacher' | 'admin';
}

interface StudentGroups {
  groupID: number;
  userID: number;
  assignmentID: number;
}

<<<<<<< Updated upstream
interface CourseGroup{
=======
interface CourseGroup {
>>>>>>> Stashed changes
  id: number;
  name: string;
  assignmentID: number;
}

interface GroupTable {
  [key: number]: GroupTableValue[];
}

<<<<<<< Updated upstream
interface GroupTableValue{
=======
interface GroupTableValue {
>>>>>>> Stashed changes
  groupID: number;
  userID: number;
  assignmentID: number;
}

interface Criterion {
  rubricID: number;
  question: string;
  scoreMax: number;
  hasScore: boolean;
}

interface Assignment {
  id: number;
  name: string;
  courseID: number;
  rubric?: string;
  due_date?: string;
}

interface CourseWithAssignments extends Course {
  assignments?: Assignment[];
  assignmentCount?: number;
<<<<<<< Updated upstream
=======
}

// ============================================================
// STUDENT GRADES (US20)
// ============================================================
interface CourseGrade {
  course_id: number;
  course_name: string;
  grade: number | null;
  max_score: number | null;
  graded_assignments: number;
  total_assignments: number;
  has_grades: boolean;
}

interface StudentGradesResponse {
  student_id: number;
  courses: CourseGrade[];
}

// ============================================================
// PEER REVIEW SUBMISSION (US1/US11)
// ============================================================
interface RubricCriteria {
  id: number;
  question: string;
  score_max: number;
  has_score: boolean;
  can_comment: boolean;
}

interface RubricResponse {
  rubric_id: number;
  assignment_id: number;
  criteria: RubricCriteria[];
}

interface CriterionSubmission {
  criteria_description_id: number;
  grade: number;
  comments?: string;
}

interface ReviewSubmission {
  assignment_id: number;
  reviewee_id: number;
  criteria: CriterionSubmission[];
}

// ============================================================
// STUDENT FEEDBACK (US12)
// ============================================================
interface CriteriaFeedback {
  question: string;
  avg_score: number;
  score_max: number;
  comments: string[];
}

interface FeedbackResponse {
  assignment_id: number;
  assignment_name: string;
  total_reviews: number;
  criteria_feedback: CriteriaFeedback[];
  overall_avg: number;
>>>>>>> Stashed changes
}interface Course {
  id: number;
  teacherID: number;
  name: string;
}

interface User {
  id: number;
  name: string;
  email: string;
  role: "student" | "teacher" | "admin";
}

interface StudentGroups {
  groupID: number;
  userID: number;
  assignmentID: number;
}

interface CourseGroup {
  id: number;
  name: string;
  assignmentID: number;
}

interface GroupTable {
  [key: number]: GroupTableValue[];
}

interface GroupTableValue {
  groupID: number;
  userID: number;
  assignmentID: number;
}

interface Criterion {
  rubricID: number;
  question: string;
  scoreMax: number;
  hasScore: boolean;
}

interface Assignment {
  id: number;
  name: string;
  courseID: number;
  rubric?: string;
  dueDate?: string;
  due_date?: string;
}

interface CourseWithAssignments extends Course {
  assignments?: Assignment[];
  assignmentCount?: number;
}

// ============================================================
// STUDENT GRADES (US20)
// ============================================================
interface CourseGrade {
  course_id: number;
  course_name: string;
  grade: number | null;
  max_score: number | null;
  graded_assignments: number;
  total_assignments: number;
  has_grades: boolean;
}

interface StudentGradesResponse {
  student_id: number;
  courses: CourseGrade[];
}

// ============================================================
// PEER REVIEW SUBMISSION (US1/US11)
// ============================================================
interface RubricCriteria {
  id: number;
  question: string;
  score_max: number;
  has_score: boolean;
  can_comment: boolean;
}

interface RubricResponse {
  rubric_id: number;
  assignment_id: number;
  criteria: RubricCriteria[];
}

interface CriterionSubmission {
  criteria_description_id: number;
  grade: number;
  comments?: string;
}

interface ReviewSubmission {
  assignment_id: number;
  reviewee_id: number;
  criteria: CriterionSubmission[];
}

// ============================================================
// STUDENT FEEDBACK (US12)
// ============================================================
interface CriteriaFeedback {
  question: string;
  avg_score: number;
  score_max: number;
  comments: string[];
}

interface FeedbackResponse {
  assignment_id: number;
  assignment_name: string;
  total_reviews: number;
  criteria_feedback: CriteriaFeedback[];
  overall_avg: number;
}