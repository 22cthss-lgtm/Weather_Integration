import { describe, expect, it } from "vitest";
import { buildCategoryItems, filterAndSortArticles } from "./faqBrowse";

const articles = [
  {
    id: 1,
    category: "Ocean",
    title: "Older pinned",
    summary: "",
    content: "",
    tags: [],
    is_pinned: true,
    created_at: "2026-01-01",
    updated_at: null,
  },
  {
    id: 2,
    category: "Storm",
    title: "Newest",
    summary: "",
    content: "",
    tags: [],
    is_pinned: false,
    created_at: "2026-01-02",
    updated_at: "2026-06-01",
  },
  {
    id: 3,
    category: "Ocean",
    title: "Guide",
    summary: "waves",
    content: "buoy content",
    tags: ["marine"],
    is_pinned: false,
    created_at: "2026-04-01",
    updated_at: null,
  },
];

describe("FAQ browse derivations", () => {
  it("builds ordered categories and article counts", () => {
    expect(buildCategoryItems([{ name: "Storm" }, { name: "Ocean" }, { name: "Empty" }], articles)).toEqual([
      { name: "Storm", count: 1 },
      { name: "Ocean", count: 2 },
      { name: "Empty", count: 0 },
    ]);
  });

  it.each([
    ["Guide", 1],
    ["waves", 1],
    ["buoy", 1],
    ["marine", 1],
    ["Ocean", 2],
  ])("searches all fields for %s", (query, count) => {
    expect(filterAndSortArticles(articles, { activeSearchKeyword: query })).toHaveLength(count);
  });

  it("filters by category", () => {
    expect(filterAndSortArticles(articles, { selectedCategory: "Storm" }).map(({ id }) => id)).toEqual([2]);
  });

  it("sorts a copy by pinned then effective timestamp", () => {
    const originalOrder = articles.map(({ id }) => id);

    expect(filterAndSortArticles(articles).map(({ id }) => id)).toEqual([1, 2, 3]);
    expect(articles.map(({ id }) => id)).toEqual(originalOrder);
  });
});
