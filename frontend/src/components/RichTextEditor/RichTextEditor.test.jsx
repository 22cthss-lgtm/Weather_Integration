import { cleanup, fireEvent, render, screen, waitFor } from "@testing-library/react";
import "@testing-library/jest-dom/vitest";
import { afterEach, describe, expect, it, vi } from "vitest";

import RichTextEditor from "./RichTextEditor";

afterEach(cleanup);


describe("RichTextEditor", () => {
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
});
