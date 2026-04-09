import { useEffect, useState } from "react";
import ClassCard from "../components/ClassCard";
import GradeBadge from "../components/GradeBadge";
import CourseSearchBar from "../components/CourseSearchBar";

import './Home.css'
import { listClasses, listAssignments, getStudentGrades } from "../util/api";
import { isTeacher, isAdmin, isStudent } from "../util/login";

export default function Home() {
  const [courses, setCourses] = useState<CourseWithAssignments[]>([]);
  const [loading, setLoading] = useState(true);

  // Dev 5 — grade state
  const [gradeMap, setGradeMap] = useState<Map<number, CourseGrade>>(new Map());
  const [gradesLoading, setGradesLoading] = useState(true);

  // US17 — search state
  const [searchQuery, setSearchQuery] = useState('');

  useEffect(() => {
    ;(async () => {
      try {
        const coursesResp = await listClasses();
        
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
        data.courses.forEach((course: CourseGrade) => {
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

  // US17 — filter courses by search query
  const filteredCourses = courses.filter(c =>
    c.name.toLowerCase().includes(searchQuery.toLowerCase().trim())
  );

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

      {/* US17 — Search bar */}
      <CourseSearchBar
        query={searchQuery}
        onQueryChange={setSearchQuery}
        resultCount={filteredCourses.length}
      />

      {/* US17 — Empty state */}
      {filteredCourses.length === 0 && searchQuery && (
        <p className="Home__empty">No courses match your search.</p>
      )}

      <div className="Classes">
        {
          filteredCourses.map((course) => {
            const assignmentText = `${course.assignmentCount || 0} assignments`;
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