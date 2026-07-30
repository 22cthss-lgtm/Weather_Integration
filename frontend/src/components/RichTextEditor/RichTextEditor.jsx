import { useEffect, useRef, useState } from "react";
import Highlight from "@tiptap/extension-highlight";
import Image from "@tiptap/extension-image";
import Link from "@tiptap/extension-link";
import Placeholder from "@tiptap/extension-placeholder";
import TextAlign from "@tiptap/extension-text-align";
import { Color, FontSize, TextStyle } from "@tiptap/extension-text-style";
import { TableKit } from "@tiptap/extension-table";
import Underline from "@tiptap/extension-underline";
import { EditorContent, useEditor } from "@tiptap/react";
import StarterKit from "@tiptap/starter-kit";

import { uploadFaqImage } from "../../api";
import { normalizeFaqContent } from "../../utils/faqContent";
import ResizableTableView from "./ResizableTableView";
import RichTextToolbar from "./RichTextToolbar";
import TableControls from "./TableControls";
import "./RichTextEditor.css";


export default function RichTextEditor({
  value = "",
  onChange,
  disabled = false,
  placeholder = "Write FAQ content...",
  uploadImage = uploadFaqImage,
}) {
  const fileInputRef = useRef(null);
  const onChangeRef = useRef(onChange);
  const [isUploading, setIsUploading] = useState(false);
  const [uploadError, setUploadError] = useState("");
  onChangeRef.current = onChange;

  const editor = useEditor({
    extensions: [
      StarterKit.configure({ link: false, underline: false }),
      Underline,
      Link.configure({ openOnClick: false, autolink: false, defaultProtocol: "https", HTMLAttributes: { target: "_blank", rel: "noopener noreferrer" } }),
      Image.configure({ allowBase64: false }),
      TextStyle,
      Color,
      FontSize,
      Highlight.configure({ multicolor: true }),
      TextAlign.configure({ types: ["heading", "paragraph"], alignments: ["left", "center", "right"] }),
      TableKit.configure({
        table: {
          resizable: true,
          cellMinWidth: 80,
          handleWidth: 6,
          lastColumnResizable: true,
          View: ResizableTableView,
        },
      }),
      TableControls,
      Placeholder.configure({ placeholder }),
    ],
    content: normalizeFaqContent(value),
    editable: !disabled,
    immediatelyRender: false,
    editorProps: {
      attributes: {
        class: "rte-content",
        role: "textbox",
        "aria-label": "FAQ content",
        "aria-multiline": "true",
      },
    },
    onUpdate: ({ editor: currentEditor }) => onChangeRef.current?.(currentEditor.getHTML()),
  });

  useEffect(() => {
    editor?.setEditable(!disabled);
  }, [disabled, editor]);

  useEffect(() => {
    if (!editor) return;
    const normalized = normalizeFaqContent(value);
    if (normalized !== editor.getHTML() && value !== editor.getHTML()) {
      editor.commands.setContent(normalized, { emitUpdate: false });
    }
  }, [editor, value]);

  async function handleImageSelection(event) {
    const file = event.target.files?.[0];
    event.target.value = "";
    if (!file || !editor) return;
    setIsUploading(true);
    setUploadError("");
    try {
      const result = await uploadImage(file);
      editor.chain().focus().setImage({ src: result.url, alt: file.name }).run();
    } catch (error) {
      setUploadError(error.message || "Image upload failed.");
    } finally {
      setIsUploading(false);
    }
  }

  return (
    <div className={`rte ${disabled ? "is-disabled" : ""}`}>
      <RichTextToolbar editor={editor} disabled={disabled} isUploading={isUploading} onChooseImage={() => fileInputRef.current?.click()} />
      <input ref={fileInputRef} className="rte-file-input" type="file" accept="image/jpeg,image/png,image/webp,image/gif" disabled={disabled || isUploading} onChange={handleImageSelection} />
      <EditorContent editor={editor} />
      {uploadError ? <p className="rte-error" role="alert">{uploadError}</p> : null}
    </div>
  );
}
