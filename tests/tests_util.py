import pytest

from sypht.util import DEFAULT_REC_LIMIT, fetch_all_pages


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


def test_fetch_all_pages_can_fetch_one_page_with_get_page():
    # arrange
    page_size = 5

    def fetch_something(offset, pages=1):
        pages0 = pages - 1
        if offset > pages0:
            return {"results": []}
        start = offset * page_size
        page = range(start, start + page_size)
        return {"results": list(page)}

    # act
    page_iter = fetch_all_pages(
        name="test1", fetch_page=fetch_something, get_page=lambda resp: resp["results"]
    )
    results = []
    for resp in page_iter(pages=1):
        results += resp["results"]

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
    assert f"more than the limit: {DEFAULT_REC_LIMIT}" in str(exc_info)


def test_fetch_with_rec_limit():
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
    page_iter = fetch_all_pages(name="test1", fetch_page=fetch_something, rec_limit=2)
    results = []
    with pytest.raises(Exception) as exc_info:
        for page in page_iter():
            results += page

    # assert
    assert f"fetched 5 records which is more than the limit: 2" in str(exc_info)


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
