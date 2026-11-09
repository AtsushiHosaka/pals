/* Offline real-Chromium extractor regression; never a product E2E substitute. */
"use strict";
const test = require("node:test"), assert = require("node:assert/strict");
const { pathToFileURL } = require("node:url");
const { readRendered, sourceSemantics, semanticTokens } = require("../release-acceptance-browser.cjs");
const dependencyRoot = process.env.PALS_ACCEPTANCE_WEB_ROOT;
if (!dependencyRoot) throw new Error("PALS_ACCEPTANCE_WEB_ROOT is required; this browser check cannot silently skip");
const resolve = name => require.resolve(name, { paths: [dependencyRoot] });
let browser, page, processor, katex;

test.before(async () => {
  const { chromium } = require(resolve("playwright"));
  katex = require(resolve("katex"));
  const [{ unified }, { default: parse }, { default: math }] = await Promise.all(
    ["unified", "remark-parse", "remark-math"].map(name => import(pathToFileURL(resolve(name)).href)));
  processor = unified().use(parse).use(math);
  browser = await chromium.launch({ headless: true });
  page = await browser.newPage();
  // No network, app server, account, or model participates in these extractor tests.
  await page.route("**/*", route => route.abort());
});
test.after(async () => { await browser?.close(); });

function html(conclusion = "Therefore the sequence converges to zero.", mathVisibility = "") {
  return `<style>.sr-only{position:absolute;width:1px;height:1px;overflow:hidden;clip-path:inset(50%)}${mathVisibility}</style>
    <div data-proof-answer><p>The bound <span class="learner-math-source sr-only">\\frac{1}{n}</span>${katex.renderToString("\\frac{1}{n}")}
    controls the sequence.</p><p><strong>${conclusion}</strong></p></div>`;
}
async function observed() { return semanticTokens(await page.locator("[data-proof-answer]").evaluate(readRendered)); }
const source = "The bound $\\frac{1}{n}$ controls the sequence.\n\n**Therefore the sequence converges to zero.**";

test("actual Chromium reads prose and visible KaTeX once despite duplicate MathML", async () => {
  await page.setContent(html());
  assert.deepEqual(await observed(), sourceSemantics(source, processor));
  const raw = await page.locator("[data-proof-answer]").textContent();
  assert.ok(raw.length > "The bound controls the sequence. Therefore the sequence converges to zero.".length);
});

test("missing final conclusion and hidden conclusion cannot equal the saved source", async () => {
  await page.setContent(html(""));
  assert.notDeepEqual(await observed(), sourceSemantics(source, processor));
  await page.setContent(html());
  await page.locator("strong").evaluate(node => { node.style.visibility = "hidden"; });
  assert.notDeepEqual(await observed(), sourceSemantics(source, processor));
});

test("an accessible source without a visible formula fails, including opacity zero", async () => {
  await page.setContent(html(undefined, ".katex{visibility:hidden}"));
  await assert.rejects(observed(), /visible_math_missing/u);
  await page.setContent(html(undefined, ".katex{opacity:0}"));
  await assert.rejects(observed(), /visible_math_missing/u);
});

test("the same saved source has identical semantics after a fresh DOM reconstruction", async () => {
  await page.setContent(html());
  const before = await observed();
  await page.setContent(html());
  assert.deepEqual(await observed(), before);
  assert.deepEqual(before, sourceSemantics(source, processor));
});
