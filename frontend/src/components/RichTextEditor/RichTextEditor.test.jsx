import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import { afterEach, describe, expect, it, vi } from "vitest";
import { Editor } from "@tiptap/core";
import { CellSelection } from "@tiptap/pm/tables";
import { TableKit } from "@tiptap/extension-table";
import StarterKit from "@tiptap/starter-kit";

import RichTextEditor from "./RichTextEditor";

afterEach(cleanup);


describe("RichTextEditor", () => {
  it("merges a selected cell range and splits the merged cell", () => {
    const editor = new Editor({
      extensions: [StarterKit, TableKit],
      content: '<table><tbody><tr><td><p>A</p></td><td><p>B</p></td></tr></tbody></table>',
    });
    const cellPositions = [];
    editor.state.doc.descendants((node, position) => {
      if (node.type.name === "tableCell") cellPositions.push(position);
    });
    editor.view.dispatch(editor.state.tr.setSelection(
      CellSelection.create(editor.state.doc, cellPositions[0], cellPositions[1]),
    ));

    expect(editor.can().mergeCells()).toBe(true);
    expect(editor.commands.mergeCells()).toBe(true);
    expect(editor.getHTML()).toContain('colspan="2"');
    expect(editor.can().splitCell()).toBe(true);
    expect(editor.commands.splitCell()).toBe(true);
    expect(editor.getHTML()).not.toContain('colspan="2"');
    expect(editor.getHTML().match(/<td/g)).toHaveLength(2);
    editor.destroy();
  });

  it("loads legacy plain text and exposes accessible toolbar state", async () => {
    render(<RichTextEditor value="Legacy text" onChange={() => {}} placeholder="FAQ body" />);

    await waitFor(() => expect(screen.getByRole("textbox")).toHaveTextContent("Legacy text"));
    expect(screen.getByRole("button", { name: "Bold" })).toHaveAttribute("aria-pressed", "false");
    expect(screen.getByRole("button", { name: "Insert image" })).toBeEnabled();
  });

  it("synchronizes a delayed external value without recreating the editor", async () => {
    const { rerender } = render(<RichTextEditor value="" onChange={() => {}} />);
    const editor = await screen.findByRole("textbox");

    rerender(<RichTextEditor value="<p>Loaded later</p>" onChange={() => {}} />);

    await waitFor(() => expect(editor).toHaveTextContent("Loaded later"));
    expect(screen.getByRole("textbox")).toBe(editor);
  });

  it("disables editing and toolbar controls", async () => {
    render(<RichTextEditor value="<p>Read only</p>" onChange={() => {}} disabled />);

    expect(await screen.findByRole("textbox")).toHaveAttribute("contenteditable", "false");
    expect(screen.getByRole("button", { name: "Bold" })).toBeDisabled();
    expect(screen.getByRole("button", { name: "Insert image" })).toBeDisabled();
  });

  it("uploads an image and inserts its returned URL", async () => {
    const uploadImage = vi.fn().mockResolvedValue({ url: "http://localhost:5174/api/faqs/images/00000000-0000-4000-8000-000000000000.png" });
    const onChange = vi.fn();
    const { container } = render(
      <RichTextEditor value="" onChange={onChange} uploadImage={uploadImage} />,
    );
    const input = container.querySelector('input[type="file"]');
    const file = new File(["image"], "weather.png", { type: "image/png" });

    fireEvent.change(input, { target: { files: [file] } });

    expect(await screen.findByText("Uploading...")).toBeInTheDocument();
    await waitFor(() => expect(uploadImage).toHaveBeenCalledWith(file));
    await waitFor(() => expect(screen.getByRole("textbox").querySelector("img")).toHaveAttribute("src", expect.stringContaining("/api/faqs/images/")));
    expect(onChange).toHaveBeenCalledWith(expect.stringContaining("<img"));
    expect(screen.queryByText("Uploading...")).not.toBeInTheDocument();
  });

  it("shows upload errors and does not insert a broken image", async () => {
    const uploadImage = vi.fn().mockRejectedValue(new Error("Unsupported image"));
    const { container } = render(
      <RichTextEditor value="" onChange={() => {}} uploadImage={uploadImage} />,
    );
    const file = new File(["bad"], "bad.png", { type: "image/png" });

    fireEvent.change(container.querySelector('input[type="file"]'), { target: { files: [file] } });

    expect(await screen.findByRole("alert")).toHaveTextContent("Unsupported image");
    expect(screen.getByRole("textbox").querySelector("img")).toBeNull();
  });

  it("inserts a two by two table with a header row", async () => {
    const onChange = vi.fn();
    render(<RichTextEditor value="" onChange={onChange} />);
    const editor = await screen.findByRole("textbox");

    fireEvent.click(screen.getByRole("button", { name: "Table" }));
    fireEvent.click(screen.getByRole("menuitem", { name: "Insert table" }));

    await waitFor(() => expect(editor.querySelectorAll("table")).toHaveLength(1));
    expect(editor.querySelectorAll("tr")).toHaveLength(2);
    expect(editor.querySelectorAll("tr")[0].querySelectorAll("th")).toHaveLength(2);
    expect(editor.querySelectorAll("tr")[1].querySelectorAll("td")).toHaveLength(2);
    expect(onChange).toHaveBeenCalledWith(expect.stringContaining("<table"));
  });

  it("enables table commands according to the current selection", async () => {
    render(<RichTextEditor value="" onChange={() => {}} />);
    await screen.findByRole("textbox");

    fireEvent.click(screen.getByRole("button", { name: "Table" }));
    expect(screen.getByRole("menuitem", { name: "Insert table" })).toBeEnabled();
    [
      "Add row above", "Add row below", "Delete row", "Add column left",
      "Add column right", "Delete column", "Toggle header row", "Merge cells",
      "Split cell", "Delete table",
    ].forEach((name) => expect(screen.getByRole("menuitem", { name })).toBeDisabled());

    fireEvent.click(screen.getByRole("menuitem", { name: "Insert table" }));
    fireEvent.click(screen.getByRole("button", { name: "Table" }));

    expect(screen.getByRole("menuitem", { name: "Insert table" })).toBeDisabled();
    expect(screen.getByRole("menuitem", { name: "Add row below" })).toBeEnabled();
    expect(screen.getByRole("menuitem", { name: "Add column right" })).toBeEnabled();
    expect(screen.getByRole("menuitem", { name: "Delete table" })).toBeEnabled();
    expect(screen.getByRole("menuitem", { name: "Merge cells" })).toBeDisabled();
    expect(screen.getByRole("menuitem", { name: "Split cell" })).toBeDisabled();
  });

  it("sets whole-table width presets and vertical cell alignment", async () => {
    render(<RichTextEditor value="" onChange={() => {}} />);
    const editor = await screen.findByRole("textbox");
    fireEvent.click(screen.getByRole("button", { name: "Table" }));

    expect(screen.getByRole("menuitem", { name: "Table width 75%" })).toBeDisabled();
    expect(screen.getByRole("menuitem", { name: "Vertical align middle" })).toBeDisabled();
    fireEvent.click(screen.getByRole("menuitem", { name: "Insert table" }));

    fireEvent.click(screen.getByRole("button", { name: "Table" }));
    fireEvent.click(screen.getByRole("menuitem", { name: "Table width 75%" }));
    expect(editor.querySelector("table")).toHaveAttribute("data-table-width", "75");

    fireEvent.click(screen.getByRole("button", { name: "Table" }));
    fireEvent.click(screen.getByRole("menuitem", { name: "Vertical align middle" }));
    expect(editor.querySelector("th")).toHaveAttribute("data-vertical-align", "middle");
  });

  it("modifies rows, columns, and the header row", async () => {
    render(<RichTextEditor value="" onChange={() => {}} />);
    const editor = await screen.findByRole("textbox");
    const chooseTableAction = (name) => {
      fireEvent.click(screen.getByRole("button", { name: "Table" }));
      fireEvent.click(screen.getByRole("menuitem", { name }));
    };

    chooseTableAction("Insert table");
    chooseTableAction("Toggle header row");
    expect(editor.querySelectorAll("th")).toHaveLength(0);
    chooseTableAction("Add row below");
    expect(editor.querySelectorAll("tr")).toHaveLength(3);
    chooseTableAction("Add column right");
    expect(editor.querySelectorAll("tr")[0].children).toHaveLength(3);
    chooseTableAction("Delete row");
    expect(editor.querySelectorAll("tr")).toHaveLength(2);
    chooseTableAction("Delete column");
    expect(editor.querySelectorAll("tr")[0].children).toHaveLength(2);
  });

  it("loads a merged cell for editing", async () => {
    const value =
      '<table><tbody><tr><td colspan="2"><p>Merged</p></td></tr>' +
      '<tr><td><p>A</p></td><td><p>B</p></td></tr></tbody></table>';
    render(<RichTextEditor value={value} onChange={() => {}} />);
    const editor = await screen.findByRole("textbox");

    expect(editor.querySelectorAll("tr")).toHaveLength(2);
    expect(editor.querySelector("td[colspan='2']")).toHaveTextContent("Merged");
  });
});
