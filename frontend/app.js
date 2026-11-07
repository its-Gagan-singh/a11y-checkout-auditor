(function () {
  "use strict";

  const SAMPLE_URL = "https://www.w3.org/WAI/demos/bad/before/home.html";

  const form = document.getElementById("audit-form");
  const urlInput = document.getElementById("url");
  const urlError = document.getElementById("url-error");
  const submitBtn = document.getElementById("submit-btn");
  const sampleBtn = document.getElementById("sample-btn");
  const statusEl = document.getElementById("status");
  const results = document.getElementById("results");
  const resultsHeading = document.getElementById("results-heading");

  // All page content comes from untrusted sites, so it is only ever inserted
  // with textContent (never innerHTML).
  function el(tag, props, children) {
    const node = document.createElement(tag);
    Object.entries(props || {}).forEach(([key, value]) => {
      if (key === "text") node.textContent = value;
      else node.setAttribute(key, value);
    });
    (children || []).forEach((child) => node.appendChild(child));
    return node;
  }

  function setStatus(message, isError) {
    statusEl.textContent = message;
    statusEl.classList.toggle("error", Boolean(isError));
  }

  function showFieldError(message) {
    urlError.textContent = message;
    urlError.hidden = !message;
    urlInput.setAttribute("aria-invalid", message ? "true" : "false");
  }

  function renderReport(report) {
    document.getElementById("r-url").textContent = report.url + (report.title ? " (" + report.title + ")" : "");
    document.getElementById("r-score").textContent = report.score + " / 100";
    document.getElementById("r-grade").textContent = "Grade " + report.grade;

    const s = report.summary;
    const lines = [
      ["Issues found", s.total_issues],
      ["Critical", s.by_impact.critical],
      ["Serious", s.by_impact.serious],
      ["Moderate", s.by_impact.moderate],
      ["Minor", s.by_impact.minor],
      ["Images missing alt text", s.images_missing_alt],
      ["Unclear form labels", s.label_issues],
      ["Vague error messages", s.vague_error_messages],
      ["Issues with a suggested fix", s.auto_fix_pct + "%"],
    ];
    const dl = document.getElementById("r-lines");
    dl.replaceChildren(...lines.map(([label, value]) =>
      el("div", {}, [el("dt", { text: label }), el("dd", { text: String(value) })])
    ));

    const list = document.getElementById("fix-list");
    if (report.fixes.length === 0) {
      list.replaceChildren(el("li", { text: "No automated issues found. Now test with a screen reader and keyboard." }));
    } else {
      list.replaceChildren(...report.fixes.map((fix) => {
        const children = [
          el("p", { class: "fix-head" }, [
            el("span", { class: "impact", text: fix.impact[0].toUpperCase() + fix.impact.slice(1) }),
            el("span", { class: "fix-source", text: fix.source + (fix.elements_affected > 1 ? ", " + fix.elements_affected + " elements" : "") }),
          ]),
          el("p", { text: fix.problem }),
          el("p", { class: "how", text: "Fix: " + fix.fix }),
        ];
        if (fix.help_url && /^https:\/\//.test(fix.help_url)) {
          children.push(el("p", {}, [el("a", { href: fix.help_url, target: "_blank", rel: "noopener noreferrer", text: "Rule documentation (opens in a new tab)" })]));
        }
        return el("li", { class: "fix", "data-impact": fix.impact }, children);
      }));
    }

    const altBlock = document.getElementById("alt-block");
    const altList = document.getElementById("alt-list");
    altBlock.hidden = report.alt_suggestions.length === 0;
    altList.replaceChildren(...report.alt_suggestions.map((a) =>
      el("li", { text: a.src + " -> alt=\"" + a.suggestion + "\" (" + a.method + ")" })
    ));

    results.hidden = false;
    resultsHeading.focus();
  }

  async function runAudit(url) {
    showFieldError("");
    submitBtn.disabled = true;
    results.hidden = true;
    setStatus("Auditing the page. This usually takes 10 to 30 seconds.");
    try {
      const response = await fetch("/audit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ url: url }),
      });
      const data = await response.json().catch(() => ({}));
      if (!response.ok) {
        const detail = typeof data.detail === "string" ? data.detail : "Enter a full address starting with https://";
        throw new Error(detail);
      }
      setStatus("Audit complete.");
      renderReport(data);
    } catch (err) {
      setStatus(err.message || "Something went wrong. Check the address and try again.", true);
    } finally {
      submitBtn.disabled = false;
    }
  }

  form.addEventListener("submit", (event) => {
    event.preventDefault();
    const value = urlInput.value.trim();
    if (!/^https?:\/\/.+\..+/.test(value)) {
      showFieldError("Enter a full page address that starts with http:// or https://");
      urlInput.focus();
      return;
    }
    runAudit(value);
  });

  sampleBtn.addEventListener("click", () => {
    urlInput.value = SAMPLE_URL;
    runAudit(SAMPLE_URL);
  });
})();
