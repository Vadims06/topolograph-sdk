"""Path-mapping tests for the BGP resource, Graph.vrfs and resolve_route.

No live API: a fake client records every call so the tests prove which URL,
verb and params each SDK method produces.
"""

import pytest

from topolograph.resources.bgp import BgpGraph, BgpGraphsManager
from topolograph.resources.graph import Graph
from topolograph.resources.path import PathsManager


class _Response:
    def __init__(self, body):
        self.body = body

    def json(self):
        return self.body


class _Client:
    def __init__(self, body=None):
        self.calls = []
        self._body = body if body is not None else {"ok": True}

    def _call(self, method, path, **kwargs):
        self.calls.append((method, path, kwargs))
        return _Response(self._body)

    def get(self, path, **kwargs):
        return self._call("get", path, **kwargs)

    def post(self, path, **kwargs):
        return self._call("post", path, **kwargs)

    def put(self, path, **kwargs):
        return self._call("put", path, **kwargs)

    def delete(self, path, **kwargs):
        return self._call("delete", path, **kwargs)


def _bgp_graph(client):
    return BgpGraph(client, {"graph_time": "bgp-epoch"})


def test_manager_lists_and_gets_bgp_graphs():
    client = _Client({"items": [{"graph_time": "bgp-epoch"}]})
    manager = BgpGraphsManager(client)

    graphs = manager.list(page=2, per_page=10)
    manager.get("bgp-epoch")

    assert [g.bgp_graph_time for g in graphs] == ["bgp-epoch"]
    assert client.calls == [
        ("get", "/bgp-graphs", {"params": {"page": 2, "per_page": 10}}),
        ("get", "/bgp-graph/bgp-epoch", {}),
    ]


def test_get_latest_asks_for_a_single_newest_row():
    client = _Client({"items": [{"graph_time": "bgp-epoch"}]})

    latest = BgpGraphsManager(client).get_latest()

    assert latest.bgp_graph_time == "bgp-epoch"
    assert client.calls == [
        ("get", "/bgp-graphs", {"params": {"page": 1, "per_page": 1}}),
    ]


def test_nodes_and_sessions_pass_their_filters():
    client = _Client()
    graph = _bgp_graph(client)

    graph.nodes.list(role="rr", asn="65000", page=1, per_page=50)
    graph.sessions.list(igp_relation="same-domain", bgp_session_type="ibgp")

    assert client.calls == [
        ("get", "/bgp-graph/bgp-epoch/nodes",
         {"params": {"page": 1, "per_page": 50, "role": "rr", "asn": "65000"}}),
        ("get", "/bgp-graph/bgp-epoch/sessions",
         {"params": {"page": 1, "per_page": 50,
                     "igp_relation": "same-domain", "bgp_session_type": "ibgp"}}),
    ]


def test_route_search_is_graph_scoped_without_a_router_id():
    client = _Client()

    _bgp_graph(client).routes.search(prefix="10.0.0.0/24", ribs="loc-rib", sort="prefix", order="desc")

    assert client.calls == [
        ("get", "/bgp-graph/bgp-epoch/routes",
         {"params": {"page": 1, "per_page": 50, "prefix": "10.0.0.0/24",
                     "ribs": "loc-rib", "sort": "prefix", "order": "desc"}}),
    ]


def test_route_search_with_a_router_id_hits_the_node_scoped_endpoint():
    client = _Client()

    _bgp_graph(client).routes.search(router_id="1.1.1.1", vrf="BLUE")

    assert client.calls == [
        ("get", "/bgp-graph/bgp-epoch/node/1.1.1.1/routes",
         {"params": {"page": 1, "per_page": 50, "vrf": "BLUE"}}),
    ]


def test_route_search_rejects_an_unknown_filter():
    with pytest.raises(ValueError, match="nexthopp"):
        _bgp_graph(_Client()).routes.search(nexthopp="192.0.2.1")


def test_route_search_lpm_is_sent_as_the_string_the_api_accepts():
    client = _Client()

    _bgp_graph(client).routes.search(prefix="10.1.2.3", lpm=True)

    assert client.calls == [
        ("get", "/bgp-graph/bgp-epoch/routes",
         {"params": {"page": 1, "per_page": 50, "prefix": "10.1.2.3", "lpm": "true"}}),
    ]


def test_route_summary_state_and_compare_paths():
    client = _Client()
    routes = _bgp_graph(client).routes

    routes.summary("1.1.1.1")
    routes.state(at="2026-08-30T10:00:00Z")
    routes.compare("2026-08-30T09:00:00Z", "2026-08-30T10:00:00Z", router_id="1.1.1.1")

    assert client.calls == [
        ("get", "/bgp-graph/bgp-epoch/node/1.1.1.1/routes/summary", {}),
        ("get", "/bgp-graph/bgp-epoch/routes/state",
         {"params": {"at": "2026-08-30T10:00:00Z"}}),
        ("get", "/bgp-graph/bgp-epoch/routes/compare",
         {"params": {"t0": "2026-08-30T09:00:00Z", "t1": "2026-08-30T10:00:00Z",
                     "router_id": "1.1.1.1"}}),
    ]


def test_events_timeline_uses_the_events_endpoint():
    client = _Client()

    _bgp_graph(client).events.timeline(last_minutes=15, event_name="peer_down")

    assert client.calls == [
        ("get", "/bgp-graph/bgp-epoch/events",
         {"params": {"last_minutes": 15, "event_name": "peer_down"}}),
    ]


def test_events_timeline_with_an_explicit_window_omits_last_minutes():
    client = _Client()

    _bgp_graph(client).events.timeline(
        start_time="2026-08-30T09:00:00Z", end_time="2026-08-30T10:00:00Z")

    assert client.calls == [
        ("get", "/bgp-graph/bgp-epoch/events",
         {"params": {"start_time": "2026-08-30T09:00:00Z",
                     "end_time": "2026-08-30T10:00:00Z"}}),
    ]


def test_binding_read_confirm_and_remove_use_the_right_verbs():
    client = _Client()
    bindings = _bgp_graph(client).igp_bindings

    bindings.list()
    bindings.get("igp-time")
    bindings.confirm("igp-time")
    bindings.remove("igp-time")

    assert client.calls == [
        ("get", "/bgp-graph/bgp-epoch/bindings", {}),
        ("get", "/bgp-graph/bgp-epoch/igp-time/binding", {}),
        ("put", "/bgp-graph/bgp-epoch/igp-time/binding", {}),
        ("delete", "/bgp-graph/bgp-epoch/igp-time/binding", {}),
    ]


def test_graph_vrfs_passes_router_and_rd_filters():
    client = _Client()

    Graph(client, {"graph_time": "igp-time"}).vrfs(router_id="1.1.1.1", rd="65000:1")

    assert client.calls == [
        ("get", "/graph/igp-time/vrfs",
         {"params": {"router_id": "1.1.1.1", "rd": "65000:1"}}),
    ]


def test_graph_vpn_routers_hits_its_endpoint():
    client = _Client()

    Graph(client, {"graph_time": "igp-time"}).vpn_routers()

    assert client.calls == [("get", "/graph/igp-time/vpn-routers", {})]


def test_resolve_route_posts_the_body_and_omits_unset_fields():
    client = _Client()

    PathsManager(client, "igp-time").resolve_route(
        "R1", "8.8.8.8", vrf="BLUE", evidence="fib", changed_edge_costs={"3": 50})

    assert client.calls == [
        ("post", "/graph/igp-time/route-resolution/R1",
         {"json": {"destination": "8.8.8.8", "with_lsps": True, "vrf": "BLUE",
                   "evidence": "fib", "changed_edge_costs": {"3": 50}}}),
    ]
