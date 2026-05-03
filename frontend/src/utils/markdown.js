import { marked } from "marked";
import katex from "katex";

marked.setOptions({ breaks: true, gfm: true });

/**
 * Render a single LaTeX expression to HTML using KaTeX.
 * Falls back to a plain code element on parse errors so users still see the source.
 */
const renderMathExpr = (expr, displayMode) => {
  try {
    return katex.renderToString(expr, {
      displayMode,
      throwOnError: false,
      strict: "ignore",
      output: "htmlAndMathml",
      trust: false,
    });
  } catch (err) {
    const safe = expr.replace(/[&<>]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;" }[c]));
    return `<code class="katex-error" title="${err?.message || "render failed"}">${safe}</code>`;
  }
};

// Use alphanumeric-only sentinels so marked never re-interprets them
// (no `_`, `*`, `$`, etc. that could trigger emphasis or other markdown rules).
const TOKEN_RE = /KATEXMATHTOKEN(\d+)ENDKATEX/g;
const makeToken = (idx) => `KATEXMATHTOKEN${idx}ENDKATEX`;

/**
 * Pull every math segment ($$..$$, \[..\], \(..\), $..$) out of `text`,
 * replace each with an opaque token, and return the cleaned text plus the
 * captured blocks so we can re-insert rendered HTML after `marked` runs.
 *
 * Order matters: longest / most-specific delimiters first so we never
 * accidentally match the inner `$` of a `$$..$$` block as inline math.
 */
const extractMath = (text) => {
  const blocks = [];
  let out = text;

  // $$ ... $$  (display math, may span multiple lines)
  out = out.replace(/\$\$([\s\S]+?)\$\$/g, (_, expr) => {
    const idx = blocks.push({ expr: expr.trim(), display: true }) - 1;
    return makeToken(idx);
  });

  // \[ ... \]  (display math)
  out = out.replace(/\\\[([\s\S]+?)\\\]/g, (_, expr) => {
    const idx = blocks.push({ expr: expr.trim(), display: true }) - 1;
    return makeToken(idx);
  });

  // \( ... \)  (inline math)
  out = out.replace(/\\\(([\s\S]+?)\\\)/g, (_, expr) => {
    const idx = blocks.push({ expr: expr.trim(), display: false }) - 1;
    return makeToken(idx);
  });

  // $ ... $  (inline math) — conservative: require non-whitespace next to the
  // delimiters and skip escaped \$ to avoid matching prices like "$5".
  out = out.replace(/(?<!\\)\$(?!\s)([^$\n]+?)(?<!\s)\$(?!\d)/g, (_, expr) => {
    const idx = blocks.push({ expr: expr.trim(), display: false }) - 1;
    return makeToken(idx);
  });

  return { text: out, blocks };
};

/**
 * Render markdown text with LaTeX math support.
 *
 * Strategy: extract math first (so marked doesn't mangle subscripts like `y_i`
 * into `<em>i</em>`), run marked on the rest, then swap tokens for KaTeX HTML.
 * Display-math tokens that ended up wrapped in `<p>` get unwrapped so the
 * resulting HTML is semantically clean and styles correctly as a block.
 */
export const renderMarkdown = (text) => {
  if (!text) return "";
  const { text: stripped, blocks } = extractMath(String(text));
  let html = marked.parse(stripped);

  // Unwrap display-math placeholders that marked put inside a paragraph,
  // so block math renders as a true block element.
  html = html.replace(
    /<p>\s*(KATEXMATHTOKEN\d+ENDKATEX)\s*<\/p>/g,
    (match, token) => {
      const idxMatch = token.match(/^KATEXMATHTOKEN(\d+)ENDKATEX$/);
      if (!idxMatch) return match;
      const block = blocks[Number(idxMatch[1])];
      return block?.display ? token : match;
    }
  );

  html = html.replace(TOKEN_RE, (_, idxStr) => {
    const block = blocks[Number(idxStr)];
    if (!block) return "";
    return renderMathExpr(block.expr, block.display);
  });

  return html;
};
