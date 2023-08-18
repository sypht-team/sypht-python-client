from typing import Any, Callable, Iterator, List


def fetch_all_pages(
    name: str, fetch_page: Callable[..., List[Any]], page_limit=1000
) -> Callable[..., Iterator[List[Any]]]:
    """Returns an iterator that calls fetch_page with an offset that we increment by the number of records returned from the last call to fetch_page.  Stop if page returns empty list."""

    def fetch_all_pages(*args, **kwargs) -> Iterator[List[Any]]:
        offset = 0
        page_count = 0
        while True:
            page_count += 1
            if page_count > page_limit:
                # Don't want to DOS ourselves...
                raise Exception(
                    f"fetch_all_pages({name}): fetched more than {page_limit} pages - you sure this thing is gonna stop?  Consider using a date range to reduce the number of pages fetched."
                )
            try:
                result = fetch_page(
                    *args,
                    **kwargs,
                    offset=offset,
                )
            except Exception as err:
                raise Exception(
                    f"Failed fetching for {name} for page={page_count} offset={offset}"
                ) from err
            if not result:
                break
            offset += len(result)
            yield result
        return None

    return fetch_all_pages
