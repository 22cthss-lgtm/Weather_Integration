import { useEffect, useMemo, useState } from "react";
import {
  createFaq,
  deleteFaq,
  fetchFaq,
  fetchFaqCategories,
  fetchFaqs,
  updateFaq,
} from "../api";

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

function parseTags(value) {
  return String(value || "")
    .split(",")
    .map((tag) => tag.trim())
    .filter(Boolean);
}

function getFormFieldError(fieldName, value) {
  const label = requiredFormFields[fieldName];
  const normalizedValue = String(value || "").trim();

  if (label && !normalizedValue) {
    return `* ${label} is required.`;
  }

  if (fieldName === "category" && !/[\p{L}\p{N}]/u.test(normalizedValue)) {
    return "Invalid Category";
  }

  if (fieldName === "tags" && normalizedValue) {
    const tags = parseTags(normalizedValue);
    const hasInvalidTag = tags.some((tag) => /[^\p{L}\p{N}\s-]/u.test(tag));

    if (hasInvalidTag) {
      return "Invalid Tags";
    }

    const normalizedTags = tags.map((tag) => tag.toLowerCase());
    const uniqueTags = new Set(normalizedTags);

    if (uniqueTags.size !== normalizedTags.length) {
      return "Duplicate Tags";
    }
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

function createEditFormState(faq) {
  return {
    category: faq.category || "",
    title: faq.title || "",
    summary: faq.summary || "",
    content: faq.content || "",
    tags: Array.isArray(faq.tags) ? faq.tags.join(", ") : "",
    is_pinned: Boolean(faq.is_pinned),
  };
}

function formatTimestamp(value) {
  if (!value) {
    return "-";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return value;
  }

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
  const [categoryFilterText, setCategoryFilterText] = useState("");
  const [searchText, setSearchText] = useState("");
  const [queryText, setQueryText] = useState("");
  const [selectedId, setSelectedId] = useState(null);
  const [selectedFaq, setSelectedFaq] = useState(null);
  const [mode, setMode] = useState("view");
  const [formState, setFormState] = useState(emptyForm);
  const [error, setError] = useState("");
  const [isLoadingList, setIsLoadingList] = useState(false);
  const [isLoadingDetail, setIsLoadingDetail] = useState(false);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isCategoryMenuOpen, setIsCategoryMenuOpen] = useState(false);
  const [isCategoryFilterMenuOpen, setIsCategoryFilterMenuOpen] = useState(false);
  const [formErrors, setFormErrors] = useState({});

  const categoryNames = useMemo(() => categories.map((item) => item.name), [categories]);
  const filteredCategoryNames = useMemo(() => {
    const normalizedFilter = categoryFilterText.trim().toLowerCase();

    if (!normalizedFilter) {
      return categoryNames;
    }

    return categoryNames.filter((categoryName) => categoryName.toLowerCase().includes(normalizedFilter));
  }, [categoryFilterText, categoryNames]);

  function scrollToTop() {
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function resetBrowseState() {
    setSelectedCategory("");
    setCategoryFilterText("");
    setSearchText("");
    setQueryText("");
    setSelectedId(null);
    setSelectedFaq(null);
    setMode("view");
    setFormState(emptyForm);
    setFormErrors({});
    setError("");
    setIsCategoryMenuOpen(false);
    setIsCategoryFilterMenuOpen(false);
  }

  useEffect(() => {
    resetBrowseState();
  }, [resetToken]);

  useEffect(() => {
    async function loadCategories() {
      try {
        const result = await fetchFaqCategories();
        setCategories(result);
      } catch (err) {
        setError(err.message);
      }
    }

    loadCategories();
  }, []);

  useEffect(() => {
    async function loadFaqs() {
      setIsLoadingList(true);
      setError("");

      try {
        const result = await fetchFaqs({ category: selectedCategory, q: queryText });
        setFaqs(result);

        if (result.length === 0) {
          setSelectedId(null);
          setSelectedFaq(null);
          if (mode === "view") {
            setFormState(emptyForm);
          }
          return;
        }

        const stillSelected = result.some((item) => item.id === selectedId);
        if (!stillSelected && mode === "view") {
          setSelectedId(result[0].id);
        }
      } catch (err) {
        setError(err.message);
      } finally {
        setIsLoadingList(false);
      }
    }

    loadFaqs();
  }, [mode, queryText, selectedCategory, selectedId]);

  useEffect(() => {
    if (!selectedId || mode !== "view") {
      if (mode === "create") {
        setSelectedFaq(null);
      }
      return;
    }

    async function loadFaqDetail() {
      setIsLoadingDetail(true);
      setError("");

      try {
        const result = await fetchFaq(selectedId);
        setSelectedFaq(result);
      } catch (err) {
        setError(err.message);
      } finally {
        setIsLoadingDetail(false);
      }
    }

    loadFaqDetail();
  }, [mode, selectedId]);

  function handleSearchSubmit(event) {
    event.preventDefault();
    setQueryText(searchText.trim());
  }

  function handleCategoryClick(categoryName) {
    setSelectedCategory(categoryName);
    setCategoryFilterText(categoryName);
    setIsCategoryFilterMenuOpen(false);
    setMode("view");
  }

  function handleClearCategoryFilter() {
    resetBrowseState();
  }

  function handleSelectFaq(faqId) {
    setSelectedId(faqId);
    setMode("view");
  }

  function handleStartCreate() {
    setMode("create");
    setSelectedId(null);
    setSelectedFaq(null);
    setFormState(emptyForm);
    setFormErrors({});
    setError("");
  }

  function handleStartEdit() {
    if (!selectedFaq) {
      return;
    }
    setMode("edit");
    setFormState(createEditFormState(selectedFaq));
    setFormErrors({});
    setError("");
  }

  function handleCancelEdit() {
    setMode("view");
    setError("");
    if (selectedFaq) {
      setFormState(createEditFormState(selectedFaq));
    } else {
      setFormState(emptyForm);
    }
    setFormErrors({});
  }

  function handleFormChange(event) {
    const { name, value, type, checked } = event.target;
    const nextValue = type === "checkbox" ? checked : value;

    setFormState((current) => ({
      ...current,
      [name]: nextValue,
    }));

    if (formErrors[name] && !getFormFieldError(name, nextValue)) {
      setFormErrors((current) => {
        const nextErrors = { ...current };
        delete nextErrors[name];
        return nextErrors;
      });
    }
  }

  function handleCategoryOptionSelect(categoryName) {
    setFormState((current) => ({
      ...current,
      category: categoryName,
    }));
    setFormErrors((current) => {
      const nextErrors = { ...current };
      delete nextErrors.category;
      return nextErrors;
    });
    setIsCategoryMenuOpen(false);
  }

  function validateForm() {
    const nextErrors = {};

    Object.entries(requiredFormFields).forEach(([fieldName, label]) => {
      const fieldError = getFormFieldError(fieldName, formState[fieldName]);
      if (fieldError) {
        nextErrors[fieldName] = fieldError;
      }
    });

    const tagError = getFormFieldError("tags", formState.tags);
    if (tagError) {
      nextErrors.tags = tagError;
    }

    return nextErrors;
  }

  async function refreshAfterMutation(nextSelectedId = null) {
    const nextFaqs = await fetchFaqs({ category: selectedCategory, q: queryText });
    const nextCategories = await fetchFaqCategories();

    setFaqs(nextFaqs);
    setCategories(nextCategories);

    if (nextSelectedId) {
      setSelectedId(nextSelectedId);
      const detail = await fetchFaq(nextSelectedId);
      setSelectedFaq(detail);
      setMode("view");
      return;
    }

    if (nextFaqs.length > 0) {
      setSelectedId(nextFaqs[0].id);
      const detail = await fetchFaq(nextFaqs[0].id);
      setSelectedFaq(detail);
      setMode("view");
    } else {
      setSelectedId(null);
      setSelectedFaq(null);
      setMode("view");
    }
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
      let savedFaq;

      if (mode === "create") {
        savedFaq = await createFaq(payload);
      } else {
        savedFaq = await updateFaq(selectedId, payload);
      }

      await refreshAfterMutation(savedFaq.id);
      setFormState(emptyForm);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsSubmitting(false);
    }
  }

  async function handleDelete() {
    if (!selectedFaq) {
      return;
    }

    const confirmed = window.confirm(`Delete "${selectedFaq.title}"? This action cannot be undone.`);
    if (!confirmed) {
      return;
    }

    setIsSubmitting(true);
    setError("");

    try {
      await deleteFaq(selectedFaq.id);
      await refreshAfterMutation();
    } catch (err) {
      setError(err.message);
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <section className="faq-page">
      <div className="faq-page-header">
        <div>
          <h2>FAQ</h2>
        </div>
        <button type="button" className="primary-button" onClick={handleStartCreate}>
          New FAQ
        </button>
      </div>

      {error ? <p className="status-message error-message">{error}</p> : null}

      <div className="faq-layout">
        <aside className="faq-sidebar">
          <form className="faq-search" onSubmit={handleSearchSubmit}>
            <input
              type="search"
              placeholder="Search FAQ keywords"
              value={searchText}
              onChange={(event) => setSearchText(event.target.value)}
            />
            <button type="submit">Search</button>
          </form>

          <div className="faq-category-panel">
            <div className="faq-category-header">
              <h3>Categories</h3>
              <button type="button" className={!selectedCategory ? "filter-chip active" : "filter-chip"} onClick={handleClearCategoryFilter}>
                All Categories
              </button>
            </div>
            <div className="faq-category-filter">
              <input
                type="text"
                value={categoryFilterText}
                onChange={(event) => {
                  setCategoryFilterText(event.target.value);
                  setSelectedCategory("");
                  setIsCategoryFilterMenuOpen(true);
                }}
                onFocus={() => setIsCategoryFilterMenuOpen(true)}
                onBlur={() => setIsCategoryFilterMenuOpen(false)}
                placeholder="Select or search a category"
              />
              {isCategoryFilterMenuOpen ? (
                <div className="faq-category-menu">
                  {filteredCategoryNames.length > 0 ? (
                    filteredCategoryNames.map((categoryName) => (
                      <button
                        type="button"
                        key={categoryName}
                        className={selectedCategory === categoryName ? "active" : ""}
                        onMouseDown={(event) => event.preventDefault()}
                        onClick={() => handleCategoryClick(categoryName)}
                      >
                        {categoryName}
                      </button>
                    ))
                  ) : (
                    <span className="faq-category-menu-empty">No categories found.</span>
                  )}
                </div>
              ) : null}
            </div>
          </div>

          <div className="faq-list-panel">
            <div className="faq-list-header">
              <h3>Entries</h3>
              <span>{faqs.length} items</span>
            </div>
            {isLoadingList ? <p className="status-message">Loading FAQs...</p> : null}
            {!isLoadingList && faqs.length === 0 ? <p className="status-message">No FAQs match the current filters.</p> : null}
            <div className="faq-card-list">
              {faqs.map((faq) => (
                <button
                  type="button"
                  key={faq.id}
                  className={selectedId === faq.id && mode === "view" ? "faq-card active" : "faq-card"}
                  onClick={() => handleSelectFaq(faq.id)}
                >
                  <div className="faq-card-topline">
                    <span className="faq-category-pill">{faq.category}</span>
                    {faq.is_pinned ? <span className="faq-pin">Pinned</span> : null}
                  </div>
                  <h4>{faq.title}</h4>
                  <p>{faq.summary}</p>
                  <span className="faq-card-meta">Updated {formatTimestamp(faq.updated_at)}</span>
                </button>
              ))}
            </div>
          </div>
        </aside>

        <section className="faq-detail-panel">
          {mode === "create" || mode === "edit" ? (
            <form className="faq-form" onSubmit={handleSubmit}>
              <div className="faq-detail-header">
                <div>
                  <h3>{mode === "create" ? "New FAQ" : "Edit FAQ"}</h3>
                </div>
                <div className="faq-detail-actions">
                  <button type="button" onClick={handleCancelEdit} disabled={isSubmitting}>
                    Cancel
                  </button>
                  <button type="submit" className="primary-button" disabled={isSubmitting}>
                    {isSubmitting ? "Saving..." : "Save"}
                  </button>
                </div>
              </div>

              <label>
                <span className="faq-label-row">
                  Title
                  {formErrors.title ? <span className="faq-field-error-text">{formErrors.title}</span> : null}
                </span>
                <input
                  name="title"
                  value={formState.title}
                  onChange={handleFormChange}
                  placeholder="FAQ title"
                  className={formErrors.title ? "faq-field-error" : ""}
                />
              </label>

              <div className="faq-form-row">
                <label className="faq-category-field">
                  <span className="faq-label-row">
                    Category
                    {formErrors.category ? <span className="faq-field-error-text">{formErrors.category}</span> : null}
                  </span>
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
                        <button
                          type="button"
                          key={categoryName}
                          onMouseDown={(event) => event.preventDefault()}
                          onClick={() => handleCategoryOptionSelect(categoryName)}
                        >
                          {categoryName}
                        </button>
                      ))}
                    </div>
                  ) : null}
                </label>

                <label>
                  <span className="faq-label-row">
                    Tags
                    {formErrors.tags ? <span className="faq-field-error-text">{formErrors.tags}</span> : null}
                  </span>
                  <input
                    name="tags"
                    value={formState.tags}
                    onChange={handleFormChange}
                    placeholder="Separate tags with commas. Example: satellite, FAQ, guide"
                    className={formErrors.tags ? "faq-field-error" : ""}
                  />
                </label>
              </div>

              <label className="checkbox-row">
                <input
                  type="checkbox"
                  name="is_pinned"
                  checked={formState.is_pinned}
                  onChange={handleFormChange}
                />
                Pin this FAQ
              </label>

              <label>
                <span className="faq-label-row">
                  Summary
                  {formErrors.summary ? <span className="faq-field-error-text">{formErrors.summary}</span> : null}
                </span>
                <textarea
                  name="summary"
                  value={formState.summary}
                  onChange={handleFormChange}
                  rows={3}
                  placeholder="Short summary shown on the list card"
                  className={formErrors.summary ? "faq-field-error" : ""}
                />
              </label>

              <label>
                <span className="faq-label-row">
                  Content
                  {formErrors.content ? <span className="faq-field-error-text">{formErrors.content}</span> : null}
                </span>
                <textarea
                  name="content"
                  value={formState.content}
                  onChange={handleFormChange}
                  rows={14}
                  placeholder="Type the content"
                  className={formErrors.content ? "faq-field-error" : ""}
                />
              </label>

            </form>
          ) : selectedFaq ? (
            <article className="faq-detail-content">
              <div className="faq-detail-header">
                <div>
                  <div className="faq-card-topline">
                    <span className="faq-category-pill">{selectedFaq.category}</span>
                    {selectedFaq.is_pinned ? <span className="faq-pin">Pinned</span> : null}
                  </div>
                  <h3>{selectedFaq.title}</h3>
                  <p className="faq-summary">{selectedFaq.summary}</p>
                </div>
                <div className="faq-detail-actions">
                  <button type="button" onClick={handleStartEdit}>
                    Edit
                  </button>
                  <button type="button" className="danger-button" onClick={handleDelete} disabled={isSubmitting}>
                    Delete
                  </button>
                </div>
              </div>

              {isLoadingDetail ? <p className="status-message">Loading content...</p> : null}
              {!isLoadingDetail ? (
                <>
                  <div className="faq-metadata">
                    <span>Created {formatTimestamp(selectedFaq.created_at)}</span>
                    <span>Last updated {formatTimestamp(selectedFaq.updated_at)}</span>
                  </div>

                  {selectedFaq.tags?.length ? (
                    <div className="faq-tag-list">
                      {selectedFaq.tags.map((tag) => (
                        <span className="faq-tag" key={tag}>
                          #{tag}
                        </span>
                      ))}
                    </div>
                  ) : null}

                  <pre className="faq-content-text">{selectedFaq.content}</pre>
                </>
              ) : null}
            </article>
          ) : (
            <div className="faq-empty-state">
              <h3>Select an FAQ</h3>
              <p>Choose a card from the list to view details, or create a new FAQ.</p>
            </div>
          )}
        </section>
      </div>
      <button className="back-to-top-button" type="button" onClick={scrollToTop} aria-label="Back to top">
        ↑
      </button>
    </section>
  );
}
