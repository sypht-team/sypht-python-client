import pytest

from sypht.util import fetch_all_pages


def test_fetch_all_pages_can_fetch_one_page():
    # arrange
    page_size = 5

    def fetch_something(offset, pages=1):
        pages0 = pages - 1
        if offset > pages0:
            return []
        start = offset * page_size
        page = range(start, start + page_size)
        return list(page)

    # act
    page_iter = fetch_all_pages(name="test1", fetch_page=fetch_something)
    results = []
    for page in page_iter(pages=1):
        results += page

    # assert
    assert results == [0, 1, 2, 3, 4]


def test_fetch_all_pages_can_fetch_several_pages():
    # arrange
    page_size = 5

    def fetch_something(offset, pages=1):
        pages0 = pages - 1
        if offset > pages0:
            return []
        start = offset * page_size
        page = range(start, start + page_size)
        return list(page)

    # act
    page_iter = fetch_all_pages(name="test1", fetch_page=fetch_something)
    results = []
    for page in page_iter(pages=2):
        results += page

    # assert
    assert results == [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]


def test_fetch_all_pages_never_ending():
    """Fail if fetch more than n pages."""
    # arrange
    def never_ending(*args, **kwargs):
        return [0, 1, 2]

    # act
    page_iter = fetch_all_pages(name="test1", fetch_page=never_ending)
    results = []
    with pytest.raises(Exception) as exc_info:
        for page in page_iter():
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
        for page in page_iter():
            results += page

    # assert
    assert "fetch error" in str(exc_info.value.__cause__)
    assert "Failed fetching for test1" in str(exc_info)
