from typing import Any, Callable, Iterator, List


def fetch_all_pages(
    name: str, fetch_page: Callable[..., List[Any]], rec_limit=20000
) -> Callable[..., Iterator[List[Any]]]:
    """Returns an iterator that calls fetch_page with an offset that we increment by the number of pages fetched.  Stop if page returns empty list."""

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
                result = fetch_page(
                    *args,
                    **kwargs,
                    offset=page_count - 1,
                )
            except Exception as err:
                raise Exception(
                    f"Failed fetching for {name} for offset={page_count - 1}"
                ) from err
            if not result:
                break
            recs += len(result)
            yield result

    return fetch_all_pages
