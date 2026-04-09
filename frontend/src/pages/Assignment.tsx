import { useEffect, useState, ChangeEvent } from "react";
import { useParams } from "react-router-dom";
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
>>>>>>> Stashed changes
} from "../util/api";

interface SelectedCriterion {
  row: number;
  column: number;
}

export default function Assignment() {
  const { id } = useParams();
  const [stuGroup, setStuGroup] = useState<StudentGroups[]>([]);
  const [revieweeID, setRevieweeID] = useState<number>(0);
  const [stuID, setStuID] = useState<number>(0);
  const [selectedCriteria, setSelectedCriteria] = useState<SelectedCriterion[]>([]);
  const [review, setReview] = useState<number[]>([]);

  useEffect(() => {
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
  }, [revieweeID, id, stuID]);

<<<<<<< Updated upstream
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
=======
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
      await submitReview({ assignment_id: Number(id), reviewee_id: revieweeID, criteria });
      setAlreadyReviewed(true);
      setJustSubmitted(true);
    } catch (error) {
      setSubmitStatus(error instanceof Error ? error.message : "Failed to submit review.");
>>>>>>> Stashed changes
    }
  };

  function handleRadioChange(event: ChangeEvent<HTMLInputElement>): void {
    const selectedID = Number(event.target.value);
    setRevieweeID(selectedID);
    console.log(`Selected group member ID: ${selectedID}`);
  }

  return (
    <>
      <div className="AssignmentHeader">
        <h2>Assignment {id}</h2>
      </div>

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
          { label: "Home",  path: `/assignments/${id}` },
          { label: "Group", path: `/assignments/${id}/group` },
          ...(isTeacher()
            ? [{ label: "Reviews", path: `/assignments/${id}/reviews` }]
            : []),
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
              <RubricForm
                criteria={rubricCriteria}
                onSubmit={handleSubmitReview}
              />
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

