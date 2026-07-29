import DOMPurify from "dompurify";


export const FAQ_ALLOWED_TAGS = [
  "a", "blockquote", "br", "code", "em", "h1", "h2", "h3", "h4", "h5",
  "h6", "hr", "img", "li", "ol", "p", "pre", "s", "span", "strong", "u", "ul",
];

const ALLOWED_FONT_SIZES = new Set(["12px", "14px", "16px", "18px", "20px", "24px", "28px", "32px"]);
const ALLOWED_TEXT_ALIGNMENTS = new Set(["left", "center", "right"]);

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function containsSupportedHtml(value) {
  const tags = FAQ_ALLOWED_TAGS.join("|");
  return new RegExp(`<\\/?(?:${tags})(?:\\s|>|/)`, "i").test(value);
}

export function normalizeFaqContent(content) {
  const value = String(content || "");
  if (!value) {
    return "";
  }
  if (containsSupportedHtml(value)) {
    return value;
  }
  return value.split(/\r?\n/).map((line) => `<p>${escapeHtml(line)}</p>`).join("");
}

function filterInlineStyles(element) {
  if (!element.hasAttribute("style")) {
    return;
  }
  const safeStyles = [];
  const { backgroundColor, color, fontSize, textAlign } = element.style;
  if (color) safeStyles.push(`color: ${color}`);
  if (backgroundColor) safeStyles.push(`background-color: ${backgroundColor}`);
  if (ALLOWED_FONT_SIZES.has(fontSize)) safeStyles.push(`font-size: ${fontSize}`);
  if (ALLOWED_TEXT_ALIGNMENTS.has(textAlign)) safeStyles.push(`text-align: ${textAlign}`);

  if (safeStyles.length) {
    element.setAttribute("style", safeStyles.join("; "));
  } else {
    element.removeAttribute("style");
  }
}

export function sanitizeFaqHtml(content) {
  const normalized = normalizeFaqContent(content);
  const clean = DOMPurify.sanitize(normalized, {
    ALLOWED_TAGS: FAQ_ALLOWED_TAGS,
    ALLOWED_ATTR: ["alt", "href", "rel", "src", "style", "target", "title"],
    ALLOW_DATA_ATTR: false,
  });
  const template = document.createElement("template");
  template.innerHTML = clean;

  template.content.querySelectorAll("[style]").forEach(filterInlineStyles);
  template.content.querySelectorAll("a").forEach((link) => {
    if (!normalizeLinkUrl(link.getAttribute("href"), { addProtocol: false })) {
      link.removeAttribute("href");
    }
    link.setAttribute("target", "_blank");
    link.setAttribute("rel", "noopener noreferrer");
  });
  template.content.querySelectorAll("img").forEach((image) => {
    const source = image.getAttribute("src") || "";
    if (!/^https?:\/\//i.test(source)) {
      image.remove();
    }
  });
  return template.innerHTML;
}

export function isFaqContentEmpty(content) {
  const template = document.createElement("template");
  template.innerHTML = sanitizeFaqHtml(content);
  const text = (template.content.textContent || "").replaceAll("\u00a0", "").trim();
  return !text && !template.content.querySelector("img[src]");
}

export function normalizeLinkUrl(value, { addProtocol = true } = {}) {
  const trimmed = String(value || "").trim();
  if (!trimmed) {
    return null;
  }
  if (/^mailto:/i.test(trimmed)) {
    return /^mailto:[^\s@]+@[^\s@]+$/i.test(trimmed) ? trimmed : null;
  }
  if (/^[a-z][a-z\d+.-]*:/i.test(trimmed) && !/^https?:/i.test(trimmed)) {
    return null;
  }

  const candidate = /^https?:\/\//i.test(trimmed)
    ? trimmed
    : addProtocol
      ? `https://${trimmed}`
      : null;
  if (!candidate) {
    return null;
  }
  try {
    const url = new URL(candidate);
    return ["http:", "https:"].includes(url.protocol) && url.hostname ? url.href : null;
  } catch {
    return null;
  }
}
