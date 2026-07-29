import { FONT_SIZES } from "./FontSize";
import { normalizeLinkUrl } from "../../utils/faqContent";


function ToolbarButton({ active = false, children, editor, label, onClick, ...props }) {
  return (
    <button
      type="button"
      aria-label={label}
      aria-pressed={active}
      className={active ? "rte-toolbar-button is-active" : "rte-toolbar-button"}
      disabled={!editor?.isEditable || props.disabled}
      onMouseDown={(event) => event.preventDefault()}
      onClick={onClick}
      title={label}
    >
      {children}
    </button>
  );
}

export default function RichTextToolbar({ editor, disabled, isUploading, onChooseImage }) {
  if (!editor) return null;

  const command = (callback) => () => callback(editor.chain().focus()).run();
  const setLink = () => {
    const currentUrl = editor.getAttributes("link").href || "";
    const enteredUrl = window.prompt(currentUrl ? "Edit link URL" : "Enter link URL", currentUrl);
    if (enteredUrl === null) return;
    const url = normalizeLinkUrl(enteredUrl);
    if (!url) {
      window.alert("Please enter a valid http, https, or email link.");
      return;
    }
    const { empty } = editor.state.selection;
    if (empty) {
      editor.chain().focus().insertContent(`<a href="${url}">${url}</a>`).run();
    } else {
      editor.chain().focus().extendMarkRange("link").setLink({ href: url }).run();
    }
  };
  const clearFormatting = () => {
    editor.chain().focus().unsetAllMarks().clearNodes().unsetTextAlign().run();
  };

  return (
    <div className="rte-toolbar" role="toolbar" aria-label="Rich text formatting">
      <div className="rte-toolbar-group">
        <ToolbarButton editor={editor} label="Bold" active={editor.isActive("bold")} onClick={command((chain) => chain.toggleBold())}><strong>B</strong></ToolbarButton>
        <ToolbarButton editor={editor} label="Italic" active={editor.isActive("italic")} onClick={command((chain) => chain.toggleItalic())}><em>I</em></ToolbarButton>
        <ToolbarButton editor={editor} label="Underline" active={editor.isActive("underline")} onClick={command((chain) => chain.toggleUnderline())}><u>U</u></ToolbarButton>
        <ToolbarButton editor={editor} label="Strikethrough" active={editor.isActive("strike")} onClick={command((chain) => chain.toggleStrike())}><s>S</s></ToolbarButton>
      </div>

      <div className="rte-toolbar-group">
        <select aria-label="Block style" value={editor.isActive("heading", { level: 1 }) ? "h1" : editor.isActive("heading", { level: 2 }) ? "h2" : editor.isActive("heading", { level: 3 }) ? "h3" : "p"} disabled={disabled} onChange={(event) => {
          const value = event.target.value;
          if (value === "p") editor.chain().focus().setParagraph().run();
          else editor.chain().focus().toggleHeading({ level: Number(value.slice(1)) }).run();
        }}>
          <option value="p">Paragraph</option><option value="h1">Heading 1</option><option value="h2">Heading 2</option><option value="h3">Heading 3</option>
        </select>
        <select aria-label="Font size" value={editor.getAttributes("textStyle").fontSize || ""} disabled={disabled} onChange={(event) => {
          const size = event.target.value;
          if (size) editor.chain().focus().setFontSize(size).run();
          else editor.chain().focus().unsetFontSize().run();
        }}>
          <option value="">Default size</option>
          {FONT_SIZES.map((size) => <option value={size} key={size}>{size}</option>)}
        </select>
        <label className="rte-color-control" title="Text color">Text <input type="color" aria-label="Text color" disabled={disabled} value={editor.getAttributes("textStyle").color || "#172033"} onChange={(event) => editor.chain().focus().setColor(event.target.value).run()} /></label>
        <label className="rte-color-control" title="Highlight color">Highlight <input type="color" aria-label="Highlight color" disabled={disabled} value={editor.getAttributes("highlight").color || "#fff3a3"} onChange={(event) => editor.chain().focus().toggleHighlight({ color: event.target.value }).run()} /></label>
      </div>

      <div className="rte-toolbar-group">
        <ToolbarButton editor={editor} label="Bullet list" active={editor.isActive("bulletList")} onClick={command((chain) => chain.toggleBulletList())}>• List</ToolbarButton>
        <ToolbarButton editor={editor} label="Ordered list" active={editor.isActive("orderedList")} onClick={command((chain) => chain.toggleOrderedList())}>1. List</ToolbarButton>
        <ToolbarButton editor={editor} label="Align left" active={editor.isActive({ textAlign: "left" })} onClick={command((chain) => chain.setTextAlign("left"))}>Left</ToolbarButton>
        <ToolbarButton editor={editor} label="Align center" active={editor.isActive({ textAlign: "center" })} onClick={command((chain) => chain.setTextAlign("center"))}>Center</ToolbarButton>
        <ToolbarButton editor={editor} label="Align right" active={editor.isActive({ textAlign: "right" })} onClick={command((chain) => chain.setTextAlign("right"))}>Right</ToolbarButton>
      </div>

      <div className="rte-toolbar-group">
        <ToolbarButton editor={editor} label={editor.isActive("link") ? "Edit link" : "Insert link"} active={editor.isActive("link")} onClick={setLink}>Link</ToolbarButton>
        <ToolbarButton editor={editor} label="Remove link" disabled={!editor.isActive("link")} onClick={command((chain) => chain.extendMarkRange("link").unsetLink())}>Unlink</ToolbarButton>
        <ToolbarButton editor={editor} label="Insert image" disabled={disabled || isUploading} onClick={onChooseImage}>{isUploading ? "Uploading..." : "Image"}</ToolbarButton>
        <ToolbarButton editor={editor} label="Undo" disabled={!editor.can().chain().focus().undo().run()} onClick={command((chain) => chain.undo())}>Undo</ToolbarButton>
        <ToolbarButton editor={editor} label="Redo" disabled={!editor.can().chain().focus().redo().run()} onClick={command((chain) => chain.redo())}>Redo</ToolbarButton>
        <ToolbarButton editor={editor} label="Clear formatting" onClick={clearFormatting}>Clear</ToolbarButton>
      </div>
    </div>
  );
}
