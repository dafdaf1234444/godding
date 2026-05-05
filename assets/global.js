/* godding/assets/global.js — runs on every page.
   Adds a quick-search chip to .topbar and a "/" keyboard shortcut.
   Pure DOM. No dependencies. */
(function () {
  // figure out the path prefix to /pages/search.html
  function searchUrl(q) {
    const here = location.pathname;
    // pages live under /pages/ — relative path differs for home vs sub-pages
    const prefix = (/\/pages\//i.test(here) || here.endsWith("/pages")) ? "" : "pages/";
    const u = prefix + "search.html";
    return q ? u + "?q=" + encodeURIComponent(q) : u;
  }

  function injectChip() {
    const tb = document.querySelector(".topbar");
    if (!tb || tb.querySelector(".qsearch")) return;
    const a = document.createElement("a");
    a.className = "qsearch";
    a.href = searchUrl("");
    a.title = "search godding · / to focus";
    a.innerHTML = 'search <span class="kbd">/</span>';
    tb.appendChild(a);
  }

  function bindKey() {
    document.addEventListener("keydown", function (e) {
      // "/" jumps to search unless we're typing somewhere
      if (e.key !== "/") return;
      const t = e.target;
      if (t && (t.tagName === "INPUT" || t.tagName === "TEXTAREA" || t.isContentEditable)) return;
      e.preventDefault();
      location.href = searchUrl("");
    });
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", () => { injectChip(); bindKey(); });
  } else {
    injectChip(); bindKey();
  }
})();
