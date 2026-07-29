import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom/vitest";
import { afterEach, describe, expect, it, vi } from "vitest";

import FaqPage from "./FaqPage";


const faq = {
  id: 7,
  category: "Guides",
  title: "Rich FAQ",
  summary: "A short summary",
  content: '<h2>Formatted</h2><p><strong>Safe content</strong></p><script>alert(1)</script>',
  tags: ["guide"],
  is_pinned: true,
  created_at: "2026-07-27T10:00:00Z",
  updated_at: "2026-07-27T10:00:00Z",
};

vi.mock("../api", () => ({
  createFaq: vi.fn(),
  deleteFaq: vi.fn(),
  fetchFaq: vi.fn(async () => faq),
  fetchFaqCategories: vi.fn(async () => [{ id: 1, name: "Guides" }]),
  fetchFaqs: vi.fn(async () => [faq]),
  updateFaq: vi.fn(),
  uploadFaqImage: vi.fn(),
}));

afterEach(cleanup);

describe("FaqPage rich content integration", () => {
  it("renders formatted detail HTML through the sanitizer", async () => {
    const { container } = render(<FaqPage />);

    expect(await screen.findByRole("heading", { name: "Formatted" })).toBeInTheDocument();
    expect(screen.getByText("Safe content").tagName).toBe("STRONG");
    expect(container.querySelector("script")).toBeNull();
    expect(container.querySelector(".faq-rich-content")).toBeInTheDocument();
  });

  it("loads fetched content into the shared rich editor in edit mode", async () => {
    render(<FaqPage />);
    await screen.findByText("Safe content");

    await userEvent.click(screen.getByRole("button", { name: "Edit" }));

    const editor = await screen.findByRole("textbox", { name: "FAQ content" });
    await waitFor(() => expect(editor).toHaveTextContent("Formatted"));
    expect(screen.getByRole("toolbar", { name: "Rich text formatting" })).toBeInTheDocument();
  });
});
