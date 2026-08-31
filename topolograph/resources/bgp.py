"""BGP topology resources for Topolograph API.

Mirrors the `Graph` object model: a `BgpGraph` exposes lazy submanagers for
nodes, sessions, routes, events and IGP bindings. Every method returns the
API's own JSON unchanged -- BGP route rows are wide and the backend's
vocabulary (folded paths, `diff_status`, RIB tags) is the contract.
"""

from typing import Any, Dict, List, Optional


# Route search filters accepted by both the graph- and node-scoped endpoints.
# Passed straight through as query parameters; unknown keys are rejected so a
# typo fails loudly instead of being silently dropped by the API. `lpm` is a
# named kwarg on search() instead -- the API only honours "true"/"1"/"yes".
_ROUTE_FILTERS = frozenset({
    "prefix", "vrf", "rd", "rt", "afi", "safi", "bmp_rib", "evidence",
    "as_path_contains", "origin", "local_pref", "med", "community",
    "large_community", "extended_community", "label", "originator_id",
    "peer_ip", "nexthop", "bmp_source", "table_filters", "ribs",
})


class BgpNodesManager:
    """BGP speakers in one epoch, with their resolved RIB view."""

    def __init__(self, client, bgp_graph_time: str):
        self._client = client
        self.bgp_graph_time = bgp_graph_time

    def list(
        self,
        role: Optional[str] = None,
        asn: Optional[str] = None,
        page: int = 1,
        per_page: int = 50,
    ) -> Dict[str, Any]:
        """Paginated node list.

        Each row carries `rib_view`, `can_build_path`, `assumptions` and
        `observed_by` (which speakers' feeds prove this node's table).
        """
        params: Dict[str, Any] = {"page": page, "per_page": per_page}
        if role:
            params["role"] = role
        if asn is not None:
            params["asn"] = asn
        return self._client.get(
            f"/bgp-graph/{self.bgp_graph_time}/nodes", params=params).json()


class BgpSessionsManager:
    """BGP sessions in one epoch, classified eBGP/iBGP and by IGP relation."""

    def __init__(self, client, bgp_graph_time: str):
        self._client = client
        self.bgp_graph_time = bgp_graph_time

    def list(
        self,
        igp_relation: Optional[str] = None,
        bgp_session_type: Optional[str] = None,
        page: int = 1,
        per_page: int = 50,
    ) -> Dict[str, Any]:
        """Paginated session list.

        Args:
            igp_relation: filter by IGP domain relation of the two endpoints.
            bgp_session_type: 'ibgp' or 'ebgp'.
        """
        params: Dict[str, Any] = {"page": page, "per_page": per_page}
        if igp_relation:
            params["igp_relation"] = igp_relation
        if bgp_session_type:
            params["bgp_session_type"] = bgp_session_type
        return self._client.get(
            f"/bgp-graph/{self.bgp_graph_time}/sessions", params=params).json()


class BgpRoutesManager:
    """Route search, node route summary, point-in-time state and route diff."""

    def __init__(self, client, bgp_graph_time: str):
        self._client = client
        self.bgp_graph_time = bgp_graph_time

    def search(
        self,
        router_id: Optional[str] = None,
        lpm: bool = False,
        sort: Optional[str] = None,
        order: Optional[str] = None,
        page: int = 1,
        per_page: int = 50,
        **filters: Any,
    ) -> Dict[str, Any]:
        """Route table, one row per distinct RFC 4271 9.1 path.

        Args:
            router_id: scope to one router's resolved RIB view (hits the
                node-scoped endpoint); omit for the whole graph table.
            lpm: with a CIDR `prefix` filter, return only the single longest
                covering match instead of the table (cannot be paged).
            sort: route column to order by (only indexed columns accepted);
                `sortable_columns` in the response lists them.
            order: 'asc' or 'desc'.
            **filters: any of prefix, vrf, rd, rt, afi, safi, bmp_rib,
                evidence, as_path_contains, origin, local_pref, med, community,
                large_community, extended_community, label, originator_id,
                peer_ip, nexthop, bmp_source, table_filters, ribs.
        """
        unknown = set(filters) - _ROUTE_FILTERS
        if unknown:
            raise ValueError(f"unknown route filter(s): {', '.join(sorted(unknown))}")
        params: Dict[str, Any] = {"page": page, "per_page": per_page}
        params.update({key: value for key, value in filters.items() if value is not None})
        if lpm:
            params["lpm"] = "true"
        if sort:
            params["sort"] = sort
        if order:
            params["order"] = order
        if router_id:
            path = f"/bgp-graph/{self.bgp_graph_time}/node/{router_id}/routes"
        else:
            path = f"/bgp-graph/{self.bgp_graph_time}/routes"
        return self._client.get(path, params=params).json()

    def summary(self, router_id: str) -> Dict[str, Any]:
        """Route counts for one node: total in its resolved RIB view, a
        per-RIB-tag histogram (`by_ribs`) and the Adj-RIB-Out count."""
        return self._client.get(
            f"/bgp-graph/{self.bgp_graph_time}/node/{router_id}/routes/summary").json()

    def state(self, at: Optional[str] = None) -> Dict[str, Any]:
        """Route table as it stood at a point in time (ISO 8601 `at`;
        omit for the latest)."""
        params = {"at": at} if at else {}
        return self._client.get(
            f"/bgp-graph/{self.bgp_graph_time}/routes/state", params=params).json()

    def compare(
        self,
        t0: str,
        t1: str,
        router_id: Optional[str] = None,
        t0_graph_time: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Route diff between two timestamps in one epoch.

        One row per added/withdrawn route; a changed route is two rows. The
        `diff_status` column carries added|withdrawn|before|after.

        Args:
            router_id: scope the diff to one reporting speaker.
            t0_graph_time: epoch of `t0` when it differs from this epoch
                (collector restart).
        """
        params: Dict[str, Any] = {"t0": t0, "t1": t1}
        if router_id:
            params["router_id"] = router_id
        if t0_graph_time:
            params["t0_graph_time"] = t0_graph_time
        return self._client.get(
            f"/bgp-graph/{self.bgp_graph_time}/routes/compare", params=params).json()


class BgpEventsManager:
    """BGP monitoring events, clustered into one-minute buckets."""

    def __init__(self, client, bgp_graph_time: str):
        self._client = client
        self.bgp_graph_time = bgp_graph_time

    def timeline(
        self,
        start_time: Optional[str] = None,
        end_time: Optional[str] = None,
        last_minutes: Optional[int] = None,
        event_name: Optional[str] = None,
        event_status: Optional[str] = None,
    ) -> Dict[str, Any]:
        """BGP change events over a window.

        Args:
            start_time, end_time: ISO 8601 bounds.
            last_minutes: look-back window; overrides start_time.
            event_name, event_status: filter the returned events.
        """
        params: Dict[str, Any] = {}
        if last_minutes is not None:
            params["last_minutes"] = last_minutes
        else:
            if start_time:
                params["start_time"] = start_time
            if end_time:
                params["end_time"] = end_time
        if event_name:
            params["event_name"] = event_name
        if event_status:
            params["event_status"] = event_status
        return self._client.get(
            f"/bgp-graph/{self.bgp_graph_time}/events", params=params).json()


class BgpBindingsManager:
    """The BGP epoch's correlations to IGP graphs."""

    def __init__(self, client, bgp_graph_time: str):
        self._client = client
        self.bgp_graph_time = bgp_graph_time

    def list(self) -> Dict[str, Any]:
        return self._client.get(
            f"/bgp-graph/{self.bgp_graph_time}/bindings").json()

    def get(self, graph_time: str) -> Dict[str, Any]:
        return self._client.get(
            f"/bgp-graph/{self.bgp_graph_time}/{graph_time}/binding").json()

    def confirm(self, graph_time: str) -> Dict[str, Any]:
        """Mark a BGP-to-IGP binding as authoritative for monitoring."""
        return self._client.put(
            f"/bgp-graph/{self.bgp_graph_time}/{graph_time}/binding").json()

    def remove(self, graph_time: str) -> None:
        """Drop a BGP-to-IGP binding (API returns 204, no body)."""
        self._client.delete(
            f"/bgp-graph/{self.bgp_graph_time}/{graph_time}/binding")


class BgpGraph:
    """One BGP topology epoch."""

    def __init__(self, client, data: Dict[str, Any]):
        self._client = client
        self.bgp_graph_time = data.get("graph_time")
        self.timestamp = data.get("timestamp")
        self.nodes_data = data.get("nodes", [])
        self.sessions_data = data.get("sessions", [])
        self.bindings = data.get("bindings", [])

        self._nodes_manager = None
        self._sessions_manager = None
        self._routes_manager = None
        self._events_manager = None
        self._bindings_manager = None

    @property
    def nodes(self) -> BgpNodesManager:
        if self._nodes_manager is None:
            self._nodes_manager = BgpNodesManager(self._client, self.bgp_graph_time)
        return self._nodes_manager

    @property
    def sessions(self) -> BgpSessionsManager:
        if self._sessions_manager is None:
            self._sessions_manager = BgpSessionsManager(self._client, self.bgp_graph_time)
        return self._sessions_manager

    @property
    def routes(self) -> BgpRoutesManager:
        if self._routes_manager is None:
            self._routes_manager = BgpRoutesManager(self._client, self.bgp_graph_time)
        return self._routes_manager

    @property
    def events(self) -> BgpEventsManager:
        if self._events_manager is None:
            self._events_manager = BgpEventsManager(self._client, self.bgp_graph_time)
        return self._events_manager

    @property
    def igp_bindings(self) -> BgpBindingsManager:
        if self._bindings_manager is None:
            self._bindings_manager = BgpBindingsManager(self._client, self.bgp_graph_time)
        return self._bindings_manager

    def __repr__(self) -> str:
        return f"BgpGraph(bgp_graph_time={self.bgp_graph_time})"


class BgpGraphsManager:
    """Manager for BGP graph epochs, registered as `client.bgp_graphs`."""

    def __init__(self, client):
        self._client = client

    def list(self, page: int = 1, per_page: int = 50) -> List[BgpGraph]:
        response = self._client.get(
            "/bgp-graphs", params={"page": page, "per_page": per_page})
        body = response.json()
        items = body.get("items", []) if isinstance(body, dict) else (body or [])
        return [BgpGraph(self._client, item) for item in items]

    def get(self, bgp_graph_time: str) -> BgpGraph:
        response = self._client.get(f"/bgp-graph/{bgp_graph_time}")
        return BgpGraph(self._client, response.json())

    def get_latest(self) -> Optional[BgpGraph]:
        """The newest epoch (`/bgp-graphs` is already ordered newest first)."""
        graphs = self.list(page=1, per_page=1)
        return graphs[0] if graphs else None
