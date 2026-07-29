export default function FAQCategorySidebar({
  searchKeyword,
  activeSearchKeyword,
  totalCount,
  categoryItems,
  selectedCategory,
  onSearchKeywordChange,
  onSearch,
  onSelectCategory,
}) {
  return (
    <aside className="faq-sidebar">
      <form className="faq-search" onSubmit={onSearch}>
        <input
          type="search"
          aria-label="Search FAQ keywords"
          placeholder="Search FAQ keywords"
          value={searchKeyword}
          onChange={(event) => onSearchKeywordChange(event.target.value)}
        />
        <button type="submit">Search</button>
      </form>

      <nav className="faq-category-panel" aria-label="FAQ categories">
        <div className="faq-category-header">
          <h3>Categories</h3>
        </div>
        <div className="faq-category-list">
          <button
            type="button"
            className={!activeSearchKeyword && !selectedCategory ? "faq-category-item active" : "faq-category-item"}
            aria-label={`All Articles ${totalCount}`}
            aria-current={!activeSearchKeyword && !selectedCategory ? "true" : undefined}
            onClick={() => onSelectCategory("")}
          >
            <span>All Articles</span>
            <span className="faq-category-count">{totalCount}</span>
          </button>
          {categoryItems.map(({ name, count }) => {
            const isActive = !activeSearchKeyword && selectedCategory === name;
            return (
              <button
                type="button"
                key={name}
                className={isActive ? "faq-category-item active" : "faq-category-item"}
                aria-label={`${name} ${count}`}
                aria-current={isActive ? "true" : undefined}
                onClick={() => onSelectCategory(name)}
              >
                <span>{name}</span>
                <span className="faq-category-count">{count}</span>
              </button>
            );
          })}
        </div>
      </nav>
    </aside>
  );
}
