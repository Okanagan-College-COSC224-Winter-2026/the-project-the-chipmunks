import { useEffect, useState, ChangeEvent } from "react";
import { useParams, useNavigate } from "react-router-dom";
import RichTextEditor from "../components/RichTextEditor";
import StatusMessage from "../components/StatusMessage";
import "./Assignment.css";
import RubricCreator from "../components/RubricCreator";
import RubricDisplay from "../components/RubricDisplay";
import TabNavigation from "../components/TabNavigation";
import { isTeacher } from "../util/login";

import { 
  listStuGroup,
  getUserId,
<<<<<<< Updated upstream
  createReview,
  createCriterion,
  getReview
=======
  getReview,
  getAssignment,
  listCourseMembers,
  submitReview,
  getRubricByAssignment,
  uploadReviewFiles,
  editAssignment,
  deleteAssignment,
>>>>>>> Stashed changes
} from "../util/api";

interface SelectedCriterion {
  row: number;
  column: number;
}

export default function Assignment() {
  const { id } = useParams();
  const navigate = useNavigate();
  const [stuGroup, setStuGroup] = useState<StudentGroups[]>([]);
  const [revieweeID, setRevieweeID] = useState<number>(0);
  const [stuID, setStuID] = useState<number>(0);
<<<<<<< Updated upstream
  const [selectedCriteria, setSelectedCriteria] = useState<SelectedCriterion[]>([]);
  const [review, setReview] = useState<number[]>([]);
=======
  const [assignmentName, setAssignmentName] = useState<string>("");
  const [descriptionHtml, setDescriptionHtml] = useState<string>("");
  const [memberNames, setMemberNames] = useState<Record<number, string>>({});
  const [rubricCriteria, setRubricCriteria] = useState<RubricCriteria[]>([]);
  const [submitStatus, setSubmitStatus] = useState<string>("");
  const [alreadyReviewed, setAlreadyReviewed] = useState(false);
  const [justSubmitted, setJustSubmitted] = useState(false);
  const [courseId, setCourseId] = useState<number | null>(null);
>>>>>>> Stashed changes

  // Edit form state
  const [showEditForm, setShowEditForm] = useState(false);
  const [editName, setEditName] = useState("");
  const [editDescription, setEditDescription] = useState("");
  const [editStatus, setEditStatus] = useState<string>("");
  const [editStatusType, setEditStatusType] = useState<"success" | "error">("error");
  const [isSaving, setIsSaving] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);

  // Load assignment details + student list once on mount
  useEffect(() => {
<<<<<<< Updated upstream
      (async () => {
        const stuID = await getUserId();
      setStuID(stuID);
      const stus = await listStuGroup(Number(id), stuID);
      setStuGroup(stus);
        try {
          const reviewResponse = await getReview(Number(id), stuID, revieweeID);
          const reviewData = await reviewResponse.json();
          setReview(reviewData.grades);
          console.log("Review data:", reviewData);
        } catch (error) {
          console.error('Error fetching review:', error);
        }
      })();
=======
    (async () => {
      try {
        const assignment = await getAssignment(Number(id));
        setAssignmentName(assignment.name || `Assignment ${id}`);
        setDescriptionHtml(assignment.description_html || "");

        // Load course members for name lookup
        setCourseId(assignment.courseID || null);
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
>>>>>>> Stashed changes
  }, [revieweeID, id, stuID]);

  const handleCriterionSelect = (row: number, column: number) => {
    // Check if this criterion is already selected
    const existingIndex = selectedCriteria.findIndex(
      criterion => criterion.row === row && criterion.column === column
    );
    
    if (existingIndex >= 0) {
      // If already selected, remove it (toggle off)
      setSelectedCriteria(prev => 
        prev.filter((_, index) => index !== existingIndex)
      );
    } else {
      // Add the new criterion, removing any other selection in the same row
      setSelectedCriteria(prev => {
        // Remove any existing selection for this row
        const filteredCriteria = prev.filter(criterion => criterion.row !== row);
        // Add the new selection
        return [...filteredCriteria, { row, column }];
      });
    }
  };

<<<<<<< Updated upstream
  function handleRadioChange(event: ChangeEvent<HTMLInputElement>): void {
    const selectedID = Number(event.target.value);
    setRevieweeID(selectedID);
    console.log(`Selected group member ID: ${selectedID}`);
  }
=======

  const handleOpenEdit = () => {
    setEditName(assignmentName);
    setEditDescription(descriptionHtml);
    setEditStatus("");
    setShowEditForm(true);
  };

  const handleCancelEdit = () => {
    setShowEditForm(false);
    setEditStatus("");
  };

  const handleSaveEdit = async () => {
    setIsSaving(true);
    setEditStatus("");
    try {
      await editAssignment(Number(id), {
        name: editName,
        description_html: editDescription,
      });
      setAssignmentName(editName);
      setDescriptionHtml(editDescription);
      setEditStatusType("success");
      setEditStatus("Assignment updated successfully.");
      setShowEditForm(false);
    } catch (error) {
      setEditStatusType("error");
      setEditStatus(error instanceof Error ? error.message : "Failed to save changes.");
    } finally {
      setIsSaving(false);
    }
  };

  const handleDeleteAssignment = async () => {
    const confirmed = window.confirm(
      `Are you sure you want to delete "${assignmentName}"? This cannot be undone.`
    );
    if (!confirmed) return;
    setIsDeleting(true);
    try {
      await deleteAssignment(Number(id));
      navigate(`/classes/${courseId}/home`);
    } catch (error) {
      setEditStatusType("error");
      setEditStatus(error instanceof Error ? error.message : "Failed to delete assignment.");
      setIsDeleting(false);
    }
  };
>>>>>>> Stashed changes

  return (
    <>
      <div className="AssignmentHeader">
<<<<<<< Updated upstream
        <h2>Assignment {id}</h2>
=======
        <h2>{assignmentName || `Assignment ${id}`}</h2>
        {isTeacher() && (
          <div className="assignment-header-actions">
            <button className="btn-edit-assignment" onClick={handleOpenEdit}>
              Edit Assignment
            </button>
            <button
              className="btn-delete-assignment"
              onClick={handleDeleteAssignment}
              disabled={isDeleting}
            >
              {isDeleting ? "Deleting..." : "Delete Assignment"}
            </button>
          </div>
        )}
>>>>>>> Stashed changes
      </div>

      {/* Edit form — teachers only, toggled by Edit Assignment button */}
      {isTeacher() && showEditForm && (
        <div className="assignment-edit-form">
          <h3>Edit Assignment</h3>
          <label className="assignment-edit-label">Assignment Name</label>
          <input
            className="assignment-edit-input"
            type="text"
            value={editName}
            onChange={e => setEditName(e.target.value)}
          />
          <label className="assignment-edit-label">Description</label>
          <RichTextEditor value={editDescription} onChange={setEditDescription} />
          <div className="assignment-edit-actions">
            <button onClick={handleSaveEdit} disabled={isSaving}>
              {isSaving ? "Saving..." : "Save Changes"}
            </button>
            <button className="btn-secondary" onClick={handleCancelEdit}>
              Cancel
            </button>
          </div>
          {editStatus && (
            <StatusMessage message={editStatus} type={editStatusType} />
          )}
        </div>
      )}

      {/* Feedback after a successful edit (form closed) */}
      {isTeacher() && !showEditForm && editStatus && (
        <StatusMessage message={editStatus} type={editStatusType} />
      )}

      <TabNavigation
        tabs={[
          {
            label: "Home",
            path: `/assignment/${id}`,
          },
          {
            label: "Group",
            path: `/assignment/${id}/group`,
          }
        ]}
      />

<<<<<<< Updated upstream
      <div className='assignmentRubricDisplay'>
        <RubricDisplay rubricId={Number(id)} onCriterionSelect={handleCriterionSelect} grades={review} />
=======
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
>>>>>>> Stashed changes
      </div>
      {
        isTeacher() && 
          <div className='assignmentRubric'>
            <RubricCreator id={Number(id)}/>
          </div>
      }

<<<<<<< Updated upstream
{
      //List group members as radio buttons to select for given review
      !isTeacher() && <div className='groupMembers'>
        <h3>Select a group member to review</h3>
          {stuGroup.map((stus) => {
                return (
                  <>
                  <input type='radio' id={stus.userID.toString()} value={stus.userID} name='groupMembers' onChange={handleRadioChange}></input>
                  <label htmlFor={stus.userID.toString()}>{stus.userID}</label>
                  <br></br>
                  </>
                )
              }
=======
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
>>>>>>> Stashed changes
            )
          }
          <button className='submitReview' onClick={async () => {
            console.log("Submitting review with selected criteria:", selectedCriteria);
            try {
              const reviewResponse = await createReview(Number(id), stuID, revieweeID);
              const reviewData = await reviewResponse.json();
              console.log("Review response:", reviewData);
              for (const criterion of selectedCriteria) {
                await createCriterion(reviewData.id, criterion.row, criterion.column, "");
              }
              console.log('Review submitted successfully');
            } catch (error) {
              console.error('Error submitting review:', error);
            }
          }}>Submit Review</button>
      </div>}
    </>
  );
}

