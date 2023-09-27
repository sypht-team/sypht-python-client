import logging
from typing import Any, Callable, Iterator, List

DEFAULT_REC_LIMIT = 100_000


def fetch_all_pages(
    name: str,
    fetch_page: Callable[..., Any],
    get_page: Callable[..., List[Any]] = lambda x: x,
    rec_limit=DEFAULT_REC_LIMIT,
) -> Callable[..., Iterator[Any]]:
    """Returns an iterator that calls fetch_page with an offset that we increment by the number of pages fetched.  Stop if page returns empty list.

    :param fetch_page: a function that makes an api call to fetch a page of results (using zero-based offset)
    :param get_page: a function that extracts the page from the response which should be a list
    """

    # Enforce a default so that the loop will stop.
    if rec_limit is None:
        rec_limit = DEFAULT_REC_LIMIT

    def fetch_all_pages(*args, **kwargs) -> Iterator[Any]:
        page_count = 0
        recs = 0
        while True:
            page_count += 1
            if recs > rec_limit:
                # Don't want to DOS ourselves...
                raise Exception(
                    f"fetch_all_pages({name}): fetched {recs} records which is more than the limit: {rec_limit} .  Consider adding or adjusting a filter to reduce the total number of items fetched."
                )
            try:
                response = fetch_page(
                    *args,
                    **kwargs,
                    offset=page_count - 1,
                )
            except Exception as err:
                raise Exception(
                    f"Failed fetching for {name} for offset={page_count - 1} (page={page_count}) (records fetched so far:{recs}). Cause: {err}"
                ) from err
            try:
                page = get_page(response)
            except Exception as err:
                raise Exception(
                    f"get_page failed to extract page from response for {name} for offset={page_count - 1} (page={page_count}) (records fetched so far:{recs}). Cause: {err}"
                ) from err
            if len(page) == 0:
                break
            recs += len(page)
            logging.info(
                f"fetch_all_pages({name}): fetched page {page_count} (records={recs})"
            )
            yield response

    return fetch_all_pages
