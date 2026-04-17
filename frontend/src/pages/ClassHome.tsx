import AssignmentCard from "../components/AssignmentCard"
import Button from "../components/Button"
import "./ClassHome.css"
import { useParams } from "react-router-dom"
import { useState, useEffect } from "react"
import { listAssignments, listClasses, createAssignment, getCourseAnnouncements, createAnnouncement, deleteAnnouncement } from "../util/api"
import TabNavigation from "../components/TabNavigation"
import { importCSV } from "../util/csv"
import Textbox from "../components/Textbox"
import StatusMessage from "../components/StatusMessage"
import { isTeacher, isAdmin } from "../util/login"
import RichTextEditor from "../components/RichTextEditor"
import AnnouncementCard from "../components/AnnouncementCard"
import AnnouncementForm from "../components/AnnouncementForm"
import DatePicker from "react-datepicker"
import "react-datepicker/dist/react-datepicker.css"
import { useNavigate } from 'react-router-dom'

interface Announcement {
  id: number;
  title: string;
  content: string;
  author_name: string;
  created_at: string;
}

export default function ClassHome() {
  const { id } = useParams()
  const idNew = Number(id)
  const [assignments, setAssignments] = useState<Assignment[]>([])
  const [newAssignmentName, setNewAssignmentName] = useState("")
  const [newAssignmentDescription, setNewAssignmentDescription] = useState("")
  const [newAssignmentDueDate, setNewAssignmentDueDate] = useState<Date | null>(null)
  const [className, setClassName] = useState<string | null>(null)
  const [statusMessage, setStatusMessage] = useState("")
  const [statusType, setStatusType] = useState<"error" | "success">("error")
  const [announcements, setAnnouncements] = useState<Announcement[]>([])
  const navigate = useNavigate()

  useEffect(() => {
    (async () => {
      const resp = await listAssignments(String(id))
      const classes = await listClasses()
      const currentClass = classes.find((c: { id: number }) => c.id === Number(id))
      setAssignments(resp)
      setClassName(currentClass?.name || null)

      const annResp = await getCourseAnnouncements(Number(id))
      if (annResp && annResp.ok) {
        const annData = await annResp.json()
        setAnnouncements(annData.announcements)
      }
    })()
  }, [id])

  const tryCreateAssignment = async () => {
    try {
      setStatusMessage("")
      const response = await createAssignment(idNew, newAssignmentName, newAssignmentDescription, newAssignmentDueDate ? newAssignmentDueDate.toISOString() : undefined)
      const createdAssignment = response?.assignment
      if (!createdAssignment?.id) throw new Error("Failed to create assignment")
      setAssignments((prev) => [...prev, createdAssignment])
      setNewAssignmentName("")
      setNewAssignmentDescription("")
      setNewAssignmentDueDate(null)
      setStatusType("success")
      setStatusMessage("Assignment created successfully!")
    } catch (error) {
      console.error("Error creating assignment:", error)
      setStatusType("error")
      setStatusMessage("Error creating assignment.")
    }
  }

  const handlePost = async (title: string, content: string) => {
    const resp = await createAnnouncement(idNew, { title, content })
    if (resp && resp.ok) {
      const data = await resp.json()
      setAnnouncements((prev) => [data.announcement, ...prev])
    }
  }

  const handleDelete = async (announcementId: number) => {
    const resp = await deleteAnnouncement(announcementId)
    if (resp && resp.ok) {
      setAnnouncements((prev) => prev.filter((a) => a.id !== announcementId))
    }
  }

  return (
    <div className="ClassHome">
      <div className="ClassHeader">
        <div className="ClassHeaderLeft">
          <h2>{className}</h2>
        </div>
        <div className="ClassHeaderRight">
          {isTeacher() && (
            <Button onClick={() => importCSV(id as string)}>
              Add Students via CSV
            </Button>
          )}
          {isTeacher() && (
            <Button onClick={() => navigate(`/classes/${id}/progress`)}>
              Student Progress
            </Button>
          )}
        </div>
      </div>

      <TabNavigation
        tabs={[
          { label: "Home",    path: `/classes/${id}/home` },
          { label: "Members", path: `/classes/${id}/members` },
        ]}
      />

      <ul style={{ listStyle: "none", padding: 0, margin: 0 }}>
        {assignments.map((assignment) => (
          <li key={assignment.id}>
            <AssignmentCard id={assignment.id} dueDate={assignment.due_date}>
              {assignment.name}
            </AssignmentCard>
          </li>
        ))}
      </ul>

      {isTeacher() && (
        <div className="NewAssignment">
          <h3>New Assignment</h3>
          <label>Name:</label>
          <Textbox
            onInput={(val) => setNewAssignmentName(val)}
            placeholder="Assignment name"
          />
          <label>Due Date: <span style={{ fontWeight: "normal", fontSize: "0.85rem", color: "var(--text-secondary)" }}>(optional)</span></label>
          <DatePicker
            selected={newAssignmentDueDate}
            onChange={(date: Date | null) => setNewAssignmentDueDate(date)}
            showTimeSelect
            dateFormat="MMMM d, yyyy h:mm aa"
            placeholderText="Select a due date..."
            isClearable
            className="assignment-due-date-input"
            wrapperClassName="assignment-due-date-wrapper"
          />
          <label>Description:</label>
          <RichTextEditor
            value={newAssignmentDescription}
            onChange={setNewAssignmentDescription}
            placeholder="Write assignment instructions..."
          />
          <Button onClick={tryCreateAssignment}>Add</Button>
          <StatusMessage message={statusMessage} type={statusType} />
        </div>
      )}

      <section className="announcements-section">
        <h2>Announcements</h2>
        {isTeacher() && <AnnouncementForm onSubmit={handlePost} />}
        {announcements.map((a) => (
          <AnnouncementCard
            key={a.id}
            id={a.id}
            title={a.title}
            content={a.content}
            author_name={a.author_name}
            created_at={a.created_at}
            canDelete={isTeacher() || isAdmin()}
            onDelete={handleDelete}
          />
        ))}
        {announcements.length === 0 && (
          <p className="announcements-empty">No announcements yet.</p>
        )}
      </section>
    </div>
  )
}
