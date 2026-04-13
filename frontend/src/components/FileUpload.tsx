/**
 * FileUpload.tsx — Dev 5 (Feature A: Enhanced Assignment Management)
 *
 * Reusable file upload component with drag-and-drop or click-to-upload.
 * Validates PDF-only, enforces 10MB size limit client-side.
 * Displays file name/size after selection, with loading/error/success states.
 *
 * Place in: frontend/src/components/FileUpload.tsx
 */

import { useState, useRef, DragEvent, ChangeEvent } from "react";
import "./FileUpload.css";

interface FileUploadProps {
  /** Called after a valid file is selected (not yet uploaded) */
  onFileSelect: (file: File) => void;
  /** Called when user removes the selected file */
  onFileRemove?: () => void;
  /** Accepted file types (MIME). Defaults to PDF only */
  accept?: string;
  /** Max file size in bytes. Defaults to 10MB */
  maxSize?: number;
  /** Whether an upload is currently in progress */
  isUploading?: boolean;
  /** Upload status message (success or error) */
  statusMessage?: string;
  /** Status type for styling */
  statusType?: "success" | "error" | "";
  /** Label for the upload area */
  label?: string;
}

const DEFAULT_MAX_SIZE = 10 * 1024 * 1024; // 10MB

function formatFileSize(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

export default function FileUpload({
  onFileSelect,
  onFileRemove,
  accept = "application/pdf",
  maxSize = DEFAULT_MAX_SIZE,
  isUploading = false,
  statusMessage = "",
  statusType = "",
  label = "Upload PDF Attachment",
}: FileUploadProps) {
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [isDragOver, setIsDragOver] = useState(false);
  const [validationError, setValidationError] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const validateFile = (file: File): string => {
    // Check file type
    const acceptedTypes = accept.split(",").map((t) => t.trim());
    const isValidType = acceptedTypes.some((type) => {
      if (type.startsWith(".")) {
        return file.name.toLowerCase().endsWith(type);
      }
      return file.type === type;
    });

    if (!isValidType) {
      return "Only PDF files are accepted.";
    }

    // Check file size
    if (file.size > maxSize) {
      return `File size exceeds ${formatFileSize(maxSize)} limit.`;
    }

    return "";
  };

  const handleFile = (file: File) => {
    const error = validateFile(file);
    setValidationError(error);

    if (!error) {
      setSelectedFile(file);
      onFileSelect(file);
    }
  };

  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(true);
  };

  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(false);
  };

  const handleDrop = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault();
    setIsDragOver(false);

    const file = e.dataTransfer.files[0];
    if (file) {
      handleFile(file);
    }
  };

  const handleInputChange = (e: ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      handleFile(file);
    }
  };

  const handleRemove = () => {
    setSelectedFile(null);
    setValidationError("");
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
    onFileRemove?.();
  };

  const handleClick = () => {
    if (!selectedFile && !isUploading) {
      fileInputRef.current?.click();
    }
  };

  return (
    <div className="file-upload-wrapper">
      <label className="file-upload-label">{label}</label>

      <div
        className={`file-upload-dropzone ${isDragOver ? "drag-over" : ""} ${selectedFile ? "has-file" : ""} ${isUploading ? "uploading" : ""}`}
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={handleClick}
      >
        <input
          ref={fileInputRef}
          type="file"
          accept={accept}
          onChange={handleInputChange}
          className="file-upload-input"
        />

        {isUploading ? (
          <div className="file-upload-loading">
            <div className="file-upload-spinner"></div>
            <span>Uploading...</span>
          </div>
        ) : selectedFile ? (
          <div className="file-upload-selected">
            <div className="file-upload-icon">📄</div>
            <div className="file-upload-info">
              <span className="file-upload-name">{selectedFile.name}</span>
              <span className="file-upload-size">
                {formatFileSize(selectedFile.size)}
              </span>
            </div>
            <button
              type="button"
              className="file-upload-remove"
              onClick={(e) => {
                e.stopPropagation();
                handleRemove();
              }}
              title="Remove file"
            >
              ✕
            </button>
          </div>
        ) : (
          <div className="file-upload-placeholder">
            <div className="file-upload-icon">📎</div>
            <span>Drag & drop a PDF here, or click to select</span>
            <span className="file-upload-hint">
              Maximum file size: {formatFileSize(maxSize)}
            </span>
          </div>
        )}
      </div>

      {validationError && (
        <div className="file-upload-error">{validationError}</div>
      )}

      {statusMessage && (
        <div className={`file-upload-status ${statusType}`}>
          {statusMessage}
        </div>
      )}
    </div>
  );
}
