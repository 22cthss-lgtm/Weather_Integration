import { Editor } from "@tiptap/core";
import { CellSelection } from "@tiptap/pm/tables";
import StarterKit from "@tiptap/starter-kit";
import { TableKit } from "@tiptap/extension-table";
import { describe, expect, it } from "vitest";

import TableControls, { calculateTableWidthPercent, getSelectedVerticalAlign } from "./TableControls";


function createTableEditor() {
  return new Editor({
    extensions: [StarterKit, TableKit, TableControls],
    content: '<table><tbody><tr><td><p>A</p></td><td><p>B</p></td></tr></tbody></table>',
  });
}

describe("TableControls", () => {
  it("sets controlled whole-table widths and rejects invalid values", () => {
    const editor = createTableEditor();

    expect(editor.commands.setTableWidth("75")).toBe(true);
    expect(editor.getHTML()).toContain('data-table-width="75"');
    expect(editor.getHTML()).toContain("width: 75%");
    expect(editor.commands.setTableWidth("24")).toBe(false);
    expect(editor.getHTML()).toContain('data-table-width="75"');
    expect(editor.commands.setTableWidth("auto")).toBe(true);
    expect(editor.getHTML()).toContain('data-table-width="auto"');
    editor.destroy();
  });

  it("sets vertical alignment across a selected cell range", () => {
    const editor = createTableEditor();
    const positions = [];
    editor.state.doc.descendants((node, position) => {
      if (node.type.name === "tableCell") positions.push(position);
    });
    editor.view.dispatch(editor.state.tr.setSelection(
      CellSelection.create(editor.state.doc, positions[0], positions[1]),
    ));

    expect(editor.commands.setCellVerticalAlign("middle")).toBe(true);
    expect(getSelectedVerticalAlign(editor.state)).toBe("middle");
    expect(editor.getHTML().match(/data-vertical-align="middle"/g)).toHaveLength(2);
    expect(editor.commands.setCellVerticalAlign("sideways")).toBe(false);
    expect(editor.commands.setCellVerticalAlign("bottom")).toBe(true);
    expect(editor.getHTML().match(/data-vertical-align="bottom"/g)).toHaveLength(2);
    editor.destroy();
  });

  it("reports a mixed vertical alignment selection", () => {
    const editor = createTableEditor();
    const positions = [];
    editor.state.doc.descendants((node, position) => {
      if (node.type.name === "tableCell") positions.push(position);
    });
    editor.commands.setCellSelection({ anchorCell: positions[0] });
    editor.commands.setCellVerticalAlign("middle");
    editor.commands.setCellSelection({ anchorCell: positions[0], headCell: positions[1] });

    expect(getSelectedVerticalAlign(editor.state)).toBeNull();
    editor.destroy();
  });

  it("clamps and rounds drag widths", () => {
    expect(calculateTableWidthPercent(300, -500, 800)).toBe(25);
    expect(calculateTableWidthPercent(300, 900, 800)).toBe(100);
    expect(calculateTableWidthPercent(300, 100, 800)).toBe(50);
  });
});
