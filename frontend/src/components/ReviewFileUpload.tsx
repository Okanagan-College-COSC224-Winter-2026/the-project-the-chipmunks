import { ChangeEvent, useState } from "react";

const ACCEPTED_TYPES = ["application/pdf", "image/png", "image/jpeg", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"];
const ACCEPTED_EXTENSIONS = ".pdf,.png,.jpg,.jpeg,.docx";
const MAX_SIZE_BYTES = 10 * 1024 * 1024; // 10MB

interface Props {
  files: File[];
  onChange: (files: File[]) => void;
}

export default function ReviewFileUpload({ files, onChange }: Props) {
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    setError(null);
    const selected = Array.from(e.target.files ?? []);
    for (const file of selected) {
      if (!ACCEPTED_TYPES.includes(file.type)) {
        setError(`"${file.name}" is not an accepted file type. Allowed: PDF, PNG, JPG, DOCX.`);
        e.target.value = "";
        return;
      }
      if (file.size > MAX_SIZE_BYTES) {
        setError(`"${file.name}" exceeds the 10MB size limit.`);
        e.target.value = "";
        return;
      }
    }
    onChange([...files, ...selected]);
    e.target.value = "";
  };

  const handleRemove = (index: number) => {
    onChange(files.filter((_, i) => i !== index));
  };

  return (
    <div className="review-file-upload">
      <label htmlFor="review-file-input">
        <strong>Attach Files (optional)</strong>
      </label>
      <p style={{ fontSize: "0.85rem", color: "#666" }}>
        Accepted: PDF, PNG, JPG, JPEG, DOCX — Max 10MB each
      </p>
      <input
        id="review-file-input"
        type="file"
        accept={ACCEPTED_EXTENSIONS}
        multiple
        onChange={handleFileChange}
      />
      {error && <p style={{ color: "red" }}>{error}</p>}
      {files.length > 0 && (
        <ul className="attached-files-list">
          {files.map((file, index) => (
            <li key={index}>
              📎 {file.name}{" "}
              <span style={{ fontSize: "0.8rem", color: "#888" }}>
                ({(file.size / 1024).toFixed(1)} KB)
              </span>{" "}
              <button
                type="button"
                onClick={() => handleRemove(index)}
                style={{ color: "red", background: "none", border: "none", cursor: "pointer" }}
              >
                ✕ Remove
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}