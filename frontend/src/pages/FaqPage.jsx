import { useEffect, useMemo, useState } from "react";
import { createFaq, deleteFaq, fetchFaqCategories, fetchFaqs, updateFaq } from "../api";
import FAQArticleDetail from "../components/faq/FAQArticleDetail";
import FAQArticleList from "../components/faq/FAQArticleList";
import FAQCategorySidebar from "../components/faq/FAQCategorySidebar";
import { buildCategoryItems, filterAndSortArticles } from "../components/faq/faqBrowse";
import RichTextEditor from "../components/RichTextEditor/RichTextEditor";
import { isFaqContentEmpty } from "../utils/faqContent";

const emptyForm = {
  category: "",
  title: "",
  summary: "",
  content: "",
  tags: "",
  is_pinned: false,
};

const requiredFormFields = {
  title: "Title",
  category: "Category",
  summary: "Summary",
  content: "Content",
};

const allArticlesOrigin = { type: "all", category: "", searchKeyword: "" };

function parseTags(value) {
  return String(value || "").split(",").map((tag) => tag.trim()).filter(Boolean);
}

function getFormFieldError(fieldName, value) {
  const label = requiredFormFields[fieldName];
  const normalizedValue = String(value || "").trim();

  if (fieldName === "content" && isFaqContentEmpty(value)) return "* Content is required.";
  if (label && !normalizedValue) return `* ${label} is required.`;
  if (fieldName === "category" && !/[\p{L}\p{N}]/u.test(normalizedValue)) return "Invalid Category";

  if (fieldName === "tags" && normalizedValue) {
    const tags = parseTags(normalizedValue);
    if (tags.some((tag) => /[^\p{L}\p{N}\s-]/u.test(tag))) return "Invalid Tags";
    const normalizedTags = tags.map((tag) => tag.toLowerCase());
    if (new Set(normalizedTags).size !== normalizedTags.length) return "Duplicate Tags";
  }

  return "";
}

function normalizeFormPayload(formState) {
  return {
    category: formState.category.trim(),
    title: formState.title.trim(),
    summary: formState.summary.trim(),
    content: formState.content,
    tags: parseTags(formState.tags),
    is_pinned: Boolean(formState.is_pinned),
  };
}

function createEditFormState(article) {
  return {
    category: article.category || "",
    title: article.title || "",
    summary: article.summary || "",
    content: article.content || "",
    tags: Array.isArray(article.tags) ? article.tags.join(", ") : "",
    is_pinned: Boolean(article.is_pinned),
  };
}

function formatTimestamp(value) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("zh-TW", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    hour12: false,
  }).format(date);
}

export default function FaqPage({ resetToken = 0 }) {
  const [faqs, setFaqs] = useState([]);
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState("");
  const [selectedArticle, setSelectedArticle] = useState(null);
  const [searchKeyword, setSearchKeyword] = useState("");
  const [activeSearchKeyword, setActiveSearchKeyword] = useState("");
  const [viewMode, setViewMode] = useState("list");
  const [detailOrigin, setDetailOrigin] = useState(allArticlesOrigin);
  const [formOrigin, setFormOrigin] = useState(null);
  const [formState, setFormState] = useState(emptyForm);
  const [formErrors, setFormErrors] = useState({});
  const [error, setError] = useState("");
  const [isLoadingList, setIsLoadingList] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isCategoryMenuOpen, setIsCategoryMenuOpen] = useState(false);

  const categoryNames = useMemo(() => categories.map(({ name }) => name), [categories]);
  const categoryItems = useMemo(() => buildCategoryItems(categories, faqs), [categories, faqs]);
  const visibleArticles = useMemo(
    () => filterAndSortArticles(faqs, { selectedCategory, activeSearchKeyword }),
    [faqs, selectedCategory, activeSearchKeyword],
  );

  const listContextType = activeSearchKeyword ? "search" : selectedCategory ? "category" : "all";
  const listHeading = activeSearchKeyword ? "Search Results" : selectedCategory || "All Articles";

  function currentListOrigin() {
    if (activeSearchKeyword) return { type: "search", category: "", searchKeyword: activeSearchKeyword };
    if (selectedCategory) return { type: "category", category: selectedCategory, searchKeyword: "" };
    return allArticlesOrigin;
  }

  async function loadFaqData() {
    const [nextFaqs, nextCategories] = await Promise.all([fetchFaqs(), fetchFaqCategories()]);
    setFaqs(nextFaqs);
    setCategories(nextCategories);
    return { nextFaqs, nextCategories };
  }

  useEffect(() => {
    let isCurrent = true;
    setSelectedCategory("");
    setSelectedArticle(null);
    setSearchKeyword("");
    setActiveSearchKeyword("");
    setViewMode("list");
    setDetailOrigin(allArticlesOrigin);
    setFormOrigin(null);
    setFormState(emptyForm);
    setFormErrors({});
    setError("");
    setIsCategoryMenuOpen(false);
    setIsLoadingList(true);

    Promise.all([fetchFaqs(), fetchFaqCategories()])
      .then(([nextFaqs, nextCategories]) => {
        if (!isCurrent) return;
        setFaqs(nextFaqs);
        setCategories(nextCategories);
      })
      .catch((loadError) => {
        if (isCurrent) setError(loadError.message);
      })
      .finally(() => {
        if (isCurrent) setIsLoadingList(false);
      });

    return () => {
      isCurrent = false;
    };
  }, [resetToken]);

  function scrollToTop() {
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function handleSearchSubmit(event) {
    event.preventDefault();
    const nextKeyword = searchKeyword.trim();
    setSelectedCategory("");
    setSelectedArticle(null);
    setActiveSearchKeyword(nextKeyword);
    setViewMode("list");
  }

  function handleCategoryClick(categoryName) {
    setSelectedCategory(categoryName);
    setSelectedArticle(null);
    setSearchKeyword("");
    setActiveSearchKeyword("");
    setViewMode("list");
    setError("");
  }

  function handleOpenArticle(article) {
    setDetailOrigin(currentListOrigin());
    setSelectedArticle(article);
    setViewMode("detail");
  }

  function restoreOrigin(origin) {
    const nextOrigin = origin || allArticlesOrigin;
    setSelectedArticle(null);
    setFormOrigin(null);
    setViewMode("list");
    if (nextOrigin.type === "search") {
      setSelectedCategory("");
      setSearchKeyword(nextOrigin.searchKeyword);
      setActiveSearchKeyword(nextOrigin.searchKeyword);
    } else {
      setSelectedCategory(nextOrigin.type === "category" ? nextOrigin.category : "");
      setSearchKeyword("");
      setActiveSearchKeyword("");
    }
  }

  function handleStartCreate() {
    setFormOrigin(viewMode === "detail" ? detailOrigin : currentListOrigin());
    setSelectedArticle(null);
    setViewMode("create");
    setFormState(emptyForm);
    setFormErrors({});
    setError("");
  }

  function handleStartEdit(article = selectedArticle) {
    if (!article) return;
    if (viewMode === "list") setDetailOrigin(currentListOrigin());
    setSelectedArticle(article);
    setViewMode("edit");
    setFormState(createEditFormState(article));
    setFormErrors({});
    setError("");
  }

  function handleCancelEdit() {
    setError("");
    setFormErrors({});
    if (viewMode === "create") {
      restoreOrigin(formOrigin);
      return;
    }
    setViewMode("detail");
    setFormState(selectedArticle ? createEditFormState(selectedArticle) : emptyForm);
  }

  function handleFormChange(event) {
    const { name, value, type, checked } = event.target;
    const nextValue = type === "checkbox" ? checked : value;
    setFormState((current) => ({ ...current, [name]: nextValue }));
    if (formErrors[name] && !getFormFieldError(name, nextValue)) {
      setFormErrors((current) => {
        const nextErrors = { ...current };
        delete nextErrors[name];
        return nextErrors;
      });
    }
  }

  function handleContentChange(content) {
    setFormState((current) => ({ ...current, content }));
    if (formErrors.content && !getFormFieldError("content", content)) {
      setFormErrors((current) => {
        const nextErrors = { ...current };
        delete nextErrors.content;
        return nextErrors;
      });
    }
  }

  function handleCategoryOptionSelect(categoryName) {
    setFormState((current) => ({ ...current, category: categoryName }));
    setFormErrors((current) => {
      const nextErrors = { ...current };
      delete nextErrors.category;
      return nextErrors;
    });
    setIsCategoryMenuOpen(false);
  }

  function validateForm() {
    const nextErrors = {};
    Object.keys(requiredFormFields).forEach((fieldName) => {
      const fieldError = getFormFieldError(fieldName, formState[fieldName]);
      if (fieldError) nextErrors[fieldName] = fieldError;
    });
    const tagError = getFormFieldError("tags", formState.tags);
    if (tagError) nextErrors.tags = tagError;
    return nextErrors;
  }

  async function handleSubmit(event) {
    event.preventDefault();
    const nextErrors = validateForm();
    if (Object.keys(nextErrors).length > 0) {
      setFormErrors(nextErrors);
      setError("");
      return;
    }

    setIsSubmitting(true);
    setError("");
    try {
      const payload = normalizeFormPayload(formState);
      const wasCreating = viewMode === "create";
      const savedArticle = wasCreating
        ? await createFaq(payload)
        : await updateFaq(selectedArticle.id, payload);
      const { nextFaqs } = await loadFaqData();
      setSelectedArticle(nextFaqs.find(({ id }) => id === savedArticle.id) || savedArticle);
      if (wasCreating) setDetailOrigin(formOrigin || allArticlesOrigin);
      setViewMode("detail");
      setFormOrigin(null);
      setFormState(emptyForm);
    } catch (submitError) {
      setError(submitError.message);
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleDelete(article = selectedArticle) {
    if (!article) return;
    if (!window.confirm(`Delete "${article.title}"? This action cannot be undone.`)) return;

    const origin = viewMode === "detail" ? detailOrigin : currentListOrigin();
    setIsSubmitting(true);
    setError("");
    try {
      await deleteFaq(article.id);
      const { nextFaqs } = await loadFaqData();
      if (origin.type === "category" && !nextFaqs.some(({ category }) => category === origin.category)) {
        restoreOrigin(allArticlesOrigin);
      } else {
        restoreOrigin(origin);
      }
    } catch (deleteError) {
      setError(deleteError.message);
    } finally {
      setIsSubmitting(false);
    }
  }

  const backLabel = detailOrigin.type === "search"
    ? "Back to Search Results"
    : detailOrigin.type === "category"
      ? `Back to ${detailOrigin.category}`
      : "Back to All Articles";

  return (
    <section className="faq-page">
      <div className="faq-page-header">
        <h2>FAQ</h2>
        <button type="button" className="primary-button" onClick={handleStartCreate}>New FAQ</button>
      </div>
      {error ? <p className="status-message error-message">{error}</p> : null}

      <div className="faq-layout">
        <FAQCategorySidebar
          searchKeyword={searchKeyword}
          activeSearchKeyword={activeSearchKeyword}
          totalCount={faqs.length}
          categoryItems={categoryItems}
          selectedCategory={selectedCategory}
          onSearchKeywordChange={setSearchKeyword}
          onSearch={handleSearchSubmit}
          onSelectCategory={handleCategoryClick}
        />

        <section className="faq-detail-panel">
          {viewMode === "create" || viewMode === "edit" ? (
            <form className="faq-form" onSubmit={handleSubmit}>
              <div className="faq-detail-header">
                <h3>{viewMode === "create" ? "New FAQ" : "Edit FAQ"}</h3>
                <div className="faq-detail-actions">
                  <button type="button" onClick={handleCancelEdit} disabled={isSubmitting}>Cancel</button>
                  <button type="submit" className="primary-button" disabled={isSubmitting}>{isSubmitting ? "Saving..." : "Save"}</button>
                </div>
              </div>

              <label>
                <span className="faq-label-row">Title {formErrors.title ? <span className="faq-field-error-text">{formErrors.title}</span> : null}</span>
                <input name="title" value={formState.title} onChange={handleFormChange} placeholder="FAQ title" className={formErrors.title ? "faq-field-error" : ""} />
              </label>

              <div className="faq-form-row">
                <label className="faq-category-field">
                  <span className="faq-label-row">Category {formErrors.category ? <span className="faq-field-error-text">{formErrors.category}</span> : null}</span>
                  <input
                    name="category"
                    value={formState.category}
                    onChange={handleFormChange}
                    onFocus={() => setIsCategoryMenuOpen(true)}
                    onBlur={() => setIsCategoryMenuOpen(false)}
                    placeholder="Enter or select a category"
                    className={formErrors.category ? "faq-field-error" : ""}
                  />
                  {isCategoryMenuOpen && categoryNames.length > 0 ? (
                    <div className="faq-category-menu">
                      {categoryNames.map((categoryName) => (
                        <button type="button" key={categoryName} onMouseDown={(event) => event.preventDefault()} onClick={() => handleCategoryOptionSelect(categoryName)}>
                          {categoryName}
                        </button>
                      ))}
                    </div>
                  ) : null}
                </label>
                <label>
                  <span className="faq-label-row">Tags {formErrors.tags ? <span className="faq-field-error-text">{formErrors.tags}</span> : null}</span>
                  <input name="tags" value={formState.tags} onChange={handleFormChange} placeholder="Separate tags with commas. Example: satellite, FAQ, guide" className={formErrors.tags ? "faq-field-error" : ""} />
                </label>
              </div>

              <label className="checkbox-row">
                <input type="checkbox" name="is_pinned" checked={formState.is_pinned} onChange={handleFormChange} />
                Pin this FAQ
              </label>

              <label>
                <span className="faq-label-row">Summary {formErrors.summary ? <span className="faq-field-error-text">{formErrors.summary}</span> : null}</span>
                <textarea name="summary" value={formState.summary} onChange={handleFormChange} rows={3} placeholder="Short summary shown on the list card" className={formErrors.summary ? "faq-field-error" : ""} />
              </label>

              <div className="faq-content-field">
                <span className="faq-label-row">Content {formErrors.content ? <span className="faq-field-error-text">{formErrors.content}</span> : null}</span>
                <RichTextEditor value={formState.content} onChange={handleContentChange} disabled={isSubmitting} placeholder="Write the FAQ content" />
              </div>
            </form>
          ) : viewMode === "detail" && selectedArticle ? (
            <FAQArticleDetail
              article={selectedArticle}
              backLabel={backLabel}
              formatTimestamp={formatTimestamp}
              isSubmitting={isSubmitting}
              onBack={() => restoreOrigin(detailOrigin)}
              onEdit={handleStartEdit}
              onDelete={handleDelete}
            />
          ) : (
            <FAQArticleList
              articles={visibleArticles}
              heading={listHeading}
              contextType={listContextType}
              isLoading={isLoadingList}
              isSubmitting={isSubmitting}
              formatTimestamp={formatTimestamp}
              onOpen={handleOpenArticle}
              onEdit={handleStartEdit}
              onDelete={handleDelete}
            />
          )}
        </section>
      </div>
      <button className="back-to-top-button" type="button" onClick={scrollToTop} aria-label="Back to top">↑</button>
    </section>
  );
}
