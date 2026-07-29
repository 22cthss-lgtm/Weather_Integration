export default function FAQArticleCard({ article, formatTimestamp, onOpen, onEdit, onDelete, isSubmitting }) {
  function handleKeyDown(event) {
    if (event.target !== event.currentTarget) return;
    if (event.key === "Enter" || event.key === " ") {
      event.preventDefault();
      onOpen(article);
    }
  }

  return (
    <article
      className="faq-article-card"
      role="button"
      tabIndex={0}
      aria-label={`Open ${article.title}`}
      onClick={() => onOpen(article)}
      onKeyDown={handleKeyDown}
    >
      <div className="faq-card-topline">
        <span className="faq-category-pill">{article.category}</span>
        {article.is_pinned ? <span className="faq-pin">Pinned</span> : null}
      </div>
      <h4>{article.title}</h4>
      <p>{article.summary}</p>
      {article.tags?.length ? (
        <div className="faq-tag-list">
          {article.tags.map((tag) => <span className="faq-tag" key={tag}>#{tag}</span>)}
        </div>
      ) : null}
      <div className="faq-article-card-footer">
        <span className="faq-card-meta">Last updated {formatTimestamp(article.updated_at || article.created_at)}</span>
        <div className="faq-article-card-actions">
          <button
            type="button"
            aria-label={`Edit ${article.title}`}
            onClick={(event) => {
              event.stopPropagation();
              onEdit(article);
            }}
          >
            Edit
          </button>
          <button
            type="button"
            className="danger-button"
            aria-label={`Delete ${article.title}`}
            disabled={isSubmitting}
            onClick={(event) => {
              event.stopPropagation();
              onDelete(article);
            }}
          >
            Delete
          </button>
        </div>
      </div>
    </article>
  );
}
