"""Turns raw crawler output into the final audit report (pure Python, easy to test)."""
from .ml.alt_text import suggest_alt_text
from .ml.label_check import check_errors, check_labels
from .scoring import FIX_HINTS, IMPACT_WEIGHT, grade, score_page, violation_penalty


def build_report(raw: dict, use_ml: bool = False) -> dict:
    violations = raw.get("axe_violations", [])
    label_issues = check_labels(raw.get("fields", []))
    error_issues = check_errors(raw.get("errors", []))
    alt_suggestions = suggest_alt_text(raw.get("images", []), use_ml=use_ml)

    fixes = []
    for v in violations:
        hint = FIX_HINTS.get(v["id"])
        fixes.append({
            "source": "axe-core", "rule": v["id"], "impact": v["impact"],
            "priority": round(violation_penalty(v), 1),
            "problem": v["help"], "fix": hint or "See the rule documentation for how to fix this.",
            "has_suggestion": hint is not None,
            "elements_affected": v["elements_affected"], "help_url": v["help_url"],
        })
    for i in label_issues:
        impact = "serious" if i["problem"] == "Form field has no label" else "moderate"
        fixes.append({
            "source": "label-check", "rule": "form-label", "impact": impact,
            "priority": float(IMPACT_WEIGHT[impact]), "problem": f'{i["problem"]}: {i["selector"]}',
            "fix": f'Use the label: "{i["suggestion"]}"', "has_suggestion": True,
            "elements_affected": 1, "help_url": None,
        })
    for e in error_issues:
        fixes.append({
            "source": "error-check", "rule": "error-message", "impact": "moderate",
            "priority": 3.0, "problem": f'Vague error message: "{e["current"]}"',
            "fix": e["suggestion"], "has_suggestion": True, "elements_affected": 1, "help_url": None,
        })
    for a in alt_suggestions:
        fixes.append({
            "source": "alt-text", "rule": "image-alt", "impact": "serious",
            "priority": float(IMPACT_WEIGHT["serious"]),
            "problem": f'Image without alt text: {a["src"]}',
            "fix": f'Use alt="{a["suggestion"]}"', "has_suggestion": True,
            "elements_affected": 1, "help_url": None, "method": a["method"],
        })
    fixes.sort(key=lambda f: f["priority"], reverse=True)

    by_impact = {k: 0 for k in IMPACT_WEIGHT}
    for f in fixes:
        by_impact[f["impact"]] = by_impact.get(f["impact"], 0) + 1
    with_suggestion = sum(1 for f in fixes if f["has_suggestion"])
    score = score_page(violations, label_issues, error_issues)

    return {
        "url": raw.get("url"),
        "title": raw.get("title", ""),
        "score": score,
        "grade": grade(score),
        "summary": {
            "total_issues": len(fixes),
            "by_impact": by_impact,
            "images_missing_alt": len(alt_suggestions),
            "label_issues": len(label_issues),
            "vague_error_messages": len(error_issues),
            "auto_fix_pct": round(100 * with_suggestion / len(fixes)) if fixes else 100,
            "ml_alt_text": use_ml,
        },
        "fixes": fixes,
        "alt_suggestions": alt_suggestions,
        "label_issues": label_issues,
        "error_issues": error_issues,
    }
