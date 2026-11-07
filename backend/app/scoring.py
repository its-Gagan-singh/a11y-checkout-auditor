"""Risk scoring and plain-English fix hints."""
import math

IMPACT_WEIGHT = {"critical": 10, "serious": 6, "moderate": 3, "minor": 1}

# Concrete fixes for the axe-core rules that show up most often on checkout pages.
FIX_HINTS = {
    "image-alt": "Add a short alt attribute describing the image (alt=\"\" if purely decorative).",
    "label": "Give every form field a visible <label for=\"id\"> (not just a placeholder).",
    "color-contrast": "Increase text/background contrast to at least 4.5:1 (3:1 for large text).",
    "button-name": "Give the button visible text or an aria-label that says what it does.",
    "link-name": "Give the link descriptive text (avoid 'click here').",
    "html-has-lang": "Add a lang attribute to <html>, e.g. <html lang=\"en\">.",
    "document-title": "Add a unique, descriptive <title> to the page.",
    "select-name": "Associate a <label> with the select (dropdown) element.",
    "input-image-alt": "Add alt text to image buttons so the action is announced.",
    "duplicate-id": "Make every id on the page unique.",
    "frame-title": "Add a title attribute to each iframe describing its content.",
    "autocomplete-valid": "Use a valid autocomplete value (e.g. cc-number) so browsers and assistive tools can fill the field.",
    "aria-allowed-attr": "Remove ARIA attributes that are not allowed on this element.",
    "heading-order": "Use heading levels in order (h1, then h2, then h3) without skipping.",
    "landmark-one-main": "Wrap the main content in a single <main> landmark.",
    "region": "Put page content inside landmarks (header, nav, main, footer).",
    "meta-viewport": "Do not disable zoom: remove user-scalable=no / maximum-scale=1.",
    "tabindex": "Avoid positive tabindex values; use the natural DOM order.",
    "target-size": "Make touch targets at least 24x24 px (44x44 px is better on mobile).",
}


def violation_penalty(v: dict) -> float:
    weight = IMPACT_WEIGHT.get(v.get("impact", "minor"), 1)
    return weight * math.sqrt(min(v.get("elements_affected", 1), 16))


def score_page(violations: list, label_issues: list, error_issues: list) -> int:
    penalty = sum(violation_penalty(v) for v in violations)
    # Vague labels / vague error text are not detectable by axe, so count them here.
    # (Fully missing labels are already counted through axe's "label" rule.)
    penalty += 2 * sum(1 for i in label_issues if i["problem"] != "Form field has no label")
    penalty += 1.5 * len(error_issues)
    return max(0, round(100 - penalty))


def grade(score: int) -> str:
    for threshold, letter in ((90, "A"), (80, "B"), (65, "C"), (50, "D")):
        if score >= threshold:
            return letter
    return "F"
