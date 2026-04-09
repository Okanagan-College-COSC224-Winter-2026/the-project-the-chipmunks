import { useEffect, useState } from "react";
import ClassCard from "../components/ClassCard";
<<<<<<< Updated upstream
=======
import GradeBadge from "../components/GradeBadge";
>>>>>>> Stashed changes

import './Home.css'
import { listClasses, listAssignments } from "../util/api";
import { isTeacher, isAdmin } from "../util/login";

export default function Home() {
  const [courses, setCourses] = useState<CourseWithAssignments[]>([]);
  const [loading, setLoading] = useState(true);

<<<<<<< Updated upstream
=======
  // Dev 5 — grade state
  const [gradeMap, setGradeMap] = useState<Map<number, CourseGrade>>(new Map());
  const [gradesLoading, setGradesLoading] = useState(true);

>>>>>>> Stashed changes
  useEffect(() => {
    ;(async () => {
      try {
        const coursesResp = await listClasses();
        
        // Fetch assignments for each course
        const coursesWithAssignments = await Promise.all(
          coursesResp.map(async (course: Course) => {
            try {
              const assignments = await listAssignments(String(course.id));
              return {
                ...course,
                assignments: assignments || [],
                assignmentCount: assignments?.length || 0
              };
            } catch (error) {
              console.error(`Error fetching assignments for course ${course.id}:`, error);
              return {
                ...course,
                assignments: [],
                assignmentCount: 0
              };
            }
          })
        );
        
        setCourses(coursesWithAssignments);
      } catch (error) {
        console.error("Error fetching courses:", error);
      } finally {
        setLoading(false);
      }
    })();
  }, []);

<<<<<<< Updated upstream
=======
  // Dev 5 — fetch grades for students only
  useEffect(() => {
    if (!isStudent()) {
      setGradesLoading(false);
      return;
    }

    ;(async () => {
      try {
        const data = await getStudentGrades();
        const map = new Map<number, CourseGrade>();
        data.courses.forEach((course) => {
          map.set(course.course_id, course);
        });
        setGradeMap(map);
      } catch (error) {
        console.error("Error fetching grades:", error);
      } finally {
        setGradesLoading(false);
      }
    })();
  }, []);

>>>>>>> Stashed changes
  if (loading) {
    return (
      <div className="Home">
        <h1>Peer Review Dashboard</h1>
        <p>Loading courses...</p>
      </div>
    );
  }

  return (
    <div className="Home">
      <h1>Peer Review Dashboard</h1>

      <div className="Classes">
        {
          courses.map((course) => {
            const assignmentText = `${course.assignmentCount || 0} assignments`;
<<<<<<< Updated upstream
            
            return (
              <ClassCard
                key={course.id}
                image="https://crc.losrios.edu//shared/img/social-1200-630/programs/general-science-social.jpg"
                name={course.name}
                subtitle={assignmentText}
                onclick={() => {
                  window.location.href = `/classes/${course.id}/home`
                }}
              />
=======
            // Dev 5 — look up grade for this course
            const courseGrade = gradeMap.get(course.id);
            
            return (
              <div key={course.id} className="CourseCardWrapper">
                <ClassCard
                  image="https://crc.losrios.edu//shared/img/social-1200-630/programs/general-science-social.jpg"
                  name={course.name}
                  subtitle={assignmentText}
                  onclick={() => {
                    window.location.href = `/classes/${course.id}/home`
                  }}
                />
                {/* Dev 5 — show grade badge for students only */}
                {isStudent() && (
                  <div className="CourseGradeRow">
                    <GradeBadge
                      grade={courseGrade?.grade ?? null}
                      maxScore={courseGrade?.max_score ?? null}
                      hasGrades={courseGrade?.has_grades ?? false}
                      gradedAssignments={courseGrade?.graded_assignments ?? 0}
                      totalAssignments={courseGrade?.total_assignments ?? 0}
                      loading={gradesLoading}
                    />
                  </div>
                )}
              </div>
>>>>>>> Stashed changes
            )
          })
        }

        {isTeacher() && <div className="ClassCreateButton" onClick={() => window.location.href = '/classes/create'}>
          <h2>Create Class</h2>
        </div>}
        
        {isAdmin() && <div className="ClassCreateButton" onClick={() => window.location.href = '/admin/create-teacher'}>
          <h2>Create Teacher</h2>
        </div>}
      </div>
    </div>
  )
}
