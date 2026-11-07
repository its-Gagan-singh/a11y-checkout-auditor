from backend.app.ml.alt_text import heuristic_alt, suggest_alt_text


def test_heuristic_uses_file_name():
    assert heuristic_alt("https://x.com/img/visa-logo.png") == "Visa logo"


def test_heuristic_falls_back_for_hashed_names():
    assert "Describe" in heuristic_alt("https://x.com/a/3f9a1c7be2d4.jpg")


def test_only_images_without_alt_get_suggestions():
    images = [
        {"selector": "img.a", "src": "https://x.com/cart-icon.png", "alt": None},
        {"selector": "img.b", "src": "https://x.com/logo.png", "alt": "Company logo"},
        {"selector": "img.c", "src": "https://x.com/spacer.gif", "alt": ""},  # decorative
    ]
    out = suggest_alt_text(images)
    assert len(out) == 1
    assert out[0]["selector"] == "img.a"
    assert out[0]["method"] == "filename-heuristic"
