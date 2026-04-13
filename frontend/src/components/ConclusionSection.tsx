/**
 * ConclusionSection.tsx — Dev 5 (Feature B: File Attachments on Reviews & Conclusions)
 *
 * Displays on the Assignment detail page:
 * - Teachers: can upload conclusion/summary files after review period
 * - Students: can see and download uploaded conclusion files
 *
 * Reuses FileUpload component from Feature A for the upload UI.
 *
 * Place in: frontend/src/components/ConclusionSection.tsx
 */

import { useState, useEffect } from "react";
import FileUpload from "./FileUpload";
import {
  uploadConclusionFile,
  listConclusionFiles,
  downloadConclusionFile,
} from "../util/api";
import { isTeacher } from "../util/login";
import "./ConclusionSection.css";

interface ConclusionFileData {
  file_id: number;
  filename: string;
  uploaded_at: string | null;
  teacher: string | null;
}

interface ConclusionSectionProps {
  assignmentId: number;
}

export default function ConclusionSection({
  assignmentId,
}: ConclusionSectionProps) {
  const [files, setFiles] = useState<ConclusionFileData[]>([]);
  const [loading, setLoading] = useState(true);
  const [isUploading, setIsUploading] = useState(false);
  const [downloadingId, setDownloadingId] = useState<number | null>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [statusMessage, setStatusMessage] = useState("");
  const [statusType, setStatusType] = useState<"success" | "error" | "">("");

  // Fetch existing conclusion files on mount
  useEffect(() => {
    (async () => {
      try {
        const data = await listConclusionFiles(assignmentId);
        setFiles(data.files || []);
      } catch {
        // No conclusion files yet or endpoint not available
        setFiles([]);
      } finally {
        setLoading(false);
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
      const result = await uploadConclusionFile(assignmentId, selectedFile);

      // Add the new file to the list without refetching
      const newFile: ConclusionFileData = {
        file_id: result.file_id,
        filename: result.filename,
        uploaded_at: new Date().toISOString(),
        teacher: null, // Will show on next fetch
      };
      setFiles((prev) => [newFile, ...prev]);
      setSelectedFile(null);
      setStatusMessage(`"${result.filename}" uploaded successfully!`);
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

  // eslint-disable-next-line @typescript-eslint/no-unused-vars
  const handleDownload = async (fileId: number, _filename: string) => {
    setDownloadingId(fileId);
    try {
      await downloadConclusionFile(assignmentId, fileId);
    } catch (error) {
      setStatusMessage(
        error instanceof Error ? error.message : "Download failed."
      );
      setStatusType("error");
    } finally {
      setDownloadingId(null);
    }
  };

  const formatDate = (dateStr: string | null): string => {
    if (!dateStr) return "";
    const date = new Date(dateStr);
    return date.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
      hour: "numeric",
      minute: "2-digit",
    });
  };

  // Don't show the section at all while loading
  if (loading) {
    return (
      <div className="conclusion-section">
        <h3>Conclusion Files</h3>
        <p className="conclusion-loading">Loading...</p>
      </div>
    );
  }

  // If student and no files, show a simple message
  if (!isTeacher() && files.length === 0) {
    return (
      <div className="conclusion-section">
        <h3>Conclusion Files</h3>
        <p className="conclusion-empty">
          No conclusion files have been uploaded for this assignment yet.
        </p>
      </div>
    );
  }

  return (
    <div className="conclusion-section">
      <h3>Conclusion Files</h3>

      {/* File list — visible to everyone */}
      {files.length > 0 && (
        <div className="conclusion-file-list">
          {files.map((file) => (
            <div key={file.file_id} className="conclusion-file-row">
              <span className="conclusion-file-icon">📄</span>
              <div className="conclusion-file-info">
                <span className="conclusion-file-name">{file.filename}</span>
                <span className="conclusion-file-meta">
                  {file.teacher && `Uploaded by ${file.teacher}`}
                  {file.teacher && file.uploaded_at && " · "}
                  {file.uploaded_at && formatDate(file.uploaded_at)}
                </span>
              </div>
              <button
                className="conclusion-download-btn"
                onClick={() => handleDownload(file.file_id, file.filename)}
                disabled={downloadingId === file.file_id}
              >
                {downloadingId === file.file_id ? "Downloading..." : "Download"}
              </button>
            </div>
          ))}
        </div>
      )}

      {/* Upload section — teachers only */}
      {isTeacher() && (
        <div className="conclusion-upload-section">
          <FileUpload
            onFileSelect={handleFileSelect}
            onFileRemove={handleFileRemove}
            accept="application/pdf,image/png,image/jpeg,.docx,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            isUploading={isUploading}
            statusMessage={statusMessage}
            statusType={statusType}
            label="Upload a conclusion file"
          />

          {selectedFile && !isUploading && (
            <button className="conclusion-upload-btn" onClick={handleUpload}>
              Upload Conclusion File
            </button>
          )}
        </div>
      )}

      {/* Status message for download errors */}
      {statusMessage && !selectedFile && statusType === "error" && (
        <div className="conclusion-status error">{statusMessage}</div>
      )}
    </div>
  );
}
