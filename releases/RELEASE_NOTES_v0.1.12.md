# topolograph-sdk v0.1.12

Tag: `v0.1.12`
Requires: Topolograph >= 2.69

Full read access to the BGP topology feature: a new `client.bgp_graphs`
manager mirroring `client.graphs`, plus `Graph.vrfs` / `Graph.vpn_routers` /
`Graph.paths.resolve_route`.

Every output below was captured by running the SDK against Topolograph's
built-in demo BGP topology (the "demo topology" button seeds it), not written
by hand. Arrays are truncated where noted; nothing else is edited. The same
method / how-to-use / output layout is reusable on docs.topolograph.com.

```python
from topolograph import Topolograph

client = Topolograph(url="http://localhost:5000",
                     username="you@example.com", password="...")
bgp = client.bgp_graphs.get_latest()
```

---

## `client.bgp_graphs.list(page=1, per_page=50)`

List BGP topology epochs, newest first. Each carries the IGP graphs it is
bound to.

```python
client.bgp_graphs.list(per_page=3)
```

```json
[
  {
    "bgp_graph_time": "29Aug2026_18h14m29s_13_hosts_cae0c6",
    "timestamp": "2026-08-29T18:14:31.233000Z",
    "bindings": [
      {
        "bgp_graph_time": "29Aug2026_18h14m29s_13_hosts_cae0c6",
        "igp_graph_time": "30Aug2026_13h48m56s_13_hosts_demo",
        "matched_rids": ["123.10.10.10", "123.11.11.11", "123.123.100.100", "… 10 more"],
        "source_coverage": 1.0,
        "state": "bound"
      }
    ]
  }
]
```

## `client.bgp_graphs.get(bgp_graph_time)` / `.get_latest()`

Return one `BgpGraph`. `get_latest()` takes the newest epoch.

```python
bgp = client.bgp_graphs.get_latest()
{"bgp_graph_time": bgp.bgp_graph_time, "timestamp": bgp.timestamp,
 "nodes": len(bgp.nodes_data), "sessions": len(bgp.sessions_data)}
```

```json
{
  "bgp_graph_time": "29Aug2026_18h14m29s_13_hosts_cae0c6",
  "timestamp": "2026-08-29T18:14:31.233000Z",
  "nodes": 13,
  "sessions": 22
}
```

## `bgp.nodes.list(role=None, asn=None, page=1, per_page=50)`

BGP speakers, each with the RIB view its table is resolved at
(`rib_view`), whether a path can be built from it (`can_build_path`), the
modelling `assumptions`, and which speakers' feeds prove its table
(`observed_by`).

```python
bgp.nodes.list(per_page=3)
```

```json
{
  "items": [
    {
      "name": "123.123.100.100", "label": "RR1 (7854)", "asn": "65000",
      "device_role": "route-reflector", "role": "speaker",
      "rib_view": "loc_rib_reflected", "can_build_path": true,
      "assumptions": ["reflection_assumed", "import_not_observed"],
      "observed_by": []
    },
    {
      "name": "123.123.101.101", "label": "RR2 (7854+9069+8671)", "asn": "65000",
      "device_role": "route-reflector", "role": "speaker",
      "rib_view": "loc_rib", "can_build_path": true,
      "assumptions": [], "observed_by": []
    },
    {
      "name": "123.123.30.30", "asn": "65000", "device_role": "pe", "role": "peer",
      "rib_view": "adj_rib_in", "can_build_path": true,
      "assumptions": ["import_not_observed"], "observed_by": ["123.123.101.101"]
    }
  ],
  "pagination": {"page": 1, "per_page": 3, "total": 13, "total_pages": 5}
}
```

## `bgp.sessions.list(igp_relation=None, bgp_session_type=None, page=1, per_page=50)`

BGP sessions, classified `ibgp`/`ebgp` and by IGP-domain relation.

```python
bgp.sessions.list(per_page=3)
```

```json
{
  "items": [
    {
      "source": "123.123.100.100", "target": "123.123.30.30",
      "source_router_id": "123.123.100.100", "target_router_id": "123.123.30.30",
      "asn": "65000", "bgp_session_type": "ibgp", "igp_relation": "intra-domain",
      "local_ip": "123.123.100.100", "peer_ip": "123.123.30.30",
      "families": ["1/1", "1/128", "2/1", "2/128"],
      "policies": ["pre", "post"]
    }
  ],
  "pagination": {"page": 1, "per_page": 3, "total": 22, "total_pages": 8}
}
```

## `bgp.routes.search(router_id=None, lpm=False, sort=None, order=None, page=1, per_page=50, **filters)`

The route table, one row per distinct RFC 4271 §9.1 path. `bmp_source` and
`bmp_ribs` are arrays (a folded row can come from several speakers / RIB
tags). Filters: `prefix, vrf, rd, rt, afi, safi, bmp_rib, evidence,
as_path_contains, origin, local_pref, med, community, large_community,
extended_community, label, originator_id, peer_ip, nexthop, bmp_source,
table_filters, ribs`. `sortable_columns` in the response lists what `sort`
accepts.

```python
bgp.routes.search(per_page=2)
```

```json
{
  "items": [
    {
      "prefix": "100.30.0.0/24", "afi": 1, "safi": 1,
      "nexthop": "123.123.30.30", "as_path": ["65300", "64530"], "origin": "igp",
      "local_pref": 100, "med": 50, "communities": [],
      "bmp_ribs": ["pre"], "bmp_source": ["123.123.100.100"],
      "originator_id": "123.123.30.30", "peer_ip": "123.123.30.30",
      "path_id": 10, "rd": null, "vrf": null
    },
    {
      "prefix": "100.30.0.0/24", "afi": 1, "safi": 1,
      "nexthop": "123.123.30.30", "as_path": ["65300", "64530"], "origin": "igp",
      "local_pref": 200, "med": 20, "communities": ["65000:100", "65000:110"],
      "bmp_ribs": ["post"], "bmp_source": ["123.123.100.100"],
      "originator_id": "123.123.30.30", "peer_ip": "123.123.30.30",
      "path_id": 10, "rd": null, "vrf": null
    }
  ],
  "pagination": {"page": 1, "per_page": 2, "total": 67, "total_pages": 34},
  "sortable_columns": ["afi", "local_pref", "med", "nexthop", "peer_ip",
                       "prefix", "prefix_len", "safi"]
}
```

### Scoped to one router's resolved RIB view

Pass `router_id` — the query hits the node-scoped endpoint and returns only
what that router's table (at its resolved `rib_view`) holds.

```python
bgp.routes.search(router_id="123.123.100.100", per_page=1)
```

```json
{
  "items": [
    {
      "prefix": "100.14.0.0/24", "afi": 1, "safi": 1, "nexthop": "123.14.14.14",
      "as_path": ["65140"], "local_pref": 180, "med": 0,
      "large_communities": ["65000:14:1"],
      "bmp_ribs": ["loc-rib", "post"], "bmp_source": ["123.123.101.101"],
      "originator_id": "123.14.14.14", "path_id": 12
    }
  ],
  "pagination": {"page": 1, "per_page": 1, "total": 16, "total_pages": 16}
}
```

### Longest-prefix match

```python
bgp.routes.search(prefix="100.30.0.0/24", lpm=True)
```

```json
{
  "items": [
    {
      "prefix": "100.30.0.0/24", "nexthop": "123.123.30.30",
      "as_path": ["65300", "64530"], "local_pref": 100, "med": 50,
      "bmp_ribs": ["pre"], "bmp_source": ["123.123.100.100"]
    }
  ],
  "pagination": {"page": 1, "per_page": 50, "total": 1, "total_pages": 1}
}
```

## `bgp.routes.summary(router_id)`

Route counts for one router: total in its resolved RIB view, a per-RIB-tag
histogram, and how many prefixes it advertised (`adj_rib_out`).

```python
bgp.routes.summary("123.123.100.100")
```

```json
{
  "rib_view": "loc_rib_reflected",
  "total": 16,
  "by_ribs": [
    {"ribs": ["loc-rib"], "count": 10},
    {"ribs": ["loc-rib", "post"], "count": 6}
  ],
  "adj_rib_out": 0
}
```

## `bgp.routes.state(at=None)`

The route table as it stood at a point in time (`at`, ISO 8601; omit for
latest).

```python
bgp.routes.state()
```

```json
{
  "at": null,
  "items": [
    {
      "prefix": "100.30.0.0/24", "nexthop": "123.123.30.30",
      "as_path": ["65300", "64530"], "local_pref": 100, "med": 50,
      "bmp_ribs": ["pre"], "bmp_source": ["123.123.100.100"]
    }
  ]
}
```
_73 routes in the demo epoch; one shown._

## `bgp.routes.compare(t0, t1, router_id=None, t0_graph_time=None)`

One row per added/withdrawn route between two timestamps; a changed route is
two rows. The `diff_status` column carries `added|withdrawn|before|after`.

```python
bgp.routes.compare("2026-08-29T00:00:00Z", "2026-08-29T18:14:31Z")
```

```json
{ "items": [] }
```
_The demo has a single snapshot, so nothing changed between the two times._

## `bgp.events.timeline(start_time=None, end_time=None, last_minutes=None, event_name=None, event_status=None)`

BGP change events over a window.

```python
bgp.events.timeline(last_minutes=1440)
```

```json
{ "events": 0, "items": [] }
```
_No change events in the demo snapshot._

## `bgp.igp_bindings.list()` / `.get(graph_time)`

The BGP epoch's correlations to IGP graphs. `matched_rids` are the Router IDs
present in both; `source_coverage` is the fraction of BGP speakers covered.

```python
bgp.igp_bindings.get("30Aug2026_13h48m56s_13_hosts_demo")
```

```json
{
  "bgp_graph_time": "29Aug2026_18h14m29s_13_hosts_cae0c6",
  "igp_graph_time": "30Aug2026_13h48m56s_13_hosts_demo",
  "matched_rids": ["123.10.10.10", "123.11.11.11", "123.123.100.100", "… 10 more"],
  "source_coverage": 1.0,
  "state": "bound"
}
```

`.confirm(graph_time)` (PUT) and `.remove(graph_time)` (DELETE) mutate the
binding; both need basic or bearer auth.

## `graph.vrfs(router_id=None, rd=None)`

VRF inventory for an IGP graph's routers, as of the graph timestamp.

```python
igp = client.graphs.get(latest=True)
igp.vrfs()
```

```json
{
  "items": [
    {
      "name": "Blue", "router_id": "123.123.30.30", "rd": "1:123.123.30.30:200",
      "observed_at": "2026-08-18T07:51:03.919000Z",
      "address_families": [
        {"afi": "ipv4", "safi": "unicast",
         "import_rts": ["65000:200"], "export_rts": ["65000:200"]},
        {"afi": "ipv6", "safi": "unicast",
         "import_rts": ["65000:200"], "export_rts": ["65000:200"]}
      ]
    }
  ]
}
```
_4 VRFs in the demo; one shown._

## `graph.vpn_routers()`

Routers the bound BGP epochs know, each with the vantage its table is
observed at. Use a `router_id` here as `start_node` for `resolve_route` on a
VPN destination.

```python
igp.vpn_routers()
```

```json
{
  "items": [
    {"router_id": "123.123.100.100", "vpn_count": 2, "evidence": "loc_rib",
     "can_build_path": true, "assumptions": []},
    {"router_id": "123.123.30.30", "vpn_count": 1, "evidence": "adj_rib_in",
     "can_build_path": true, "assumptions": ["import_not_observed"]},
    {"router_id": "123.11.11.11", "vpn_count": 2, "evidence": "loc_rib_reflected",
     "can_build_path": true,
     "assumptions": ["reflection_assumed", "import_not_observed"]}
  ]
}
```
_13 routers in the demo; three shown._

## `graph.paths.resolve_route(start_node, destination, rt=None, vrf=None, rd=None, evidence=None, with_lsps=True, changed_edge_costs=None)`

Protocol-aware path resolution: walk `start_node` toward `destination` (a
router ID or a prefix), handing off between static / BGP / IGP / LSP wherever
one overrides the plain SPF path. `evidence` names what the answer rests on
when the start router's RIB is not observed directly.

```python
igp.paths.resolve_route("123.10.10.10", "100.30.0.0/24")
```

```json
{
  "cost_and_spt_path_node_names_ll_in_ll": [
    [11, ["123.10.10.10", "123.30.30.30", "123.123.30.30"]]
  ],
  "evidence": {
    "level": "adj_rib_in",
    "observed_from": ["123.123.100.100", "123.123.101.101"],
    "assumptions": ["import_not_observed"]
  }
}
```
_The per-hop node/edge render payload (`node_dd_in_ll`, `new_edge_title_dd_ll`)
is returned too and omitted here._

---

## Also in this release

- `AuthenticationError` now subclasses `APIError`, so a 401 raises it
  cleanly (it previously raised `TypeError` from the `status_code` kwarg).
- BGP ingestion endpoints stay collector-only, unwrapped — same as
  OSPF/IS-IS.
