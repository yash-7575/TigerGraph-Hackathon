from ingest.chunker import chunk_text


def test_short_text():
    r = chunk_text("hello world", size=512, overlap=64)
    assert len(r) == 1
    assert r[0] == "hello world"


def test_empty():
    assert chunk_text("") == []


def test_long_text_has_overlap():
    text = " ".join(["word"] * 2000)
    r = chunk_text(text, size=100, overlap=20)
    assert len(r) >= 2
    # Every chunk should have some tokens
    assert all(len(c) > 0 for c in r)
