import { Editor } from "@tiptap/core";
import StarterKit from "@tiptap/starter-kit";
import { TableKit } from "@tiptap/extension-table";
import { describe, expect, it } from "vitest";

import TableControls from "./TableControls";
import ResizableTableView from "./ResizableTableView";


describe("ResizableTableView", () => {
  it("renders a whole-table handle and stores a clamped drag width", () => {
    const editor = new Editor({
      element: document.createElement("div"),
      extensions: [
        StarterKit,
        TableKit.configure({ table: { resizable: true, View: ResizableTableView } }),
        TableControls,
      ],
      content: '<table><tbody><tr><td><p>A</p></td><td><p>B</p></td></tr></tbody></table>',
    });
    const wrapper = editor.view.dom.querySelector(".tableWrapper");
    const table = wrapper.querySelector("table");
    const handle = wrapper.querySelector(".rte-table-width-handle");
    wrapper.parentElement.getBoundingClientRect = () => ({ width: 800 });
    table.getBoundingClientRect = () => ({ width: 400 });

    expect(handle).not.toBeNull();
    handle.dispatchEvent(new PointerEvent("pointerdown", { bubbles: true, clientX: 400 }));
    document.dispatchEvent(new PointerEvent("pointermove", { bubbles: true, clientX: 600 }));
    document.dispatchEvent(new PointerEvent("pointerup", { bubbles: true, clientX: 600 }));

    expect(editor.getHTML()).toContain('data-table-width="75"');
    editor.destroy();
  });
});
