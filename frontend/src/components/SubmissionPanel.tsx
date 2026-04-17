import { useEffect, useState, useRef } from 'react';
import {
  getSubmissionStatus,
  uploadSubmission,
  deleteSubmission,
  downloadSubmission,
} from '../util/api';
import StatusMessage from './StatusMessage';
import './SubmissionPanel.css';

interface SubmissionEntry {
  id: number;
  filename: string;
  uploaded_at: string;
  uploaded_by?: string;
  is_mine: boolean;
}

interface StatusResponse {
  assignment_id: number;
  group_id: number | null;
  individual_submissions: SubmissionEntry[];
  group_submissions: SubmissionEntry[];
}

interface Props {
  assignmentId: number;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, {
    month: 'short', day: 'numeric', year: 'numeric',
  });
}

export default function SubmissionPanel({ assignmentId }: Props) {
  const [status, setStatus] = useState<StatusResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [mode, setMode] = useState<'individual' | 'group'>('individual');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [feedback, setFeedback] = useState<string>('');
  const [feedbackType, setFeedbackType] = useState<'success' | 'error'>('error');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const load = async () => {
    try {
      const data = await getSubmissionStatus(assignmentId);
      setStatus(data);
    } catch {
      // silently ignore — group_id null means no group
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, [assignmentId]);

  const activeSubmissions =
    mode === 'individual'
      ? (status?.individual_submissions ?? [])
      : (status?.group_submissions ?? []);

  const isSubmitted = activeSubmissions.length > 0;

  const handleUpload = async () => {
    if (!selectedFile) return;
    if (mode === 'group' && !status?.group_id) {
      setFeedbackType('error');
      setFeedback('You are not in a group for this assignment.');
      return;
    }
    setUploading(true);
    setFeedback('');
    try {
      await uploadSubmission(assignmentId, selectedFile, mode);
      setSelectedFile(null);
      if (fileInputRef.current) fileInputRef.current.value = '';
      setFeedbackType('success');
      setFeedback('Submission uploaded successfully!');
      await load();
    } catch (err) {
      setFeedbackType('error');
      setFeedback(err instanceof Error ? err.message : 'Upload failed.');
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (sub: SubmissionEntry) => {
    if (!window.confirm(`Remove "${sub.filename}"?`)) return;
    try {
      await deleteSubmission(assignmentId, sub.id);
      setFeedbackType('success');
      setFeedback('Submission removed.');
      await load();
    } catch (err) {
      setFeedbackType('error');
      setFeedback(err instanceof Error ? err.message : 'Delete failed.');
    }
  };

  if (loading) return <p style={{ padding: '12px' }}>Loading...</p>;

  return (
    <div className="subpanel">

      {/* ── Status banner ─────────────────────────────── */}
      <div className={`subpanel__status ${isSubmitted ? 'subpanel__status--submitted' : 'subpanel__status--pending'}`}>
        <span className="subpanel__status-icon">{isSubmitted ? '✓' : '○'}</span>
        <span className="subpanel__status-label">
          {isSubmitted ? 'Submitted' : 'Pending — no submission yet'}
        </span>
      </div>

      {/* ── Mode toggle ───────────────────────────────── */}
      <div className="subpanel__toggle">
        <button
          className={`subpanel__toggle-btn ${mode === 'individual' ? 'subpanel__toggle-btn--active' : ''}`}
          onClick={() => { setMode('individual'); setFeedback(''); }}
        >
          Individual
        </button>
        <button
          className={`subpanel__toggle-btn ${mode === 'group' ? 'subpanel__toggle-btn--active' : ''}`}
          onClick={() => { setMode('group'); setFeedback(''); }}
          disabled={!status?.group_id}
          title={!status?.group_id ? 'You are not in a group for this assignment' : ''}
        >
          Group
        </button>
      </div>
      {mode === 'group' && !status?.group_id && (
        <p className="subpanel__hint">
          You need to be assigned to a group to use group submissions.
        </p>
      )}
      {mode === 'group' && status?.group_id && (
        <p className="subpanel__hint">
          Group submissions are visible to all members of your group.
        </p>
      )}

      {/* ── Existing submissions ──────────────────────── */}
      {activeSubmissions.length > 0 && (
        <div className="subpanel__files">
          {activeSubmissions.map((sub) => (
            <div key={sub.id} className="subpanel__file-row">
              <div className="subpanel__file-info">
                <span className="subpanel__file-name">{sub.filename}</span>
                <span className="subpanel__file-meta">
                  {formatDate(sub.uploaded_at)}
                  {sub.uploaded_by && mode === 'group' && ` · ${sub.uploaded_by}`}
                </span>
              </div>
              <div className="subpanel__file-actions">
                <button
                  className="subpanel__btn subpanel__btn--download"
                  onClick={() => downloadSubmission(assignmentId, sub.id, sub.filename)}
                >
                  Download
                </button>
                {sub.is_mine && (
                  <button
                    className="subpanel__btn subpanel__btn--remove"
                    onClick={() => handleDelete(sub)}
                  >
                    Remove
                  </button>
                )}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* ── Upload ───────────────────────────────────── */}
      <div className="subpanel__upload">
        <label className="subpanel__upload-label">
          {isSubmitted ? 'Add another file:' : 'Upload your submission:'}
        </label>
        <div className="subpanel__upload-row">
          <input
            ref={fileInputRef}
            type="file"
            accept=".pdf,.png,.jpg,.jpeg,.docx,.zip"
            onChange={(e) => setSelectedFile(e.target.files?.[0] ?? null)}
            className="subpanel__file-input"
          />
          <button
            className="subpanel__btn subpanel__btn--submit"
            onClick={handleUpload}
            disabled={!selectedFile || uploading}
          >
            {uploading ? 'Uploading...' : 'Submit'}
          </button>
        </div>
        <p className="subpanel__hint">Accepted: PDF, PNG, JPG, DOCX, ZIP · Max 10MB</p>
      </div>

      {feedback && <StatusMessage message={feedback} type={feedbackType} />}
    </div>
  );
}
