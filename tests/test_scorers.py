from bench.scorers import exact_match, normalize, recall_at_k


def test_normalize_number_word():
    assert normalize("Five") == "5"
    assert normalize("the FIVE bikes") == "5 bikes"


def test_exact_match_numeric():
    assert exact_match("5", ["5"])
    assert exact_match("Five", ["5"])
    assert exact_match("The answer is 5", ["5"])


def test_exact_match_name():
    assert exact_match("Chen Ding", ["Chen Ding"])
    assert exact_match("chen ding won gold", ["Chen Ding"])


def test_exact_match_negative():
    assert not exact_match("Usain Bolt", ["Chen Ding"])


def test_recall_at_k():
    assert recall_at_k(["a", "b"], ["a", "b", "c"]) == 2 / 3
    assert recall_at_k([], ["a"]) == 0.0
    assert recall_at_k(["a"], []) == 1.0


def test_recall_dedup():
    assert recall_at_k(["a", "a", "b"], ["a", "b"]) == 1.0
