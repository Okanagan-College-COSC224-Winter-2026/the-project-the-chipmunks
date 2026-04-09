import { useEffect, useState } from 'react';
import { getTeamSubmissions, downloadTeamReviewFile, downloadConclusionFile } from '../util/api';
import StatusMessage from './StatusMessage';
import AvatarInitials from './AvatarInitials';
import './TeamSubmissionsPanel.css';

interface ReviewFileEntry {
  file_id: number;
  filename: string;
  uploaded_at: string;
  size_bytes: number;
}

interface ConclusionFileEntry {
  file_id: number;
  filename: string;
  uploaded_at: string;
}

interface GroupMemberEntry {
  member_id: number;
  member_name: string;
  review_files: ReviewFileEntry[];
  conclusion_files: ConclusionFileEntry[];
}

interface TeamSubmissionsResponse {
  assignment_id: number;
  assignment_name: string;
  group_members: GroupMemberEntry[];
}

interface Props {
  assignmentId: number;
}

function formatDate(iso: string): string {
  return new Date(iso).toLocaleDateString(undefined, {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
  });
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function TeamSubmissionsPanel({ assignmentId }: Props) {
  const [data, setData] = useState<TeamSubmissionsResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [noGroup, setNoGroup] = useState(false);

  useEffect(() => {
    getTeamSubmissions(assignmentId)
      .then((res) => {
        if (res.status === 403) {
          setNoGroup(true);
          setLoading(false);
          return null;
        }
        if (!res.ok) {
          return res.json().then((body) => {
            throw new Error(body?.msg || `Error ${res.status}`);
          });
        }
        return res.json();
      })
      .then((json) => {
        if (json) {
          setData(json);
        }
        setLoading(false);
      })
      .catch((err: Error) => {
        setError(err.message || 'Failed to load team submissions.');
        setLoading(false);
      });
  }, [assignmentId]);

  if (loading) return <p>Loading team submissions...</p>;
  if (error) return <StatusMessage type="error" message={error} />;

  if (noGroup) {
    return (
      <div className="tsub-empty">
        <p>You are not assigned to a group for this assignment yet.</p>
      </div>
    );
  }

  if (!data) return null;

  const hasAnyFiles = data.group_members.some(
    (m) => m.review_files.length > 0 || m.conclusion_files.length > 0
  );

  return (
    <div className="tsub-panel">
      <h2 className="tsub-heading">Team Submissions</h2>
      <p className="tsub-subheading">
        Files submitted by your group members for{' '}
        <strong>{data.assignment_name}</strong>.
      </p>

      {!hasAnyFiles ? (
        <div className="tsub-empty">
          <p>No files submitted by your group members yet.</p>
        </div>
      ) : (
        <div className="tsub-members">
          {data.group_members.map((member) => {
            const totalFiles =
              member.review_files.length + member.conclusion_files.length;
            return (
              <div key={member.member_id} className="tsub-card">
                <div className="tsub-card-header">
                  <AvatarInitials
                    firstName={member.member_name.split(' ')[0]}
                    lastName={member.member_name.split(' ').slice(1).join(' ')}
                  />
                  <div className="tsub-card-info">
                    <span className="tsub-member-name">{member.member_name}</span>
                    <span className="tsub-file-count">
                      {totalFiles} file{totalFiles !== 1 ? 's' : ''}
                    </span>
                  </div>
                </div>

                {totalFiles === 0 ? (
                  <p className="tsub-no-files">No files uploaded yet.</p>
                ) : (
                  <div className="tsub-file-list">
                    {member.review_files.map((file) => (
                      <div key={`rv-${file.file_id}`} className="tsub-file-row">
                        <div className="tsub-file-meta">
                          <span className="tsub-file-name">{file.filename}</span>
                          <span className="tsub-file-detail">
                            {formatDate(file.uploaded_at)} &middot;{' '}
                            {formatBytes(file.size_bytes)}
                          </span>
                        </div>
                        <button
                          className="tsub-download-btn"
                          onClick={() => downloadTeamReviewFile(file.file_id)}
                        >
                          Download
                        </button>
                      </div>
                    ))}

                    {member.conclusion_files.map((file) => (
                      <div key={`cf-${file.file_id}`} className="tsub-file-row tsub-file-row--conclusion">
                        <div className="tsub-file-meta">
                          <span className="tsub-file-name">{file.filename}</span>
                          <span className="tsub-file-detail">
                            {formatDate(file.uploaded_at)} &middot; Conclusion
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
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}