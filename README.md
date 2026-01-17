# Topolograph Python SDK

A Pythonic, object-oriented client for the Topolograph REST API with built-in topology ingestion via SSH.

## Features

- **Pythonic API Client**: Clean, object-oriented interface to the Topolograph REST API
- **SSH-Based Collection**: Collect IGP LSDB data directly from network devices using Nornir
- **CLI Interface**: Command-line tool built on top of the SDK
- **PyPI Ready**: Installable via `pip install topolograph-sdk`

## Installation

```bash
pip install topolograph-sdk
```

## Quick Start

### Basic Usage

```python
from topolograph import Topolograph

# Initialize client
topo = Topolograph(
    url="http://localhost:8080",
    token="your-api-token"  # or set TOPOLOGRAPH_TOKEN env var
)

# Get latest graph
graph = topo.graphs.get(latest=True)

# Access graph properties
print(f"Graph Time: {graph.graph_time}")
print(f"Protocol: {graph.protocol}")
print(f"Hosts: {graph.hosts['count']}")

# Get graph status
status = graph.status()
print(f"Status: {status['status']}")
```

### Collecting Topology Data

```python
from topolograph import TopologyCollector

# Create collector with inventory file
collector = TopologyCollector("inventory.yaml")

# Collect LSDB data
result = collector.collect()

# Access results
print(f"Collected from {len(result.host_results)} hosts")
print(f"LSDB text length: {len(result.raw_lsdb_text)}")

# Upload to Topolograph
graph = topo.uploader.upload_raw(
    lsdb_text=result.raw_lsdb_text,
    vendor="FRR",
    protocol="isis"
)
```

### Inventory Format

Create a YAML inventory file with explicit vendor and protocol metadata. A sample inventory file (`inventory.yaml.example`) is provided in the project root:

```yaml
---
router1:
  hostname: 172.20.20.2
  username: admin
  password: admin
  vendor: frr
  protocol: isis
  port: 22

router2:
  hostname: 172.20.20.3
  username: admin
  password: admin
  vendor: cisco
  protocol: ospf
  port: 22
```

**Required fields:**
- `hostname`: IP address or hostname of the device
- `username`: SSH username
- `password`: SSH password
- `vendor`: Device vendor (`cisco`, `juniper`, `frr`, `arista`, `nokia`, `huawei`)
- `protocol`: IGP protocol (`ospf`, `isis`)
- `port`: SSH port (optional, defaults to 22)

**Quick start:** Copy the example inventory file:
```bash
cp inventory.yaml.example inventory.yaml
# Edit inventory.yaml with your device credentials
```

### Working with Graphs

```python
# List all graphs
graphs = topo.graphs.list(protocol="ospf")

# Get specific graph
graph = topo.graphs.get_by_time("2024-01-15T10:30:00Z")

# Get nodes
nodes = graph.nodes.get()
for node in nodes:
    print(f"Node: {node.name} (ID: {node.id})")

# Find networks
networks = graph.networks.find_by_ip("10.10.10.1")
networks = graph.networks.find_by_node("1.1.1.1")
network = graph.networks.find_by_network("10.10.10.0/24")
```

### Path Computation

```python
# Shortest path between nodes
path = graph.paths.shortest("1.1.1.1", "2.2.2.2")
print(f"Path cost: {path.cost}")
for path_nodes in path.paths:
    print(f"Path: {' -> '.join(path_nodes)}")

# Shortest path between networks/IPs
path = graph.paths.shortest_network("192.168.1.1", "192.168.2.1")

# Backup path (removing specific edges)
path = graph.paths.shortest(
    "1.1.1.1",
    "2.2.2.2",
    removed_edges=[("1.1.1.1", "3.3.3.3")]
)
```

### Events

```python
# Get network events
network_events = graph.events.get_network_events(last_minutes=60)
for event in network_events['network_up_down_events']:
    print(f"Network {event.event_object} is {event.event_status}")

# Get adjacency events
adjacency_events = graph.events.get_adjacency_events(
    start_time="2024-01-15T10:00:00Z",
    end_time="2024-01-15T11:00:00Z"
)
```

## CLI Usage

The SDK includes a CLI tool accessible via the `topo` command:

### List Graphs

```bash
# List all graphs
topo graphs --list

# Get latest graph
topo graphs --latest

# Filter by protocol
topo graphs --list --protocol ospf

# Filter by watcher
topo graphs --list --watcher production-watcher
```

### Collect and Upload Topology

```bash
# Collect LSDB from devices
topo ingest inventory.yaml --protocol isis

# Collect and save to file
topo ingest inventory.yaml --output lsdb.txt

# Collect and upload to Topolograph
topo ingest inventory.yaml --upload --url http://localhost:8080
```

### Compute Paths

```bash
# Shortest path between nodes
topo path --src 1.1.1.1 --dst 2.2.2.2

# Shortest path between networks
topo path --src 192.168.1.1 --dst 192.168.2.1 --network

# Use specific graph
topo path --src 1.1.1.1 --dst 2.2.2.2 --graph-time "2024-01-15T10:30:00Z"
```

### Upload LSDB Files

```bash
# Upload a LSDB file
topo upload --file lsdb.txt --vendor FRR --protocol isis

# Upload with watcher name
topo upload --file lsdb.txt --vendor Cisco --protocol ospf --watcher prod-watcher
```

## Supported Vendors and Protocols

### OSPF
- **Cisco**: `show ip ospf database router`, `show ip ospf database network`, `show ip ospf database external`
- **Juniper**: `show ospf database router extensive | no-more`, etc.
- **FRR/Quagga**: `show ip ospf database router`, etc.
- **Arista**: `show ip ospf database router detail`, etc.
- **Nokia**: `show router ospf database router detail`, etc.

### IS-IS
- **Cisco**: `show isis database detail`
- **Juniper**: `show isis database extensive`
- **FRR**: `show isis database detail`
- **Nokia**: `show router isis database detail`
- **Huawei**: `display isis lsdb verbose`

## Authentication

The SDK supports multiple authentication methods (in priority order):

1. **Explicit token parameter**:
   ```python
   topo = Topolograph(url="...", token="your-token")
   ```

2. **Environment variable**:
   ```bash
   export TOPOLOGRAPH_TOKEN="your-token"
   ```

3. **Basic authentication**:
   ```python
   topo = Topolograph(url="...", username="user", password="pass")
   ```

## Error Handling

The SDK raises custom exceptions for different error scenarios:

```python
from topolograph.exceptions import (
    AuthenticationError,
    NotFoundError,
    ValidationError,
    APIError
)

try:
    graph = topo.graphs.get_by_time("invalid-time")
except NotFoundError:
    print("Graph not found")
except AuthenticationError:
    print("Authentication failed")
except APIError as e:
    print(f"API error: {e}")
```

## Testing

Run integration tests with containerlab:

```bash
# Set environment variables
export TOPOLOGRAPH_URL="http://localhost:8080"
export TOPOLOGRAPH_TOKEN="your-token"

# Run tests
pytest tests/test_integration.py -v
```

Or use the manual test script:

```bash
python test_sdk.py
```

## Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/topolograph/topolograph-sdk.git
cd topolograph-sdk

# Install in development mode
pip install -e ".[dev]"
```

### Project Structure

```
topolograph-sdk/
├── topolograph/          # SDK package
│   ├── client.py        # Core HTTP client
│   ├── resources/       # Resource objects (Graph, Node, Network, etc.)
│   ├── collector/       # SSH-based topology collection
│   └── upload/          # Upload pipeline
├── cli/                 # CLI interface
├── tests/               # Test suite
└── pyproject.toml       # Package configuration
```

## License

Apache License 2.0 - See LICENSE file for details.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request.

## Support

For issues, questions, or feature requests, please open an issue on GitHub.
