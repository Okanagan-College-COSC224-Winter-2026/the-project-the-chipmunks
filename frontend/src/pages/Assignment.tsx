import { useEffect, useState, ChangeEvent } from "react";
import { useParams } from "react-router-dom";
import "./Assignment.css";
import RubricCreator from "../components/RubricCreator";
import RubricDisplay from "../components/RubricDisplay";
import TabNavigation from "../components/TabNavigation";
import AssignmentAttachment from "../components/AssignmentAttachment";
import ConclusionSection from "../components/ConclusionSection";
import RubricForm from "../components/RubricForm";
import { isTeacher } from "../util/login";
import ReviewFileUpload from '../components/ReviewFileUpload';

import {
  listStuGroup,
  getUserId,
  getReview,
  getAssignment,
  listCourseMembers,
  submitReview,
  getRubricByAssignment,
  uploadReviewFiles,
} from "../util/api";

export default function Assignment() {
  const [attachedFiles, setAttachedFiles] = useState<File[]>([]);
  const { id } = useParams();
  const [stuGroup, setStuGroup] = useState<StudentGroups[]>([]);
  const [revieweeID, setRevieweeID] = useState<number>(0);
  const [stuID, setStuID] = useState<number>(0);
  const [assignmentName, setAssignmentName] = useState<string>("");
  const [descriptionHtml, setDescriptionHtml] = useState<string>("");
  const [memberNames, setMemberNames] = useState<Record<number, string>>({});
  const [rubricCriteria, setRubricCriteria] = useState<RubricCriteria[]>([]);
  const [submitStatus, setSubmitStatus] = useState<string>("");
  const [alreadyReviewed, setAlreadyReviewed] = useState(false);
  const [justSubmitted, setJustSubmitted] = useState(false);

  // Load assignment details + student list once on mount
  useEffect(() => {
    (async () => {
      try {
        const assignment = await getAssignment(Number(id));
        setAssignmentName(assignment.name || `Assignment ${id}`);
        setDescriptionHtml(assignment.description_html || "");

        // Load course members for name lookup
        if (assignment.courseID) {
          const members = await listCourseMembers(String(assignment.courseID));
          const nameMap: Record<number, string> = {};
          members.forEach((m: { id: number; name: string }) => {
            nameMap[m.id] = m.name;
          });
          setMemberNames(nameMap);
        }
      } catch (e) {
        console.error("Failed to load assignment details:", e);
      }

      // Load rubric criteria for RubricForm
      try {
        const rubricData = await getRubricByAssignment(Number(id));
        setRubricCriteria(rubricData.criteria || []);
      } catch {
        // No rubric yet
      }

      // Load student's own group members
      try {
        const uid = await getUserId();
        setStuID(uid);
        const stus = await listStuGroup(Number(id), uid);
        setStuGroup(stus);
      } catch (e) {
        console.error("Failed to load group:", e);
      }
    })();
  }, [id]);

  // Check if this reviewer already submitted a review for the selected reviewee
  useEffect(() => {
    setAlreadyReviewed(false);
    setJustSubmitted(false);
    if (!revieweeID || !stuID) return;
    (async () => {
      try {
        const reviewResponse = await getReview(Number(id), stuID, revieweeID);
        const reviewData = await reviewResponse.json();
        if (reviewData?.id) setAlreadyReviewed(true);
      } catch {
        // No existing review — fine
      }
    })();
  }, [revieweeID, id, stuID]);

  const handleRadioChange = (event: ChangeEvent<HTMLInputElement>) => {
    setRevieweeID(Number(event.target.value));
    setSubmitStatus("");
  };

  const handleSubmitReview = async (
    scores: Record<number, number>,
    comments: Record<number, string>
  ) => {
    try {
      setSubmitStatus("");
      const criteria = rubricCriteria.map((c) => ({
        criteria_description_id: c.id,
        grade: scores[c.id] ?? 0,
        comments: comments[c.id] ?? "",
      }));
      const data = await submitReview({ assignment_id: Number(id), reviewee_id: revieweeID, criteria });

      if (attachedFiles.length > 0) {
        await uploadReviewFiles(data.review_id, attachedFiles);
        setAttachedFiles([]);
      }

      setAlreadyReviewed(true);
      setJustSubmitted(true);
    } catch (error) {
      setSubmitStatus(error instanceof Error ? error.message : "Failed to submit review.");
    }
  };

  return (
    <>
      <div className="AssignmentHeader">
        <h2>{assignmentName || `Assignment ${id}`}</h2>
      </div>

      <TabNavigation
        tabs={[
          { label: "Home",  path: `/assignments/${id}` },
          { label: "Group", path: `/assignments/${id}/group` },
          ...(isTeacher()
            ? [{ label: "Reviews", path: `/assignments/${id}/reviews` }]
            : [{ label: "Team Submissions", path: `/assignments/${id}/team-submissions` }]
          ),
        ]}
      />

      {/* Assignment description (rich text from teacher) */}
      {descriptionHtml && (
        <div
          className="assignmentDescription"
          dangerouslySetInnerHTML={{ __html: descriptionHtml }}
          style={{ padding: "0 12px 12px" }}
        />
      )}

      {/* PDF attachment — teachers can upload, everyone can download */}
      <AssignmentAttachment assignmentId={Number(id)} />

      {/* Conclusion files — teachers upload after review period, students download */}
      <ConclusionSection assignmentId={Number(id)} />

      <div className="assignmentRubricDisplay">
        <RubricDisplay rubricId={Number(id)} />
      </div>

      {isTeacher() && (
        <div className="assignmentRubric">
          <RubricCreator id={Number(id)} />
        </div>
      )}

      {!isTeacher() && (
        <div className="groupMembers">
          <h3>Select a group member to review</h3>

          {stuGroup.length === 0 && (
            <p style={{ color: "#888" }}>No group members found.</p>
          )}

          {stuGroup.map((stu) => (
            <div key={stu.userID} style={{ margin: "4px 0" }}>
              <input
                type="radio"
                id={`stu-${stu.userID}`}
                value={stu.userID}
                name="groupMembers"
                onChange={handleRadioChange}
              />
              <label htmlFor={`stu-${stu.userID}`} style={{ marginLeft: 6 }}>
                {memberNames[stu.userID] || `Student #${stu.userID}`}
              </label>
            </div>
          ))}

          {revieweeID > 0 && (
            alreadyReviewed ? (
              <p style={{ color: "#2e7d32", marginTop: 12 }}>
                {justSubmitted
                  ? "✓ Review submitted successfully!"
                  : "✓ You have already submitted a review for this student."}
              </p>
            ) : rubricCriteria.length > 0 ? (
              <>
                <ReviewFileUpload files={attachedFiles} onChange={setAttachedFiles} />
                <RubricForm
                  criteria={rubricCriteria}
                  onSubmit={handleSubmitReview}
                />
              </>
            ) : (
              <p style={{ color: "#888", marginTop: 12 }}>
                No rubric assigned yet — the teacher hasn't created one.
              </p>
            )
          )}

          {submitStatus && (
            <p style={{ marginTop: 8, color: submitStatus.includes("success") ? "#2e7d32" : "#c33" }}>
              {submitStatus}
            </p>
          )}
        </div>
      )}
    </>
  );
}