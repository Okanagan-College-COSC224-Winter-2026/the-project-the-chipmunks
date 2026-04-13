import { useRef, useCallback, useEffect } from "react";
import ReactQuill from "react-quill";
import "react-quill/dist/quill.snow.css";
import "./RichTextEditor.css";

interface Props {
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
}

const MODULES = {
  toolbar: [
    ["bold", "italic", "underline"],
    [{ background: [] }],
    [{ list: "ordered" }, { list: "bullet" }],
    ["clean"],
  ],
};

export default function RichTextEditor({ value, onChange, placeholder }: Props) {
  const quillRef = useRef<any>(null);
  const internalValue = useRef(value);

  const handleChange = useCallback(
    (content: string) => {
      internalValue.current = content;
      onChange(content);
    },
    [onChange]
  );

  // Only push the parent's value into the editor when it genuinely
  // differs from what the editor already has (e.g. a form reset).
  useEffect(() => {
    if (value !== internalValue.current) {
      internalValue.current = value;
      const editor = quillRef.current?.getEditor();
      if (editor) {
        const cursorPos = editor.getSelection()?.index ?? 0;
        editor.clipboard.dangerouslyPasteHTML(value);
        editor.setSelection(cursorPos);
      }
    }
  }, [value]);

  return (
    <div className="RichTextEditor">
      <ReactQuill
        ref={quillRef}
        theme="snow"
        defaultValue={value}
        onChange={handleChange}
        modules={MODULES}
        placeholder={placeholder ?? "Write assignment description..."}
      />
    </div>
  );
}