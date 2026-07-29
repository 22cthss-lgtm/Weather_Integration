import FaqRichContent from "../FaqRichContent";

export default function FAQArticleDetail({
  article,
  backLabel,
  formatTimestamp,
  isSubmitting,
  onBack,
  onEdit,
  onDelete,
}) {
  return (
    <article className="faq-detail-content">
      <button type="button" className="faq-back-button" onClick={onBack}>{backLabel}</button>
      <div className="faq-detail-header">
        <div>
          <div className="faq-card-topline">
            <span className="faq-category-pill">{article.category}</span>
            {article.is_pinned ? <span className="faq-pin">Pinned</span> : null}
          </div>
          <h3>{article.title}</h3>
          <p className="faq-summary">{article.summary}</p>
        </div>
        <div className="faq-detail-actions">
          <button type="button" onClick={() => onEdit(article)}>Edit</button>
          <button type="button" className="danger-button" onClick={() => onDelete(article)} disabled={isSubmitting}>Delete</button>
        </div>
      </div>
      <div className="faq-metadata">
        <span>Created {formatTimestamp(article.created_at)}</span>
        <span>Last updated {formatTimestamp(article.updated_at)}</span>
      </div>
      {article.tags?.length ? (
        <div className="faq-tag-list">
          {article.tags.map((tag) => <span className="faq-tag" key={tag}>#{tag}</span>)}
        </div>
      ) : null}
      <FaqRichContent content={article.content} />
    </article>
  );
}
