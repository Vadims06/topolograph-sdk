"""Path resource for Topolograph API."""

from typing import Optional, List, Tuple


class Path:
    """Represents a shortest path result."""
    
    def __init__(self, data: dict):
        """Initialize a Path object.
        
        Args:
            data: Path data from API
        """
        self.paths = data.get('spt_path_nodes_name_as_ll_in_ll', [])
        self.cost = data.get('cost')
        self.unbackup_paths = data.get('unbackup_paths_nodes_name_as_ll_in_ll', [])
    
    def __repr__(self) -> str:
        return f"Path(cost={self.cost}, paths={len(self.paths)})"


class PathsManager:
    """Manager for path computation."""
    
    def __init__(self, client, graph_time: str):
        """Initialize the PathsManager.
        
        Args:
            client: Topolograph client instance
            graph_time: Graph time identifier
        """
        self._client = client
        self.graph_time = graph_time
    
    def shortest(
        self,
        src_node: str,
        dst_node: str,
        removed_edges: Optional[List[Tuple[str, str]]] = None
    ) -> Path:
        """Compute shortest path between two nodes.
        
        Args:
            src_node: Source node identifier
            dst_node: Destination node identifier
            removed_edges: Optional list of (src, dst) tuples representing
                          edges to remove for backup path calculation
        
        Returns:
            Path object
        """
        payload = {
            'graph_time': self.graph_time,
            'src_node': src_node,
            'dst_node': dst_node
        }
        
        if removed_edges:
            payload['removedEdgesAsNodePairsFromSptPath_ll_in_ll'] = [
                [src, dst] for src, dst in removed_edges
            ]
        
        response = self._client.post('/path/', json=payload)
        return Path(response.json())
    
    def shortest_network(
        self,
        src_ip_or_network: str,
        dst_ip_or_network: str,
        removed_edges: Optional[List[Tuple[str, str]]] = None
    ) -> Path:
        """Compute shortest path between two IP addresses or networks.
        
        Args:
            src_ip_or_network: Source IP address or network
            dst_ip_or_network: Destination IP address or network
            removed_edges: Optional list of (src, dst) tuples representing
                          edges to remove for backup path calculation
        
        Returns:
            Path object
        """
        payload = {
            'graph_time': self.graph_time,
            'src_ip_or_network': src_ip_or_network,
            'dst_ip_or_network': dst_ip_or_network
        }
        
        if removed_edges:
            payload['removedEdgesAsNodePairsFromSptPath_ll_in_ll'] = [
                [src, dst] for src, dst in removed_edges
            ]
        
        response = self._client.post('/path/network/', json=payload)
        return Path(response.json())
