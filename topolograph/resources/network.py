"""Network resource for Topolograph API."""

from typing import Optional, List, Dict, Any


class Network:
    """Represents a network in a Topolograph graph."""
    
    def __init__(self, network: str, data: List[Dict[str, Any]]):
        """Initialize a Network object.
        
        Args:
            network: Network address with mask (e.g., "10.10.10.0/24")
            data: List of network attributes from API
        """
        self.network = network
        self.attributes = data  # List of dicts with rid, cost, metric_type, etc.
    
    def __repr__(self) -> str:
        return f"Network(network={self.network}, routers={len(self.attributes)})"


class NetworksManager:
    """Manager for network resources."""
    
    def __init__(self, client, graph_time: str):
        """Initialize the NetworksManager.
        
        Args:
            client: Topolograph client instance
            graph_time: Graph time identifier
        """
        self._client = client
        self.graph_time = graph_time
    
    def find_by_ip(self, ip_address: str) -> List[Network]:
        """Find networks by IP address.
        
        Args:
            ip_address: IP address to search for
        
        Returns:
            List of Network objects
        """
        response = self._client.get(
            f'/network/{self.graph_time}',
            params={'ip_address': ip_address}
        )
        networks_data = response.json()
        
        if not networks_data:
            return []
        
        return [
            Network(network, attrs)
            for network, attrs in networks_data.items()
        ]
    
    def find_by_network(self, network_with_mask: str) -> Optional[Network]:
        """Find a specific network by network/mask notation.
        
        Args:
            network_with_mask: Network with mask (e.g., "10.10.10.0/24")
        
        Returns:
            Network object or None if not found
        """
        response = self._client.get(
            f'/network/{self.graph_time}',
            params={'network_w_digit_mask': network_with_mask}
        )
        networks_data = response.json()
        
        if not networks_data or network_with_mask not in networks_data:
            return None
        
        return Network(network_with_mask, networks_data[network_with_mask])
    
    def find_by_node(self, node_id: str) -> List[Network]:
        """Find all networks terminated by a specific node.
        
        Args:
            node_id: Node identifier (OSPF RID or IS-IS System ID)
        
        Returns:
            List of Network objects
        """
        response = self._client.get(
            f'/network/{self.graph_time}',
            params={'node_id': node_id}
        )
        networks_data = response.json()
        
        if not networks_data:
            return []
        
        return [
            Network(network, attrs)
            for network, attrs in networks_data.items()
        ]
    
    def get_all(self) -> List[Network]:
        """Get all networks in the graph.
        
        Returns:
            List of Network objects
        """
        response = self._client.get(f'/network/{self.graph_time}')
        networks_data = response.json()
        
        if not networks_data:
            return []
        
        return [
            Network(network, attrs)
            for network, attrs in networks_data.items()
        ]
