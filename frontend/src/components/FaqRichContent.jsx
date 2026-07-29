import { useMemo } from "react";

import { sanitizeFaqHtml } from "../utils/faqContent";


export default function FaqRichContent({ content }) {
  const sanitizedHtml = useMemo(() => sanitizeFaqHtml(content), [content]);
  return <div className="faq-rich-content" dangerouslySetInnerHTML={{ __html: sanitizedHtml }} />;
}
