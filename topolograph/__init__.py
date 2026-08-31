"""Topolograph Python SDK - A Pythonic client for the Topolograph REST API."""

from .client import Topolograph
from .resources.graph import GraphsManager, Graph
from .resources.bgp import (
    BgpGraphsManager,
    BgpGraph,
    BgpNodesManager,
    BgpSessionsManager,
    BgpRoutesManager,
    BgpEventsManager,
    BgpBindingsManager,
)
from .resources.node import NodesManager, Node
from .resources.network import NetworksManager, Network
from .resources.path import PathsManager, Path
from .resources.event import EventsManager, Event
from .collector.collector import TopologyCollector
from .upload.uploader import Uploader

__version__ = "0.1.12"

__all__ = [
    "Topolograph",
    "GraphsManager",
    "Graph",
    "BgpGraphsManager",
    "BgpGraph",
    "BgpNodesManager",
    "BgpSessionsManager",
    "BgpRoutesManager",
    "BgpEventsManager",
    "BgpBindingsManager",
    "NodesManager",
    "Node",
    "NetworksManager",
    "Network",
    "PathsManager",
    "Path",
    "EventsManager",
    "Event",
    "TopologyCollector",
    "Uploader",
]
