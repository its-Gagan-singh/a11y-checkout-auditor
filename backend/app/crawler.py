"""Opens a page in headless Chromium, runs axe-core, and collects images,
form fields and visible error messages for the extra checks.

Uses Playwright's *sync* API (run in a worker thread by FastAPI). This avoids
the asyncio/subprocess problems that the async API has on Windows."""

AXE_URL = "https://cdnjs.cloudflare.com/ajax/libs/axe-core/4.10.2/axe.min.js"
AXE_TAGS = ["wcag2a", "wcag2aa", "section508"]

_axe_source = None  # cached after first download

PAGE_DATA_JS = r"""
() => {
  const abs = (u) => { try { return new URL(u, document.baseURI).href; } catch (e) { return null; } };
  const sel = (el) => {
    let s = el.tagName.toLowerCase();
    if (el.id) s += '#' + el.id;
    else if (el.classList.length) s += '.' + el.classList[0];
    return s;
  };

  const images = [...document.querySelectorAll('img')].map((img) => ({
    selector: sel(img),
    src: abs(img.currentSrc || img.src),
    alt: img.getAttribute('alt'),
    width: img.naturalWidth || img.width || 0,
    height: img.naturalHeight || img.height || 0,
  }));

  const skipTypes = ['hidden', 'submit', 'button', 'image', 'reset'];
  const fields = [...document.querySelectorAll('input, select, textarea')]
    .filter((el) => !skipTypes.includes((el.getAttribute('type') || '').toLowerCase()))
    .map((el) => {
      const byFor = el.id ? document.querySelector('label[for="' + CSS.escape(el.id) + '"]') : null;
      const wrap = el.closest('label');
      const ids = (el.getAttribute('aria-labelledby') || '').split(/\s+/).filter(Boolean);
      const labelledby = ids.map((i) => (document.getElementById(i) || {}).textContent || '').join(' ');
      const label = ((byFor && byFor.textContent) || (wrap && wrap.textContent) ||
                     el.getAttribute('aria-label') || labelledby || el.getAttribute('title') || '')
                    .replace(/\s+/g, ' ').trim();
      return {
        selector: sel(el),
        type: (el.getAttribute('type') || el.tagName).toLowerCase(),
        name: el.getAttribute('name') || '',
        id: el.id || '',
        autocomplete: el.getAttribute('autocomplete') || '',
        placeholder: el.getAttribute('placeholder') || '',
        label: label,
      };
    });

  const errSel = '[role="alert"], [aria-live="assertive"], [aria-live="polite"], .error, .errors, ' +
                 '.invalid-feedback, [class*="error"], [class*="invalid"]';
  const seen = new Set();
  const errors = [];
  document.querySelectorAll(errSel).forEach((el) => {
    const text = (el.textContent || '').replace(/\s+/g, ' ').trim();
    if (text && text.length < 200 && !seen.has(text)) { seen.add(text); errors.push({ selector: sel(el), text: text }); }
  });

  return { images, fields, errors, title: document.title, lang: document.documentElement.lang || '' };
}
"""


def audit_page(url: str) -> dict:
    global _axe_source
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch()
        try:
            # bypass_csp lets us inject axe-core even on pages with strict CSP
            context = browser.new_context(bypass_csp=True)
            page = context.new_page()
            page.goto(url, wait_until="load", timeout=30000)

            if _axe_source is None:
                _axe_source = page.request.get(AXE_URL).text()
            page.add_script_tag(content=_axe_source)

            axe_results = page.evaluate(
                "(tags) => axe.run(document, { runOnly: { type: 'tag', values: tags } })",
                AXE_TAGS,
            )
            page_data = page.evaluate(PAGE_DATA_JS)
        finally:
            browser.close()

    return {
        "url": url,
        "axe_violations": [
            {
                "id": v["id"],
                "impact": v.get("impact") or "minor",
                "help": v["help"],
                "help_url": v["helpUrl"],
                "elements_affected": len(v["nodes"]),
            }
            for v in axe_results["violations"]
        ],
        **page_data,
    }
