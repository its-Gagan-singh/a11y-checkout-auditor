from backend.app.report import build_report

RAW = {
    "url": "https://shop.example/checkout",
    "title": "Checkout",
    "axe_violations": [
        {"id": "color-contrast", "impact": "serious", "help": "Elements must have sufficient color contrast",
         "help_url": "https://example.com", "elements_affected": 4},
        {"id": "some-unknown-rule", "impact": "minor", "help": "Something odd",
         "help_url": "https://example.com", "elements_affected": 1},
    ],
    "images": [{"selector": "img.logo", "src": "https://shop.example/logo.png", "alt": None}],
    "fields": [{"selector": "input#cc", "type": "text", "name": "cc", "id": "cc",
                "autocomplete": "cc-number", "placeholder": "", "label": ""}],
    "errors": [{"selector": "div.error", "text": "Invalid input"}],
}


def test_report_structure_and_counts():
    r = build_report(RAW)
    assert r["url"] == RAW["url"]
    assert 0 <= r["score"] < 100
    assert r["grade"] in "ABCDF"
    assert r["summary"]["images_missing_alt"] == 1
    assert r["summary"]["label_issues"] == 1
    assert r["summary"]["vague_error_messages"] == 1
    assert r["summary"]["total_issues"] == 5


def test_fixes_are_sorted_by_priority():
    priorities = [f["priority"] for f in build_report(RAW)["fixes"]]
    assert priorities == sorted(priorities, reverse=True)


def test_auto_fix_percentage_counts_only_issues_with_suggestions():
    # 5 issues, 1 (unknown axe rule) has no concrete suggestion -> 80%
    assert build_report(RAW)["summary"]["auto_fix_pct"] == 80


def test_clean_page():
    r = build_report({"url": "https://ok.example", "axe_violations": [], "images": [], "fields": [], "errors": []})
    assert r["score"] == 100 and r["summary"]["auto_fix_pct"] == 100
