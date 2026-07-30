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

  it("keeps table structure and safe spans while removing dangerous table HTML", () => {
    const dirty =
      '<table onclick="bad()" style="position:fixed"><thead><tr>' +
      '<th colspan="2" rowspan="1" onerror="bad()">Heading</th></tr></thead>' +
      '<tbody><tr><td rowspan="2" data-secret="x">A</td><td>B</td></tr>' +
      '<tr><td colspan="1"><iframe src="https://example.com"></iframe>C' +
      '<script>alert(1)</script></td></tr></tbody></table>';

    const clean = sanitizeFaqHtml(dirty);

    expect(clean).toContain("<table>");
    expect(clean).toContain("<thead>");
    expect(clean).toContain("<tbody>");
    expect(clean).toContain('<th colspan="2" rowspan="1">Heading</th>');
    expect(clean).toContain('<td rowspan="2">A</td>');
    expect(clean).not.toContain("onclick");
    expect(clean).not.toContain("onerror");
    expect(clean).not.toContain("data-secret");
    expect(clean).not.toContain("position");
    expect(clean).not.toContain("iframe");
    expect(clean).not.toContain("script");
  });

  it("keeps controlled table sizing and vertical alignment", () => {
    const dirty =
      '<table data-table-width="75" style="width: 75%; position: fixed"><colgroup>' +
      '<col style="width: 120px; color: red"><col style="min-width: 80px"></colgroup>' +
      '<tbody><tr><td data-vertical-align="middle">A</td>' +
      '<td data-vertical-align="sideways" data-secret="x">B</td></tr></tbody></table>';

    const clean = sanitizeFaqHtml(dirty);

    expect(clean).toContain('data-table-width="75"');
    expect(clean).toContain("width: 75%");
    expect(clean).toContain("<colgroup>");
    expect(clean).toContain('style="width: 120px"');
    expect(clean).toContain('style="min-width: 80px"');
    expect(clean).toContain('data-vertical-align="middle"');
    expect(clean).not.toContain("position");
    expect(clean).not.toContain("color");
    expect(clean).not.toContain("sideways");
    expect(clean).not.toContain("data-secret");
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
