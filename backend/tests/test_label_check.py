from backend.app.ml.label_check import check_errors, check_labels, suggest_label


def field(**kw):
    base = {"selector": "input#x", "type": "text", "name": "", "id": "",
            "autocomplete": "", "placeholder": "", "label": ""}
    base.update(kw)
    return base


def test_missing_label_uses_autocomplete_for_suggestion():
    issues = check_labels([field(autocomplete="cc-number")])
    assert issues[0]["problem"] == "Form field has no label"
    assert issues[0]["suggestion"] == "Card number"


def test_placeholder_only_is_flagged():
    issues = check_labels([field(placeholder="Enter CVV")])
    assert "Placeholder" in issues[0]["problem"]
    assert issues[0]["suggestion"] == "Security code (CVV)"


def test_generic_label_is_flagged():
    issues = check_labels([field(label="Input", name="email")])
    assert issues[0]["problem"] == "Label is too generic"
    assert issues[0]["suggestion"] == "Email address"


def test_good_label_is_not_flagged():
    assert check_labels([field(label="Card number")]) == []


def test_suggest_label_from_field_name():
    assert suggest_label(field(name="card_number")) == "Card number"


def test_vague_errors_are_flagged_and_clear_ones_are_not():
    errors = [
        {"selector": "div.error", "text": "Invalid input"},
        {"selector": "div.error", "text": "Something went wrong."},
        {"selector": "div.error", "text": "Enter a 16-digit card number."},
    ]
    flagged = check_errors(errors)
    assert [e["current"] for e in flagged] == ["Invalid input", "Something went wrong."]
