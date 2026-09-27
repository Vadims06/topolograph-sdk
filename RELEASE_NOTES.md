# Release Notes - topolograph-sdk v0.2.0

Requires Topolograph >= 2.73.

## New

- **BGP VPN and EVPN on the IGP graph.** Every question is asked on the OSPF/IS-IS
  graph; the BGP epoch bound to it answers, with no `bgp_graph_time`.
  - `graph.vpns`: VNIs and VRFs of the fabric; `graph.vpns.filter(router_id=...)` for one router.
  - `graph.routes`: where a MAC or IP is, what a VRF or VNI holds. Filters: `mac`, `prefix`,
    `vni`, `vrf`, `rt`, `rd`, `vtep`, `at`, `router_id`.
  - `graph.events.routes`: route history; a MAC's arrival on a new VTEP carries `moved_from_vtep`.
  - `graph.nodes.filter(protocol="bgp", vni=...)` (or `vrf=`, `rt=`): the leaves that carry it.
  - `graph.paths.shortest_to_many(src, [dst1, dst2])`: paths to several targets from one SPF.
- **Managers in pynetbox style.** `graph.nodes`, `graph.vpns` and `graph.routes` have
  `all()`, `filter(**filters)` and `count(**filters)`; pages are fetched while iterating.
  `graph.nodes.get(name=...)` returns one node or `None`.
- `graph.protocols`: the graph's IGP, plus `bgp` when a BGP epoch is bound to it.
- `graph.events.networks()`, `.adjacency()`, `.timeline()`.

## Deprecated (still work, emit `DeprecationWarning`)

| Old | New |
|---|---|
| `graph.protocol` | `graph.protocols` |
| `graph.nodes_list()` | `graph.nodes.filter()` |
| `graph.nodes.get()` with filters or paging | `graph.nodes.filter()` / `.count()` |
| `graph.events.get_network_events()` | `graph.events.networks()` |
| `graph.events.get_adjacency_events()` | `graph.events.adjacency()` |
| `graph.events.get_events_timeline()` | `graph.events.timeline()` |

## Removed

- `graph.vpn_routers()`: use `graph.nodes.filter(protocol="bgp")`.
- `lpm` in BGP route search: pass an address as `prefix=`; covering routes come back
  longest prefix first. Passing `lpm` raises `ValueError`.

---

# Release Notes - topolograph-sdk v0.1.5

## ✨ New

- **`graph.events.get_events_timeline(...)`**: adjacency events grouped into
  chronological time *waves* (server-side), with a per-wave summary
  (`pattern` outage/flap/up, `converged`, `trigger_device`, and more).
  `start_ts`/`end_ts` are ISO 8601, reusable as `get_adjacency_events`
  `start_time`/`end_time` to fetch a wave's individual events.
  Requires Topolograph >= 2.65.
- **`graph.status()`** now also returns `top_unstable_devices` in `details`
  (top-N `{device, event_count}` sorted desc).

---

# Release Notes - topolograph-sdk v0.1.1

## 🎉 Initial Release

This is the first public release of the Topolograph Python SDK, providing a Pythonic interface to the Topolograph REST API with built-in SSH-based topology ingestion.

## ✨ Features

### Core SDK
- **Pythonic API Client**: Clean, object-oriented interface to the Topolograph REST API
- **Graph Management**: Retrieve, list, and query network topology graphs
- **Node & Network Queries**: Find nodes and networks by various criteria (IP, network, node ID)
- **Path Computation**: Calculate shortest paths between nodes or networks with backup path support
- **Event Monitoring**: Retrieve network and adjacency events with time-based filtering

### Topology Collection
- **SSH-Based Collection**: Collect IGP LSDB data directly from network devices using Nornir
- **Multi-Vendor Support**: Cisco, Juniper, FRR, Arista, Nokia, Huawei
- **Multi-Protocol Support**: OSPF and IS-IS
- **Command Registry**: Centralized command mapping per vendor and protocol
- **Raw LSDB Upload**: Upload collected LSDB data to Topolograph

### CLI Interface
- **Command-Line Tool**: `topo` command for all SDK operations
- **Graph Management**: List and query graphs via CLI
- **Topology Ingestion**: Collect and upload topology data from inventory files
- **Path Computation**: Compute shortest paths from command line

## 📦 Installation

```bash
pip install topolograph-sdk
```

## 🚀 Quick Start

```python
from topolograph import Topolograph

# Initialize client
topo = Topolograph(
    url="http://localhost:8080",
    token="your-api-token"  # or set TOPOLOGRAPH_TOKEN env var
)

# Get latest graph
graph = topo.graphs.get(latest=True)

# Collect topology from devices
from topolograph import TopologyCollector
collector = TopologyCollector("inventory.yaml")
result = collector.collect()

# Upload to Topolograph
graph = topo.uploader.upload_raw(
    lsdb_text=result.raw_lsdb_text,
    vendor="FRR",
    protocol="isis"
)
```

## 📋 Supported Vendors & Protocols

### OSPF
- Cisco, Juniper, FRR, Arista, Nokia

### IS-IS
- Cisco, Juniper, FRR, Nokia, Huawei

## 🔧 Requirements

- Python 3.8+
- Network devices accessible via SSH
- Topolograph API endpoint

## 📚 Documentation

Full documentation available in the [README](README.md) and on [GitHub](https://github.com/Vadims06/topolograph-sdk).

## 🔗 Links

- **PyPI**: https://pypi.org/project/topolograph-sdk/
- **GitHub**: https://github.com/Vadims06/topolograph-sdk
- **Issues**: https://github.com/Vadims06/topolograph-sdk/issues

## 📝 Changes in v0.1.1

- Fixed GitHub repository URLs in package metadata
- Updated package links to point to correct repository

## 🙏 Acknowledgments

Built with:
- [Nornir](https://github.com/nornir-automation/nornir) for network automation
- [Typer](https://typer.tiangolo.com/) for CLI interface
- [Rich](https://rich.readthedocs.io/) for beautiful terminal output
