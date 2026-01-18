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
