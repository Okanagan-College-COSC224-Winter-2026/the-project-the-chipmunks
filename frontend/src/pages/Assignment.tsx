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

  // Edit form state
  const [showEditForm, setShowEditForm] = useState(false);
  const [editName, setEditName] = useState("");
  const [editDescription, setEditDescription] = useState("");
  const [editStatus, setEditStatus] = useState<string>("");
  const [editStatusType, setEditStatusType] = useState<"success" | "error">("error");
  const [isSaving, setIsSaving] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
>>>>>>> Stashed changes

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
>>>>>>> Stashed changes
        }
      })();
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
<<<<<<< Updated upstream
          {
            label: "Home",
            path: `/assignment/${id}`,
          },
          {
            label: "Group",
            path: `/assignment/${id}/group`,
          }
=======
          { label: "Home", path: `/assignments/${id}` },
          { label: "Group", path: `/assignments/${id}/group` },
          ...(isTeacher()
            ? [{ label: "Reviews", path: `/assignments/${id}/reviews` }]
            : [{ label: "Team Submissions", path: `/assignments/${id}/team-submissions` }]
          ),
>>>>>>> Stashed changes
        ]}
      />

      <div className='assignmentRubricDisplay'>
        <RubricDisplay rubricId={Number(id)} onCriterionSelect={handleCriterionSelect} grades={review} />
      </div>
      {
        isTeacher() && 
          <div className='assignmentRubric'>
            <RubricCreator id={Number(id)}/>
          </div>
      }

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

