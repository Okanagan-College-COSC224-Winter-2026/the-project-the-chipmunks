import { useEffect, useState } from "react";
import { useParams } from "react-router-dom";
import { getReview, getReviewFiles, downloadReviewFile } from "../util/api";
import { getUserId } from "../util/api";

interface ReviewFile {
  file_id: number;
  filename: string;
  uploaded_at: string;
  size: string;
}

export default function Feedback() {
  const { assignmentId, revieweeId } = useParams();
  const [, setReviewId] = useState<number | null>(null);
  const [files, setFiles] = useState<ReviewFile[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    (async () => {
      try {
        const stuID = await getUserId();
        const reviewResponse = await getReview(
          Number(assignmentId),
          stuID,
          Number(revieweeId)
        );
        const reviewData = await reviewResponse.json();
        setReviewId(reviewData.id);
        const filesData = await getReviewFiles(reviewData.id);
        setFiles(filesData.files ?? []);
      } catch (err) {
        console.error("Error loading feedback:", err);
        setError("Failed to load feedback or files.");
      } finally {
        setLoading(false);
      }
    })();
  }, [assignmentId, revieweeId]);

  if (loading) return <p>Loading feedback...</p>;
  if (error) return <p style={{ color: "red" }}>{error}</p>;

  return (
    <div className="feedback-page">
      <h1>Feedback</h1>
      {files.length === 0 ? (
        <p>No files were attached to this review.</p>
      ) : (
        <>
          <h3>📎 Attached Files</h3>
          <ul>
            {files.map((file) => (
              <li key={file.file_id}>
                <a
                  href={downloadReviewFile(file.file_id)}
                  target="_blank"
                  rel="noreferrer"
                >
                  {file.filename}
                </a>{" "}
                <span style={{ fontSize: "0.8rem", color: "#888" }}>
                  ({file.size} — {new Date(file.uploaded_at).toLocaleDateString()})
                </span>
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  );
}