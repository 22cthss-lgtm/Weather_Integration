import FAQArticleCard from "./FAQArticleCard";

function pluralize(count) {
  return `${count} ${count === 1 ? "article" : "articles"}`;
}

export default function FAQArticleList({
  articles,
  heading,
  contextType,
  isLoading,
  isSubmitting,
  formatTimestamp,
  onOpen,
  onEdit,
  onDelete,
}) {
  let emptyMessage = "No articles yet.";
  if (contextType === "category") emptyMessage = "No articles in this category.";
  if (contextType === "search") emptyMessage = "No articles match your search.";

  return (
    <div className="faq-article-list-view">
      <div className="faq-article-list-header">
        <h3>{heading}</h3>
        <span>{pluralize(articles.length)}</span>
      </div>
      {isLoading ? <p className="status-message">Loading FAQs...</p> : null}
      {!isLoading && articles.length === 0 ? (
        <div className="faq-empty-state">
          <h3>No articles found</h3>
          <p>{emptyMessage}</p>
        </div>
      ) : null}
      {!isLoading && articles.length > 0 ? (
        <div className="faq-article-card-list">
          {articles.map((article) => (
            <FAQArticleCard
              key={article.id}
              article={article}
              formatTimestamp={formatTimestamp}
              onOpen={onOpen}
              onEdit={onEdit}
              onDelete={onDelete}
              isSubmitting={isSubmitting}
            />
          ))}
        </div>
      ) : null}
    </div>
  );
}
