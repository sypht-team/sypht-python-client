from typing import Any, Callable, Iterator, List


def fetch_all_pages(
    name: str,
    fetch_page: Callable[..., Any],
    get_page: Callable[..., List[Any]] = lambda x: x,
    rec_limit=20000,
) -> Callable[..., Iterator[Any]]:
    """Returns an iterator that calls fetch_page with an offset that we increment by the number of pages fetched.  Stop if page returns empty list.

    :param fetch_page: the api call that takes an offset (zero-based) that fetches a page of results
    :param get_page: a function that extracts the page from the response
    """

    def fetch_all_pages(*args, **kwargs) -> Iterator[List[Any]]:
        page_count = 0
        recs = 0
        while True:
            page_count += 1
            if recs > rec_limit:
                # Don't want to DOS ourselves...
                raise Exception(
                    f"fetch_all_pages({name}): fetched more than {rec_limit} items.  Consider using adding or adjusting a filter to reduce the number of items fetched."
                )
            try:
                response = fetch_page(
                    *args,
                    **kwargs,
                    offset=page_count - 1,
                )
            except Exception as err:
                raise Exception(
                    f"Failed fetching for {name} for offset={page_count - 1}"
                ) from err
            try:
                page = get_page(response)
            except Exception as err:
                raise Exception(
                    f"get_page failed to extract page from response for {name} for offset={page_count - 1}"
                ) from err
            if len(page) == 0:
                break
            recs += len(page)
            yield response

    return fetch_all_pages
