/**
 * AssignmentAttachment.tsx — Dev 5 (Feature A: Enhanced Assignment Management)
 *
 * Displays the file attachment section on the Assignment detail page.
 * - Teachers: see FileUpload component + existing attachment with delete option
 * - Students: see download link if an attachment exists
 *
 * Place in: frontend/src/components/AssignmentAttachment.tsx
 */

import { useState, useEffect } from "react";
import FileUpload from "./FileUpload";
import {
  uploadAssignmentFile,
  downloadAssignmentAttachment,
  deleteAssignmentAttachment,
  getAssignment,
} from "../util/api";
import { isTeacher } from "../util/login";
import "./AssignmentAttachment.css";

interface AssignmentAttachmentProps {
  assignmentId: number;
}

export default function AssignmentAttachment({
  assignmentId,
}: AssignmentAttachmentProps) {
  const [attachmentFilename, setAttachmentFilename] = useState<string | null>(
    null
  );
  const [isUploading, setIsUploading] = useState(false);
  const [isDeleting, setIsDeleting] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);
  const [statusMessage, setStatusMessage] = useState("");
  const [statusType, setStatusType] = useState<"success" | "error" | "">("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);

  // Fetch assignment details to check for existing attachment
  useEffect(() => {
    (async () => {
      try {
        const assignment = await getAssignment(assignmentId);
        if (assignment.attachment_filename) {
          setAttachmentFilename(assignment.attachment_filename);
        }
      } catch {
        // Assignment fetch failed — attachment info unavailable
      }
    })();
  }, [assignmentId]);

  const handleFileSelect = (file: File) => {
    setSelectedFile(file);
    setStatusMessage("");
    setStatusType("");
  };

  const handleFileRemove = () => {
    setSelectedFile(null);
    setStatusMessage("");
    setStatusType("");
  };

  const handleUpload = async () => {
    if (!selectedFile) return;

    setIsUploading(true);
    setStatusMessage("");
    setStatusType("");

    try {
      const result = await uploadAssignmentFile(assignmentId, selectedFile);
      setAttachmentFilename(result.filename);
      setSelectedFile(null);
      setStatusMessage(`File "${result.filename}" uploaded successfully!`);
      setStatusType("success");
    } catch (error) {
      setStatusMessage(
        error instanceof Error ? error.message : "Upload failed."
      );
      setStatusType("error");
    } finally {
      setIsUploading(false);
    }
  };

  const handleDownload = async () => {
    if (!attachmentFilename) return;

    setIsDownloading(true);
    try {
      await downloadAssignmentAttachment(assignmentId, attachmentFilename);
    } catch (error) {
      setStatusMessage(
        error instanceof Error ? error.message : "Download failed."
      );
      setStatusType("error");
    } finally {
      setIsDownloading(false);
    }
  };

  const handleDelete = async () => {
    if (!attachmentFilename) return;

    const confirmed = window.confirm(
      `Remove attachment "${attachmentFilename}"?`
    );
    if (!confirmed) return;

    setIsDeleting(true);
    try {
      await deleteAssignmentAttachment(assignmentId);
      setAttachmentFilename(null);
      setStatusMessage("Attachment removed.");
      setStatusType("success");
    } catch (error) {
      setStatusMessage(
        error instanceof Error ? error.message : "Delete failed."
      );
      setStatusType("error");
    } finally {
      setIsDeleting(false);
    }
  };

  return (
    <div className="assignment-attachment">
      <h3>Attachment</h3>

      {/* Existing attachment — visible to everyone */}
      {attachmentFilename && (
        <div className="attachment-existing">
          <div className="attachment-file-row">
            <span className="attachment-file-icon">📄</span>
            <span className="attachment-file-name">{attachmentFilename}</span>
            <button
              className="attachment-download-btn"
              onClick={handleDownload}
              disabled={isDownloading}
            >
              {isDownloading ? "Downloading..." : "Download"}
            </button>
            {isTeacher() && (
              <button
                className="attachment-delete-btn"
                onClick={handleDelete}
                disabled={isDeleting}
              >
                {isDeleting ? "Removing..." : "Remove"}
              </button>
            )}
          </div>
        </div>
      )}

      {/* Upload section — teachers only */}
      {isTeacher() && !attachmentFilename && (
        <div className="attachment-upload-section">
          <FileUpload
            onFileSelect={handleFileSelect}
            onFileRemove={handleFileRemove}
            isUploading={isUploading}
            statusMessage={statusMessage}
            statusType={statusType}
            label="Attach a PDF to this assignment"
          />

          {selectedFile && !isUploading && (
            <button className="attachment-upload-btn" onClick={handleUpload}>
              Upload Attachment
            </button>
          )}
        </div>
      )}

      {/* Status for non-upload actions (download/delete) */}
      {!isTeacher() && !attachmentFilename && (
        <p className="attachment-none">No attachment for this assignment.</p>
      )}

      {/* Status messages for delete/download (upload has its own via FileUpload) */}
      {statusMessage && !selectedFile && attachmentFilename === null && isTeacher() && (
        <div className={`file-upload-status ${statusType}`}>
          {statusMessage}
        </div>
      )}
    </div>
  );
}
