import { describe, expect, it } from "vitest";

import {
  isFaqContentEmpty,
  normalizeFaqContent,
  normalizeLinkUrl,
  sanitizeFaqHtml,
} from "./faqContent";


describe("normalizeFaqContent", () => {
  it("escapes legacy plain text and preserves line breaks", () => {
    expect(normalizeFaqContent("First <unsafe>\nSecond & final")).toBe(
      "<p>First &lt;unsafe&gt;</p><p>Second &amp; final</p>",
    );
  });

  it("keeps existing HTML for the sanitizer", () => {
    expect(normalizeFaqContent("<h2>Heading</h2>")).toBe("<h2>Heading</h2>");
  });
});

describe("sanitizeFaqHtml", () => {
  it("keeps supported formatting and removes executable HTML", () => {
    const dirty =
      '<h2 style="text-align:center" onclick="bad()">Title</h2>' +
      '<span style="font-size:20px;color:#123456;position:fixed">Text</span>' +
      '<script>alert(1)</script><a href="javascript:alert(2)">bad</a>';

    const clean = sanitizeFaqHtml(dirty);

    expect(clean).toContain("<h2");
    expect(clean).toContain("text-align: center");
    expect(clean).toContain("font-size: 20px");
    expect(clean).not.toContain("onclick");
    expect(clean).not.toContain("position");
    expect(clean).not.toContain("script");
    expect(clean).not.toContain("javascript:");
  });
});

describe("isFaqContentEmpty", () => {
  it.each(["", "<p></p>", "<p><br></p>", "<p><span>&nbsp;</span></p>"])(
    "treats %s as empty",
    (content) => expect(isFaqContentEmpty(content)).toBe(true),
  );

  it("accepts visible text and image-only documents", () => {
    expect(isFaqContentEmpty("<p>Visible</p>")).toBe(false);
    expect(isFaqContentEmpty('<p><img src="https://example.com/image.png"></p>')).toBe(false);
  });
});

describe("normalizeLinkUrl", () => {
  it("adds https to host-like values and preserves safe protocols", () => {
    expect(normalizeLinkUrl("example.com/docs")).toBe("https://example.com/docs");
    expect(normalizeLinkUrl("https://example.com")).toBe("https://example.com/");
    expect(normalizeLinkUrl("mailto:faq@example.com")).toBe("mailto:faq@example.com");
  });

  it.each(["javascript:alert(1)", "data:text/html,bad", "file:///etc/passwd", "   "])(
    "rejects unsafe value %s",
    (value) => expect(normalizeLinkUrl(value)).toBeNull(),
  );
});
