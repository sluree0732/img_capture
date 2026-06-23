from collector import dedupe_preserve_order, oldest_first


def test_dedupe_preserve_order_removes_duplicates_keeps_first_order():
    links = ["a", "b", "a", "c", "b"]
    assert dedupe_preserve_order(links) == ["a", "b", "c"]


def test_dedupe_preserve_order_handles_empty_list():
    assert dedupe_preserve_order([]) == []


def test_oldest_first_reverses_list():
    links = ["newest", "middle", "oldest"]
    assert oldest_first(links) == ["oldest", "middle", "newest"]


def test_oldest_first_handles_empty_list():
    assert oldest_first([]) == []


def test_oldest_first_does_not_mutate_input():
    links = ["newest", "oldest"]
    oldest_first(links)
    assert links == ["newest", "oldest"]
