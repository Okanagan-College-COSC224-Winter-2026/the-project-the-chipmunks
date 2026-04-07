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
  due_date?: string;
  description_html?: string;
  attachment_filename?: string;
  has_attachment?: boolean;
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
  comments: string;
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
// ============================================================
// STUDENT PROGRESS DASHBOARD (US5)
// ============================================================
interface ProgressPerAssignment {
  in_group: boolean;
  reviews_given: number;
  reviews_received: number;
  avg_score: number | null;
}
interface ProgressStudent {
  user_id: number;
  name: string;
  email: string;
  per_assignment: Record<string, ProgressPerAssignment>;
}
interface CourseProgressResponse {
  course_id: number;
  course_name: string;
  assignments: { id: number; name: string }[];
  students: ProgressStudent[];
}