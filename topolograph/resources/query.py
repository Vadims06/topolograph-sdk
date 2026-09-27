"""pynetbox-style reads over one paginated list endpoint."""

from typing import Any, Callable, Dict, FrozenSet, Iterator, Optional


class QueryManager:
    """Every collection answers all/filter/count the same way, so no caller pages by hand."""

    per_page = 50

    def __init__(
        self,
        client,
        path: Callable[[Dict[str, Any]], str],
        allowed_filters: Optional[FrozenSet[str]] = None,
    ):
        """
        Args:
            client: Topolograph client instance.
            path: builds the endpoint from the filters, popping the ones that
                are path segments (such as router_id).
            allowed_filters: accepted filter names; None accepts any, for
                endpoints that filter on free-form attributes.
        """
        self._client = client
        self._path = path
        self._allowed_filters = allowed_filters

    def _encode(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        return filters

    def _page(self, filters: Dict[str, Any], page: int, per_page: int) -> Dict[str, Any]:
        params = {name: value for name, value in filters.items() if value is not None}
        if self._allowed_filters is not None:
            unknown = set(params) - self._allowed_filters
            if unknown:
                # the API ignores unknown parameters, so a typo would return everything
                raise ValueError(f"unknown filter(s): {', '.join(sorted(unknown))}")
        path = self._path(params)
        params = self._encode(params)
        params.update(page=page, per_page=per_page)
        return self._client.get(path, params=params).json()

    def filter(self, **filters) -> Iterator[Dict[str, Any]]:
        """Matching records; later pages are fetched while iterating."""
        page = 1
        while True:
            body = self._page(filters, page, self.per_page)
            yield from body.get('items', [])
            if page >= body.get('pagination', {}).get('total_pages', 0):
                return
            page += 1

    def all(self) -> Iterator[Dict[str, Any]]:
        return self.filter()

    def count(self, **filters) -> int:
        return self._page(filters, 1, 1).get('pagination', {}).get('total', 0)
