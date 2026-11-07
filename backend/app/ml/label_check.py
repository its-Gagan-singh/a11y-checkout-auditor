"""Rule-based NLP checks for form labels and error messages on checkout pages.
Flags missing / placeholder-only / vague labels and vague error messages, and
suggests clearer wording."""
import re

# autocomplete token -> friendly label
AUTOCOMPLETE_LABELS = {
    "cc-number": "Card number",
    "cc-exp": "Expiry date (MM/YY)",
    "cc-exp-month": "Expiry month",
    "cc-exp-year": "Expiry year",
    "cc-csc": "Security code (CVV)",
    "cc-name": "Name on card",
    "email": "Email address",
    "tel": "Phone number",
    "postal-code": "Postal code",
    "street-address": "Street address",
    "address-line1": "Address line 1",
    "address-line2": "Address line 2",
    "given-name": "First name",
    "family-name": "Last name",
    "name": "Full name",
    "username": "Username",
    "current-password": "Password",
    "new-password": "New password",
}

# keywords in name/id/placeholder -> friendly label
KEYWORD_LABELS = [
    ("cardnumber", "Card number"), ("card_number", "Card number"), ("card-number", "Card number"),
    ("ccnum", "Card number"), ("cvv", "Security code (CVV)"), ("cvc", "Security code (CVV)"),
    ("expiry", "Expiry date (MM/YY)"), ("exp", "Expiry date (MM/YY)"),
    ("cardname", "Name on card"), ("email", "Email address"), ("phone", "Phone number"),
    ("zip", "Postal code"), ("postal", "Postal code"), ("pincode", "Postal code"),
    ("address", "Street address"), ("city", "City"), ("state", "State"),
    ("first", "First name"), ("last", "Last name"), ("name", "Full name"),
    ("password", "Password"), ("coupon", "Coupon code"), ("promo", "Promo code"),
]

GENERIC_LABELS = {
    "input", "field", "text", "textbox", "value", "enter", "enter value",
    "type here", "untitled", "label", "your input", "select", "choose",
}

VAGUE_ERROR = re.compile(
    r"^(invalid( input| value| entry| data)?|error|errors?!?|incorrect|wrong|failed|"
    r"something went wrong|try again|oops.*|required|not valid|bad input)[\s.!]*$",
    re.IGNORECASE,
)

ERROR_EXAMPLE = (
    "Say what went wrong and how to fix it, e.g. 'Enter a 16-digit card number "
    "with no spaces.'"
)


def _humanize(text: str) -> str:
    text = re.sub(r"[\[\]_\-.]+", " ", text)
    text = re.sub(r"([a-z])([A-Z])", r"\1 \2", text).strip()
    return text.capitalize() if text else ""


def suggest_label(field: dict) -> str:
    token = (field.get("autocomplete") or "").split()[-1:] or [""]
    if token[0] in AUTOCOMPLETE_LABELS:
        return AUTOCOMPLETE_LABELS[token[0]]
    haystack = " ".join(
        [field.get("name", ""), field.get("id", ""), field.get("placeholder", "")]
    ).lower()
    for key, label in KEYWORD_LABELS:
        if key in haystack:
            return label
    guess = _humanize(field.get("placeholder") or field.get("name") or field.get("id") or "")
    return guess or "Describe what to enter here"


def check_labels(fields: list) -> list:
    issues = []
    for f in fields:
        label = (f.get("label") or "").strip()
        if not label:
            problem = (
                "Placeholder used as the only label (it disappears while typing)"
                if f.get("placeholder")
                else "Form field has no label"
            )
            issues.append({
                "selector": f["selector"], "problem": problem, "current": f.get("placeholder") or "",
                "suggestion": suggest_label(f),
            })
        elif label.lower().strip(" :*") in GENERIC_LABELS or len(label) < 2:
            issues.append({
                "selector": f["selector"], "problem": "Label is too generic",
                "current": label, "suggestion": suggest_label(f),
            })
    return issues


def check_errors(errors: list) -> list:
    issues = []
    for e in errors:
        text = e["text"].strip()
        if VAGUE_ERROR.match(text):
            issues.append({
                "selector": e["selector"], "problem": "Error message is vague",
                "current": text, "suggestion": ERROR_EXAMPLE,
            })
    return issues
