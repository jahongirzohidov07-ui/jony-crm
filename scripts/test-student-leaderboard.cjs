const { readFileSync } = require("node:fs");
const ts = require("typescript");
const assert = require("node:assert/strict");
const React = require("react");
const { renderToStaticMarkup } = require("react-dom/server");

function load(file, resolve = require) {
  const exports = {};
  const js = ts.transpileModule(readFileSync(file, "utf8"), {
    compilerOptions: { module: ts.ModuleKind.CommonJS, jsx: ts.JsxEmit.ReactJSX },
  }).outputText;
  new Function("exports", "require", js)(exports, resolve);
  return exports;
}
const helper = load("src/lib/studentLeaderboard.ts");
const standing = helper.leaderboardStanding;
let state;
const Page = load("src/pages/student/StudentLeaderboard.tsx", (id) => {
  if (id === "react") return { ...React, useState: () => [state.shift(), () => {}],
    useEffect: () => {}, useCallback: (fn) => fn };
  if (id === "react-router-dom") return { useSearchParams: () => [new URLSearchParams(), () => {}],
    Link: ({ to, children, ...props }) => React.createElement("a", { href: to, ...props }, children) };
  if (id.endsWith("/studentLeaderboard")) return helper;
  if (id.endsWith("/studentApi")) return { fmtNum: String };
  if (id.endsWith("/lang")) return { useLearningLanguage: () => "en" };
  if (id.endsWith("/Jsa")) return { JSA: {}, JsaLogo: () => null };
  if (id.endsWith("/StudentIcon")) return { StudentImage: () => null, StudentCoinIcon: () => null };
  if (id.endsWith("/StudentLoading")) return { StudentLoading: () => null };
  if (id.endsWith("/WordBoard")) return { WordBoard: () => null };
  if (id.endsWith("/api")) return { api: {} };
  if (id.endsWith("/wordbankApi")) return {};
  if (id.endsWith("/wordbankUi")) return {};
  return require(id);
}).default;

function render(rank, gap, extra = {}) {
  state = ["xp", "off", "group", "week", {
    podium: [], rows: [], total: 20, to_top10: gap,
    me: { rank, name: "Siz", points: 30, is_me: true }, ...extra,
  }, "", null];
  return renderToStaticMarkup(React.createElement(Page));
}
let cases = 0;
for (const rank of [null, undefined, 0, -1, 1.5, NaN, Infinity, 1, 2, 10, 11, 50]) {
  for (const gap of [null, undefined, 0, 25, -1, NaN, Infinity]) {
    const expected = Number.isInteger(rank) && rank >= 1 && rank <= 10;
    const result = standing(rank, gap);
    assert.equal(result.top10, expected);
    const html = render(rank, gap);
    assert.equal(html.includes("Siz eng yaxshi 10 talikdasiz"), expected);
    assert.ok(!html.includes("+10 Coin"));
    if (result.rank === null) {
      assert.ok(html.includes("Hali reytingda emassiz."));
      assert.ok(html.includes("Mashqni boshlash"));
      assert.ok(html.includes("—"));
      assert.ok(html.includes('href="/student/games"'));
    }
    assert.equal(html.includes("Yana 25 XP"), !expected && gap === 25);
    cases++;
  }
}
assert.ok(render(11, 0).includes("XP teng"));
assert.ok(!render(11, null).includes("XP teng"));
assert.ok(render(11, 25).includes("yetish uchun"));
assert.ok(!render(11, 25).includes("Top 10 gacha yana"));
assert.ok(render(null, 0, { total: 3 }).includes("Hali reytingda emassiz."));
assert.ok(!render(null, null, { me: null }).includes("Siz eng yaxshi"));
assert.ok(!render(null, null, { hint: "Reyting hali boshlanmadi", total: 0 }).includes("Siz eng yaxshi"));
assert.ok(render(null, null, { hint: "Reyting hali boshlanmadi", total: 0 }).includes("Mashqni boshlash"));
console.log(`Leaderboard: ${cases} rank/gap helper + rendered-page combinations and empty/missing-me cases PASS`);
