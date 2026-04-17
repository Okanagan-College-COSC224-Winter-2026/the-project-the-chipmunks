import { useEffect, useState } from 'react';
import { getTeamSubmissions, downloadSubmission, downloadConclusionFile } from '../util/api';
import StatusMessage from './StatusMessage';
import AvatarInitials from './AvatarInitials';
import './TeamSubmissionsPanel.css';

interface SubmissionEntry {
  id: number;
  filename: string;
  uploaded_at: string;
  is_mine: boolean;
}

interface ConclusionFileEntry {
  file_id: number;
  filename: string;
  uploaded_at: string;
}

interface GroupMemberEntry {
  member_id: number;
  member_name: string;
  is_self: boolean;
  individual_submissions: SubmissionEntry[];
}

interface TeamSubmissionsResponse {
  assignment_id: number;
  assignment_name: string;
  group_members: GroupMemberEntry[];
  group_submissions: SubmissionEntry[];
  conclusion_files: ConclusionFileEntry[];
}

interface Props {
  assignmentId: number;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, {
    year: 'numeric', month: 'short', day: 'numeric',
  });
}

export default function TeamSubmissionsPanel({ assignmentId }: Props) {
  const [data, setData] = useState<TeamSubmissionsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [noGroup, setNoGroup] = useState(false);

  useEffect(() => {
    getTeamSubmissions(assignmentId)
      .then((res) => {
        if (res.status === 403) { setNoGroup(true); setLoading(false); return null; }
        if (!res.ok) return res.json().then((b) => { throw new Error(b?.msg || `Error ${res.status}`); });
        return res.json();
      })
      .then((json) => { if (json) setData(json); setLoading(false); })
      .catch((err: Error) => { setError(err.message); setLoading(false); });
  }, [assignmentId]);

  if (loading) return <p>Loading team submissions...</p>;
  if (error) return <StatusMessage type="error" message={error} />;
  if (noGroup) return (
    <div className="tsub-empty">
      <p>You are not assigned to a group for this assignment yet.</p>
    </div>
  );
  if (!data) return null;

  const hasGroupSubs = data.group_submissions.length > 0;
  const hasAnySubs = hasGroupSubs || data.group_members.some(m => m.individual_submissions.length > 0);
  const hasConclusionFiles = data.conclusion_files.length > 0;

  return (
    <div className="tsub-panel">
      <h2 className="tsub-heading">Team Submissions</h2>
      <p className="tsub-subheading">
        Submitted files for <strong>{data.assignment_name}</strong>.
      </p>

      {/* ── Group submissions ─────────────────────────── */}
      {hasGroupSubs && (
        <div className="tsub-group-section">
          <h3 className="tsub-section-heading">Group Submission</h3>
          <div className="tsub-file-list">
            {data.group_submissions.map((sub) => (
              <div key={`gs-${sub.id}`} className="tsub-file-row tsub-file-row--group">
                <div className="tsub-file-meta">
                  <span className="tsub-file-name">{sub.filename}</span>
                  <span className="tsub-file-detail">{formatDate(sub.uploaded_at)}</span>
                </div>
                <button
                  className="tsub-download-btn"
                  onClick={() => downloadSubmission(data.assignment_id, sub.id, sub.filename)}
                >
                  Download
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── Individual submissions per member ─────────── */}
      {!hasAnySubs ? (
        <div className="tsub-empty"><p>No submissions yet.</p></div>
      ) : (
        <div className="tsub-members">
          {data.group_members.map((member) => (
            <div key={member.member_id} className="tsub-card">
              <div className="tsub-card-header">
                <AvatarInitials
                  firstName={member.member_name.split(' ')[0]}
                  lastName={member.member_name.split(' ').slice(1).join(' ')}
                />
                <div className="tsub-card-info">
                  <span className="tsub-member-name">
                    {member.member_name}
                    {member.is_self && <span className="tsub-you-badge"> (You)</span>}
                  </span>
                  <span className="tsub-file-count">
                    {member.individual_submissions.length} individual file
                    {member.individual_submissions.length !== 1 ? 's' : ''}
                  </span>
                </div>
              </div>

              {member.individual_submissions.length === 0 ? (
                <p className="tsub-no-files">No individual submission yet.</p>
              ) : (
                <div className="tsub-file-list">
                  {member.individual_submissions.map((sub) => (
                    <div key={`is-${sub.id}`} className="tsub-file-row">
                      <div className="tsub-file-meta">
                        <span className="tsub-file-name">{sub.filename}</span>
                        <span className="tsub-file-detail">{formatDate(sub.uploaded_at)}</span>
                      </div>
                      <button
                        className="tsub-download-btn"
                        onClick={() => downloadSubmission(data.assignment_id, sub.id, sub.filename)}
                      >
                        Download
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* ── Teacher conclusion files ──────────────────── */}
      {hasConclusionFiles && (
        <div className="tsub-conclusion-section">
          <h3 className="tsub-conclusion-heading">Teacher Conclusion Files</h3>
          <div className="tsub-file-list">
            {data.conclusion_files.map((file) => (
              <div key={`cf-${file.file_id}`} className="tsub-file-row tsub-file-row--conclusion">
                <div className="tsub-file-meta">
                  <span className="tsub-file-name">{file.filename}</span>
                  <span className="tsub-file-detail">
                    {formatDate(file.uploaded_at)} · Conclusion
                  </span>
                </div>
                <button
                  className="tsub-download-btn"
                  onClick={() => downloadConclusionFile(assignmentId, file.file_id)}
                >
                  Download
                </button>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
