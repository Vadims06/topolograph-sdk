"""Graph resource for Topolograph API."""

from typing import Optional, List, Dict, Any
from .node import NodesManager
from .network import NetworksManager
from .path import PathsManager
from .event import EventsManager


class Graph:
    """Represents a single Topolograph graph."""
    
    def __init__(self, client, data: Dict[str, Any]):
        """Initialize a Graph object.
        
        Args:
            client: Topolograph client instance
            data: Graph data from API
        """
        self._client = client
        self.graph_time = data.get('graph_time')
        self.timestamp = data.get('timestamp')
        self.protocol = data.get('protocol')
        self.watcher_name = data.get('watcher_name')
        self.is_from_watcher = data.get('is_from_watcher', False)
        self.hosts = data.get('hosts', {})
        self.networks_data = data.get('networks', {})
        self.areas = data.get('areas', [])
        
        # Initialize resource managers
        self._nodes_manager = None
        self._networks_manager = None
        self._paths_manager = None
        self._events_manager = None
    
    @property
    def nodes(self) -> NodesManager:
        """Get nodes manager for this graph."""
        if self._nodes_manager is None:
            self._nodes_manager = NodesManager(self._client, self.graph_time)
        return self._nodes_manager
    
    @property
    def networks(self) -> NetworksManager:
        """Get networks manager for this graph."""
        if self._networks_manager is None:
            self._networks_manager = NetworksManager(self._client, self.graph_time)
        return self._networks_manager
    
    @property
    def paths(self) -> PathsManager:
        """Get paths manager for this graph."""
        if self._paths_manager is None:
            self._paths_manager = PathsManager(self._client, self.graph_time)
        return self._paths_manager
    
    @property
    def events(self) -> EventsManager:
        """Get events manager for this graph."""
        if self._events_manager is None:
            self._events_manager = EventsManager(self._client, self.graph_time)
        return self._events_manager
    
    def status(self) -> Dict[str, Any]:
        """Get the status of this graph.
        
        Returns:
            Dictionary with status information including:
            - status: ok, warning, critical, or no_monitoring_data
            - details: is_monitored, is_connected, event counts, etc.
        """
        response = self._client.get(f'/graph/{self.graph_time}/status')
        return response.json()
    
    def delete(self) -> None:
        """Delete this graph."""
        self._client.delete(f'/graph/{self.graph_time}')
    
    def __repr__(self) -> str:
        return f"Graph(graph_time={self.graph_time}, protocol={self.protocol})"


class GraphsManager:
    """Manager for graph resources."""
    
    def __init__(self, client):
        """Initialize the GraphsManager.
        
        Args:
            client: Topolograph client instance
        """
        self._client = client
    
    def get(
        self,
        latest: bool = True,
        protocol: Optional[str] = None,
        area: Optional[str] = None,
        watcher_name: Optional[str] = None
    ) -> Optional[Graph]:
        """Retrieve a graph.
        
        Args:
            latest: If True, return only the latest graph (default: True)
            protocol: Filter by protocol (ospf, ospfv3, isis, yaml)
            area: Filter by area number
            watcher_name: Filter by watcher name
        
        Returns:
            Graph object or None if not found
        """
        params = {}
        if latest:
            params['latest_only'] = True
        if protocol:
            params['protocol'] = protocol
        if area:
            params['area'] = area
        if watcher_name:
            params['watcher_name'] = watcher_name
        
        response = self._client.get('/graph/', params=params)
        graphs_data = response.json()
        
        if not graphs_data:
            return None
        
        # If latest_only=True, API returns a list but we want the first (latest) one
        if isinstance(graphs_data, list):
            if len(graphs_data) == 0:
                return None
            return Graph(self._client, graphs_data[0])
        
        # If it's a single graph object
        return Graph(self._client, graphs_data)
    
    def list(
        self,
        protocol: Optional[str] = None,
        area: Optional[str] = None,
        watcher_name: Optional[str] = None,
        latest_only: bool = False
    ) -> List[Graph]:
        """List graphs with optional filters.
        
        Args:
            protocol: Filter by protocol (ospf, ospfv3, isis, yaml)
            area: Filter by area number
            watcher_name: Filter by watcher name
            latest_only: Return only the latest graph for each watcher
        
        Returns:
            List of Graph objects
        """
        params = {}
        if protocol:
            params['protocol'] = protocol
        if area:
            params['area'] = area
        if watcher_name:
            params['watcher_name'] = watcher_name
        if latest_only:
            params['latest_only'] = True
        
        response = self._client.get('/graph/', params=params)
        graphs_data = response.json()
        
        if not graphs_data:
            return []
        
        if isinstance(graphs_data, list):
            return [Graph(self._client, g) for g in graphs_data]
        
        # Single graph
        return [Graph(self._client, graphs_data)]
    
    def get_by_time(self, graph_time: str) -> Graph:
        """Get a specific graph by graph_time.
        
        Args:
            graph_time: Graph time identifier
        
        Returns:
            Graph object
        
        Raises:
            NotFoundError: If graph not found
        """
        response = self._client.get(f'/graph/{graph_time}')
        return Graph(self._client, response.json())
    
    def delete(self, graph_time: str) -> None:
        """Delete a graph by graph_time.
        
        Args:
            graph_time: Graph time identifier
        """
        self._client.delete(f'/graph/{graph_time}')
    
    def upload(
        self,
        lsdb_data: str,
        vendor: str,
        protocol: str,
        watcher_name: Optional[str] = None
    ) -> Graph:
        """Upload a raw LSDB and create a new graph.
        
        Args:
            lsdb_data: Raw LSDB text output
            vendor: Vendor name (e.g., 'Cisco', 'Juniper', 'FRR')
            protocol: Protocol name (ospf, ospfv3, isis)
            watcher_name: Optional watcher name
        
        Returns:
            Graph object with diff information
        """
        payload = {
            'lsdb_output': lsdb_data,
            'vendor_device': vendor,
            'igp_protocol': protocol
        }
        if watcher_name:
            payload['watcher_name'] = watcher_name
        
        response = self._client.post('/graph/', json=payload)
        return Graph(self._client, response.json())
    
    def upload_multi(self, lsdb_array: List[Dict[str, Any]]) -> Graph:
        """Upload multiple LSDB files and create a new graph.
        
        Args:
            lsdb_array: List of LSDB dictionaries, each with:
                - lsdb_output: Raw LSDB text
                - vendor_device: Vendor name
                - igp_protocol: Protocol name (ospf, ospfv3, isis)
                - watcher_name: Optional watcher name
        
        Returns:
            Graph object with diff information
        """
        response = self._client.post('/graphs', json=lsdb_array)
        return Graph(self._client, response.json())
