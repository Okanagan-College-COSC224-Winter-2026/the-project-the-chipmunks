import ReactQuill from "react-quill";
import "react-quill/dist/quill.snow.css";
import "./RichTextEditor.css";

interface Props {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}

const TOOLBAR = [
  ["bold", "italic", "underline"],
  [{ background: [] }],
  [{ list: "ordered" }, { list: "bullet" }],
  ["clean"],
];

export default function RichTextEditor({ value, onChange, placeholder }: Props) {
  return (
    <div className="RichTextEditor">
      <ReactQuill
        theme="snow"
        value={value}
        onChange={onChange}
        modules={{ toolbar: TOOLBAR }}
        placeholder={placeholder ?? "Write assignment description..."}
      />
    </div>
  );
}
