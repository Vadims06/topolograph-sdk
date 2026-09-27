"""Path-mapping tests for the BGP resource and the graph-scoped BGP/EVPN calls
(Graph.vrfs, the vpns/routes/events.routes/nodes managers, resolve_route,
shortest_to_many).

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
        """body: one response for every call, or a list answered in order."""
        self.calls = []
        self._body = body if body is not None else {"ok": True}

    def _call(self, method, path, **kwargs):
        self.calls.append((method, path, kwargs))
        if isinstance(self._body, list):
            return _Response(self._body[len(self.calls) - 1])
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


def test_route_search_points_a_removed_lpm_call_at_prefix():
    with pytest.raises(ValueError, match="prefix="):
        _bgp_graph(_Client()).routes.search(prefix="10.1.2.3", lpm=True)


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


def _graph(client):
    return Graph(client, {"graph_time": "igp-time", "protocols": ["ospf", "bgp"]})


@pytest.mark.parametrize("manager, filters, path, params", [
    (lambda graph: graph.vpns, {}, "/graph/igp-time/vpns", {}),
    (lambda graph: graph.vpns, {"router_id": "1.1.1.1"}, "/graph/igp-time/node/1.1.1.1/vpns", {}),
    (lambda graph: graph.routes, {"vni": 1010, "mac": "aa:bb:cc:00:00:01"},
     "/graph/igp-time/routes", {"vni": 1010, "mac": "aa:bb:cc:00:00:01"}),
    (lambda graph: graph.routes, {"router_id": "leaf1", "vrf": "tenant1", "prefix": "10.10.20.0/24"},
     "/graph/igp-time/node/leaf1/routes", {"vrf": "tenant1", "prefix": "10.10.20.0/24"}),
    (lambda graph: graph.events.routes, {"mac": "aa:bb:cc:00:00:01", "last_minutes": 60},
     "/events/igp-time/routes", {"mac": "aa:bb:cc:00:00:01", "last_minutes": 60}),
    (lambda graph: graph.nodes, {"protocol": "bgp", "vni": 1010, "watcher": True, "abr": True},
     "/graph/igp-time/nodes", {"protocol": "bgp", "vni": 1010, "watcher": "true", "abr": 1}),
])
def test_filter_maps_to_its_endpoint(manager, filters, path, params):
    client = _Client({"items": [], "pagination": {"total_pages": 0}})

    list(manager(_graph(client)).filter(**filters))

    assert client.calls == [("get", path, {"params": {**params, "page": 1, "per_page": 50}})]


def test_filter_fetches_every_page_while_iterating():
    client = _Client([
        {"items": [{"prefix": "a"}], "pagination": {"total_pages": 2}},
        {"items": [{"prefix": "b"}], "pagination": {"total_pages": 2}},
    ])

    rows = list(_graph(client).routes.filter(vni=1010))

    assert rows == [{"prefix": "a"}, {"prefix": "b"}]
    assert [call[2]["params"]["page"] for call in client.calls] == [1, 2]


def test_count_reads_the_total_of_a_one_row_page():
    client = _Client({"items": [{}], "pagination": {"total": 7, "total_pages": 7}})

    assert _graph(client).routes.count(vni=1010) == 7
    assert client.calls == [
        ("get", "/graph/igp-time/routes", {"params": {"vni": 1010, "page": 1, "per_page": 1}}),
    ]


def test_filter_rejects_an_unknown_filter_before_calling():
    client = _Client()

    with pytest.raises(ValueError, match="nexthopp"):
        list(_graph(client).routes.filter(nexthopp="192.0.2.1"))
    assert client.calls == []


@pytest.mark.parametrize("items, expected", [
    ([{"node_id": "10.0.0.1"}], {"node_id": "10.0.0.1"}),
    ([], None),
])
def test_nodes_get_by_name_returns_one_node_or_none(items, expected):
    client = _Client({"items": items, "pagination": {"total_pages": 1}})

    assert _graph(client).nodes.get(name="10.0.0.1") == expected
    assert client.calls[0][2]["params"]["name"] == "10.0.0.1"


def test_nodes_get_by_name_refuses_several_matches():
    client = _Client({"items": [{"node_id": "a"}, {"node_id": "b"}], "pagination": {"total_pages": 1}})

    with pytest.raises(ValueError, match="more than one"):
        _graph(client).nodes.get(name="dup")


def test_nodes_get_with_filters_is_the_deprecated_page_call():
    page = {"items": [{"node_id": "a"}], "pagination": {"total_pages": 1}}
    client = _Client(page)

    with pytest.deprecated_call():
        assert _graph(client).nodes.get(protocol="ospf", per_page=10) == page
    assert client.calls == [
        ("get", "/graph/igp-time/nodes", {"params": {"protocol": "ospf", "page": 1, "per_page": 10}}),
    ]


@pytest.mark.parametrize("data", [
    {"protocols": ["ospf", "bgp"]},
    {"protocol": "ospf"},
])
def test_graph_protocol_is_a_deprecated_alias_of_the_first_protocol(data):
    with pytest.deprecated_call():
        assert Graph(_Client(), {"graph_time": "igp-time", **data}).protocol == "ospf"


def test_paths_shortest_to_many_joins_targets_with_commas():
    client = _Client()

    PathsManager(client, "igp-time").shortest_to_many("leaf1", ["leaf2", "leaf3"])

    assert client.calls == [("get", "/graph/igp-time/path/leaf1/leaf2,leaf3", {})]


def test_nodes_list_is_a_deprecated_alias_of_nodes_filter():
    client = _Client()

    with pytest.deprecated_call():
        _graph(client).nodes_list(protocol="bgp", abr=True)

    assert client.calls == [
        ("get", "/graph/igp-time/nodes",
         {"params": {"protocol": "bgp", "abr": 1, "page": 1, "per_page": 50}}),
    ]


@pytest.mark.parametrize("deprecated_method, path_suffix, params", [
    ("get_network_events", "networks", {"last_minutes": 30}),
    ("get_adjacency_events", "adjacency", {"last_minutes": 30}),
    ("get_events_timeline", "adjacency/timeline", {"page": 1, "per_page": 20, "last_minutes": 30}),
])
def test_event_methods_have_deprecated_aliases(deprecated_method, path_suffix, params):
    client = _Client()
    events = _graph(client).events

    with pytest.deprecated_call():
        getattr(events, deprecated_method)(last_minutes=30)

    assert client.calls == [("get", f"/events/igp-time/{path_suffix}", {"params": params})]


def test_resolve_route_posts_the_body_and_omits_unset_fields():
    client = _Client()

    PathsManager(client, "igp-time").resolve_route(
        "R1", "8.8.8.8", vrf="BLUE", evidence="fib", changed_edge_costs={"3": 50})

    assert client.calls == [
        ("post", "/graph/igp-time/route-resolution/R1",
         {"json": {"destination": "8.8.8.8", "with_lsps": True, "vrf": "BLUE",
                   "evidence": "fib", "changed_edge_costs": {"3": 50}}}),
    ]
