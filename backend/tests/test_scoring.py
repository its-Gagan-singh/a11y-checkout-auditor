from backend.app.scoring import grade, score_page, violation_penalty


def test_clean_page_scores_100():
    assert score_page([], [], []) == 100


def test_more_severe_violations_lower_the_score():
    minor = [{"id": "x", "impact": "minor", "elements_affected": 1}]
    critical = [{"id": "x", "impact": "critical", "elements_affected": 1}]
    assert score_page(critical, [], []) < score_page(minor, [], [])


def test_penalty_grows_with_elements_but_is_capped():
    one = violation_penalty({"impact": "serious", "elements_affected": 1})
    many = violation_penalty({"impact": "serious", "elements_affected": 10})
    huge = violation_penalty({"impact": "serious", "elements_affected": 5000})
    assert one < many < huge
    assert huge == violation_penalty({"impact": "serious", "elements_affected": 16})


def test_score_never_below_zero():
    bad = [{"id": "x", "impact": "critical", "elements_affected": 50}] * 20
    assert score_page(bad, [], []) == 0


def test_grades():
    assert grade(95) == "A"
    assert grade(82) == "B"
    assert grade(70) == "C"
    assert grade(55) == "D"
    assert grade(10) == "F"
