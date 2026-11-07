# Checkout Auditor

AI-assisted accessibility auditor for payment and checkout pages. Paste a URL and get a
WCAG 2.0 / Section 508 score plus a ranked list of fixes written in plain language.

![CI](https://github.com/its-Gagan-singh/a11y-checkout-auditor/actions/workflows/ci.yml/badge.svg)
![License](https://img.shields.io/badge/license-MIT-blue)

<!-- Add after you record/deploy: [Live demo](link) | [Demo video](link) -->

## Why this exists

Checkout pages are where accessibility failures cost the most: a missing label on a card
field or a vague error message can stop a screen-reader or keyboard user from paying at all.
Manual audits are slow, so this tool automates the first pass.

## What it does

- Runs **axe-core** in headless Chromium (Playwright) against WCAG 2.0 A/AA and Section 508 rules.
- Flags form fields with **no label, placeholder-only labels, or generic labels**, and suggests
  clearer ones (for example `cc-number` becomes "Card number").
- Flags **vague error messages** ("Invalid input") and suggests the kind of message that helps.
- Suggests **alt text** for images that have none. By default it uses a file-name heuristic;
  with `USE_ML_ALT=1` it uses the **BLIP image-captioning model**.
- Produces a **0-100 risk score**, a grade, and a fix list ranked by impact and how many
  elements are affected.
- Web dashboard built to be accessible itself: skip link, labelled form, live status
  announcements, visible focus, no colour-only meaning, dark mode, reduced-motion support.

## Screenshots

![Dashboard](docs/screenshots/dashboard.png)

## Architecture

```
Browser dashboard (HTML/CSS/JS)
        |  POST /audit {url}
        v
FastAPI --> security check (blocks private/localhost addresses)
        --> crawler.py: Playwright + axe-core + page data (images, fields, errors)
        --> report.py : scoring.py + ml/label_check.py + ml/alt_text.py
        v
JSON report (score, grade, ranked fixes)
```

## Quick start

```bash
git clone https://github.com/its-Gagan-singh/a11y-checkout-auditor.git
cd a11y-checkout-auditor
python -m venv venv
venv\Scripts\activate          # Mac/Linux: source venv/bin/activate
pip install -r backend/requirements.txt
playwright install chromium
uvicorn backend.app.main:app --reload
```

Open http://127.0.0.1:8000 for the dashboard or http://127.0.0.1:8000/docs for the API.

### Optional: real image-captioning model

```bash
pip install -r backend/requirements-ml.txt
set USE_ML_ALT=1               # Mac/Linux: export USE_ML_ALT=1
```

### Docker

```bash
docker build -t checkout-auditor .
docker run -p 8000:8000 checkout-auditor
```

## Tests

```bash
pytest
```

The tests cover scoring, label and error checks, alt-text suggestions, report building,
URL safety and the API. They run without a browser.

## Results

See [docs/results.md](docs/results.md). Generate it yourself with:

```bash
python -m scripts.batch_audit
```

## Limitations

- Automated tools catch only part of the accessibility problems. Always also test with a
  screen reader (NVDA, TalkBack) and keyboard only.
- Pages behind a login or bot protection cannot be audited.
- Heuristic label/error checks are rule-based and English-only.
- Use only on public demo pages and never enter real card details.

## Roadmap

- Multi-step checkout flows (fill the form, audit each step)
- Keyboard-trap and focus-order checks
- Export the report as PDF/CSV
- Compare before/after audits

## Tech stack

Python, FastAPI, Playwright, axe-core, Hugging Face Transformers (optional), HTML/CSS/JS, Docker, GitHub Actions.

## License

MIT
