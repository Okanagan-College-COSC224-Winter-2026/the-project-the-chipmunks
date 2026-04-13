import { useEffect, useState } from "react";
import Button from "./Button";
import StatusMessage from "./StatusMessage";
import { teacherSaveConclusion } from "../util/api";

interface Props {
  reviewId: number;
  existingNote?: string;
  onSaved: (note: string) => void;
}

export default function ConclusionForm({ reviewId, existingNote, onSaved }: Props) {
  const [note, setNote] = useState(existingNote || "");
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");

  useEffect(() => {
    setNote(existingNote || "");
  }, [existingNote]);

  const save = async () => {
    if (!note.trim()) {
      setError("Note cannot be empty");
      setSuccess("");
      return;
    }

    try {
      setSaving(true);
      setError("");
      setSuccess("");
      const saved = await teacherSaveConclusion(reviewId, note.trim());
      setNote(saved.note);
      onSaved(saved.note);
      setSuccess("Saved!");
    } catch (err) {
      setError(err instanceof Error ? err.message : "Save failed");
    } finally {
      setSaving(false);
    }
  };

  return (
    <div className="TeacherReviews__noteForm">
      <h3>Instructor Note</h3>

      <textarea
        value={note}
        rows={5}
        placeholder="Write a private instructor note..."
        onChange={(e) => setNote(e.target.value)}
        className="TeacherReviews__textarea"
      />

      <div className="TeacherReviews__noteActions">
        <Button onClick={save} disabled={saving}>
          {saving ? "Saving..." : existingNote ? "Update Note" : "Save Note"}
        </Button>
      </div>

      {error && <StatusMessage message={error} type="error" />}
      {success && <StatusMessage message={success} type="success" />}
    </div>
  );
}