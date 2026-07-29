import { cleanup, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import "@testing-library/jest-dom/vitest";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import * as api from "../api";
import FaqPage from "./FaqPage";

vi.mock("../api", () => ({
  createFaq: vi.fn(),
  deleteFaq: vi.fn(),
  fetchFaq: vi.fn(),
  fetchFaqCategories: vi.fn(),
  fetchFaqs: vi.fn(),
  updateFaq: vi.fn(),
  uploadFaqImage: vi.fn(),
}));

const articles = [
  {
    id: 7,
    category: "Guides",
    title: "Rich FAQ",
    summary: "A short summary",
    content: '<h2>Formatted</h2><p><strong>Safe content</strong></p><img src="http://localhost:5174/api/faqs/images/00000000-0000-4000-8000-000000000000.png" alt="Forecast map"><script>alert(1)</script>',
    tags: ["guide"],
    is_pinned: true,
    created_at: "2026-07-27T10:00:00Z",
    updated_at: "2026-07-27T10:00:00Z",
  },
  {
    id: 8,
    category: "Ocean",
    title: "Wave guide",
    summary: "Read the buoy forecast",
    content: "Marine observations",
    tags: ["waves"],
    is_pinned: false,
    created_at: "2026-07-28T10:00:00Z",
    updated_at: "2026-07-29T10:00:00Z",
  },
  {
    id: 9,
    category: "Ocean",
    title: "Tide table",
    summary: "Coastal timing",
    content: "Daily tide information",
    tags: ["coast"],
    is_pinned: false,
    created_at: "2026-07-26T10:00:00Z",
    updated_at: null,
  },
];

beforeEach(() => {
  vi.clearAllMocks();
  api.fetchFaqs.mockResolvedValue(articles);
  api.fetchFaqCategories.mockResolvedValue([
    { id: 1, name: "Guides" },
    { id: 2, name: "Ocean" },
  ]);
  api.fetchFaq.mockImplementation(async (id) => articles.find((article) => article.id === id));
  api.deleteFaq.mockResolvedValue({ status: "deleted" });
  vi.spyOn(window, "confirm").mockReturnValue(true);
  vi.spyOn(window, "scrollTo").mockImplementation(() => {});
});

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
});

describe("FaqPage category browsing", () => {
  it("starts at All Articles with counts and does not auto-open an article", async () => {
    render(<FaqPage />);

    expect(await screen.findByRole("button", { name: "All Articles 3" })).toHaveAttribute("aria-current", "true");
    expect(screen.getByRole("button", { name: "Guides 1" })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Ocean 2" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "All Articles" })).toBeInTheDocument();
    expect(screen.queryByText(/^Created /)).not.toBeInTheDocument();
    expect(api.fetchFaq).not.toHaveBeenCalled();
  });

  it("filters by category and clears an active search", async () => {
    const user = userEvent.setup();
    render(<FaqPage />);
    await screen.findByRole("button", { name: "Ocean 2" });

    await user.type(screen.getByPlaceholderText("Search FAQ keywords"), "guide");
    await user.click(screen.getByRole("button", { name: "Search" }));
    expect(screen.getByRole("heading", { name: "Search Results" })).toBeInTheDocument();

    await user.click(screen.getByRole("button", { name: "Ocean 2" }));
    expect(screen.getByRole("heading", { name: "Ocean" })).toBeInTheDocument();
    expect(screen.getByText("2 articles")).toBeInTheDocument();
    expect(screen.getByPlaceholderText("Search FAQ keywords")).toHaveValue("");
    expect(screen.queryByText("Rich FAQ")).not.toBeInTheDocument();
  });

  it("opens rich detail and returns to Search Results", async () => {
    const user = userEvent.setup();
    const { container } = render(<FaqPage />);
    await screen.findByRole("button", { name: "All Articles 3" });

    await user.type(screen.getByPlaceholderText("Search FAQ keywords"), "Guides");
    await user.click(screen.getByRole("button", { name: "Search" }));
    await user.click(screen.getByRole("button", { name: "Open Rich FAQ" }));

    expect(await screen.findByRole("button", { name: "Back to Search Results" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Formatted" })).toBeInTheDocument();
    expect(screen.getByText("Safe content").tagName).toBe("STRONG");
    expect(screen.getByRole("img", { name: "Forecast map" })).toHaveAttribute("src", expect.stringContaining("/api/faqs/images/"));
    expect(container.querySelector("script")).toBeNull();

    await user.click(screen.getByRole("button", { name: "Back to Search Results" }));
    expect(screen.getByRole("heading", { name: "Search Results" })).toBeInTheDocument();
    expect(screen.getByText("1 article")).toBeInTheDocument();
  });

  it("opens edit from a card without opening article detail", async () => {
    const user = userEvent.setup();
    render(<FaqPage />);
    await screen.findByRole("button", { name: "All Articles 3" });

    await user.click(screen.getByRole("button", { name: "Edit Rich FAQ" }));

    expect(await screen.findByRole("heading", { name: "Edit FAQ" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Back to All Articles" })).not.toBeInTheDocument();
    const editor = screen.getByRole("textbox", { name: "FAQ content" });
    await waitFor(() => expect(editor).toHaveTextContent("Formatted"));
  });

  it("deletes from a card without opening article detail", async () => {
    const user = userEvent.setup();
    api.fetchFaqs
      .mockResolvedValueOnce(articles)
      .mockResolvedValueOnce(articles.filter(({ id }) => id !== 8));
    render(<FaqPage />);
    await screen.findByRole("button", { name: "All Articles 3" });

    await user.click(screen.getByRole("button", { name: "Delete Wave guide" }));

    await waitFor(() => expect(api.deleteFaq).toHaveBeenCalledWith(8));
    expect(api.fetchFaq).not.toHaveBeenCalled();
    expect(await screen.findByRole("button", { name: "All Articles 2" })).toBeInTheDocument();
  });

  it("updates old and new category counts after moving an article", async () => {
    const user = userEvent.setup();
    const movedArticle = { ...articles[0], category: "Ocean" };
    api.updateFaq.mockResolvedValue(movedArticle);
    api.fetchFaqs
      .mockResolvedValueOnce(articles)
      .mockResolvedValueOnce([movedArticle, articles[1], articles[2]]);
    render(<FaqPage />);
    await screen.findByRole("button", { name: "Guides 1" });

    await user.click(screen.getByRole("button", { name: "Edit Rich FAQ" }));
    const categoryInput = screen.getByPlaceholderText("Enter or select a category");
    await user.clear(categoryInput);
    await user.type(categoryInput, "Ocean");
    await user.click(screen.getByRole("button", { name: "Save" }));

    await waitFor(() => expect(api.updateFaq).toHaveBeenCalledWith(7, expect.objectContaining({ category: "Ocean" })));
    expect(await screen.findByRole("button", { name: "Ocean 3" })).toBeInTheDocument();
    expect(screen.queryByRole("button", { name: "Guides 1" })).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: "Back to All Articles" })).toBeInTheDocument();
  });

  it("shows categories with zero articles and their empty state", async () => {
    const user = userEvent.setup();
    api.fetchFaqCategories.mockResolvedValue([{ id: 1, name: "Empty" }]);
    api.fetchFaqs.mockResolvedValue([]);
    render(<FaqPage />);
    await screen.findByRole("button", { name: "All Articles 0" });

    await user.click(screen.getByRole("button", { name: "Empty 0" }));

    expect(screen.getByRole("heading", { name: "Empty" })).toBeInTheDocument();
    expect(screen.getByText("0 articles")).toBeInTheDocument();
    expect(screen.getByText("No articles in this category.")).toBeInTheDocument();
  });
});
