import pytest

from sypht.util import fetch_all_pages


def test_fetch_all_pages_can_fetch_one_page():
    # arrange
    num_pages = 1

    def fetch_something(offset, n=0):
        result = range(offset + n, offset + n + 3)
        if offset > (len(result) * num_pages) - 1:
            return []
        return result

    # act
    page_iter = fetch_all_pages(name="test1", fetch_page=fetch_something)
    results = []
    for page in page_iter(n=10):
        results += page

    # assert
    assert results == [10, 11, 12]


def test_fetch_all_pages_can_fetch_several_pages():
    # arrange
    num_pages = 3

    def fetch_something(offset, n=0):
        result = range(offset + n, offset + n + 3)
        if offset > (len(result) * num_pages) - 1:
            return []
        return result

    # act
    page_iter = fetch_all_pages(name="test1", fetch_page=fetch_something)
    results = []
    for page in page_iter(n=2):
        results += page

    # assert
    assert results == [2, 3, 4, 5, 6, 7, 8, 9, 10]


def test_fetch_all_pages_never_ending():
    """Fail if fetch more than n pages."""
    # arrange
    def never_ending(*args, **kwargs):
        return [0, 1, 2]

    # act
    page_iter = fetch_all_pages(name="test1", fetch_page=never_ending)
    results = []
    with pytest.raises(Exception) as exc_info:
        for page in page_iter(n=2):
            results += page

    # assert
    assert "fetched more than 1000 pages" in str(exc_info)


def test_fetch_all_pages_handle_error():
    # arrange
    def failing(*args, **kwargs):
        raise Exception("fetch error")

    # act
    page_iter = fetch_all_pages(name="test1", fetch_page=failing)
    results = []
    with pytest.raises(Exception) as exc_info:
        for page in page_iter(n=2):
            results += page

    # assert
    assert "fetch error" in str(exc_info.value.__cause__)
    assert "Failed fetching for test1" in str(exc_info)
