function normalizeSearchValue(value) {
  return String(value ?? "").toLocaleLowerCase();
}

export function effectiveTimestamp(article) {
  const updatedTimestamp = Date.parse(article.updated_at || "");
  if (Number.isFinite(updatedTimestamp)) {
    return updatedTimestamp;
  }

  const createdTimestamp = Date.parse(article.created_at || "");
  return Number.isFinite(createdTimestamp) ? createdTimestamp : 0;
}

export function buildCategoryItems(categories, articles) {
  const counts = new Map();

  articles.forEach((article) => {
    const categoryName = String(article.category || "").trim();
    if (categoryName) {
      counts.set(categoryName, (counts.get(categoryName) || 0) + 1);
    }
  });

  const orderedNames = categories.map(({ name }) => name);
  [...counts.keys()].sort((left, right) => left.localeCompare(right)).forEach((categoryName) => {
    if (!orderedNames.includes(categoryName)) {
      orderedNames.push(categoryName);
    }
  });

  return orderedNames.map((categoryName) => ({
    name: categoryName,
    count: counts.get(categoryName) || 0,
  }));
}

export function filterAndSortArticles(
  articles,
  { selectedCategory = "", activeSearchKeyword = "" } = {},
) {
  const query = normalizeSearchValue(activeSearchKeyword.trim());

  return articles
    .filter((article) => !selectedCategory || article.category === selectedCategory)
    .filter((article) => {
      if (!query) {
        return true;
      }

      return [
        article.title,
        article.summary,
        article.content,
        article.category,
        ...(article.tags || []),
      ].some((value) => normalizeSearchValue(value).includes(query));
    })
    .slice()
    .sort(
      (left, right) =>
        Number(right.is_pinned) - Number(left.is_pinned) ||
        effectiveTimestamp(right) - effectiveTimestamp(left) ||
        Number(right.id) - Number(left.id),
    );
}
