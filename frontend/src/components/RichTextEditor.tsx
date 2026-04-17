import ReactQuill from "react-quill";
import "react-quill/dist/quill.snow.css";
import "./RichTextEditor.css";

interface Props {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}

// Must be defined outside the component — a new object reference on every
// render causes ReactQuill to remount its toolbar and drop active formats.
const MODULES = {
  toolbar: [
    ["bold", "italic", "underline"],
    [{ background: [] }],
    [{ list: "ordered" }, { list: "bullet" }],
    ["clean"],
  ],
};

// Do NOT pass a `formats` prop — Quill's explicit format restriction
// interferes with bold+italic active-state detection and causes one to
// be dropped when both are applied. The snow theme supports all standard
// formats natively without needing to declare them.

export default function RichTextEditor({ value, onChange, placeholder }: Props) {
  return (
    <div className="RichTextEditor">
      <ReactQuill
        theme="snow"
        value={value}
        onChange={onChange}
        modules={MODULES}
        placeholder={placeholder ?? "Write assignment description..."}
      />
    </div>
  );
}
