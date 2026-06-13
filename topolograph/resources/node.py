"""Node resource for Topolograph API."""

from typing import Optional, List, Dict, Any


class Node:
    """Represents a network node in a Topolograph graph."""
    
    def __init__(self, data: Dict[str, Any], manager: Optional['NodesManager'] = None):
        """Initialize a Node object.
        
        Args:
            data: Node data from API
            manager: Optional NodesManager reference for update methods
        """
        self.id = data.get('id')
        self.name = data.get('name')
        self.attributes = {k: v for k, v in data.items() if k not in ('id', 'name')}
        self._manager = manager
    
    def update(self, **attributes) -> 'Node':
        """Update this node's attributes (PUT - replaces all).
        
        Args:
            **attributes: Attributes to set. Must include 'name' if updating name.
                        Example: name='new_name', location='dc1', role='router'
        
        Returns:
            Updated Node object
            
        Raises:
            ValueError: If node instance not associated with a manager
        """
        if not self._manager:
            raise ValueError("Node instance not associated with a manager")
        return self._manager.update(self.id, attributes)
    
    def patch(self, **attributes) -> 'Node':
        """Partially update this node's attributes (PATCH).
        
        Args:
            **attributes: Attributes to update (only specified attributes are changed).
                         Example: name='new_name' or location='dc2', role='switch'
        
        Returns:
            Updated Node object
            
        Raises:
            ValueError: If node instance not associated with a manager
        """
        if not self._manager:
            raise ValueError("Node instance not associated with a manager")
        return self._manager.patch(self.id, attributes)
    
    def __repr__(self) -> str:
        return f"Node(id={self.id}, name={self.name})"


class NodesManager:
    """Manager for node resources."""
    
    def __init__(self, client, graph_time: str):
        """Initialize the NodesManager.
        
        Args:
            client: Topolograph client instance
            graph_time: Graph time identifier
        """
        self._client = client
        self.graph_time = graph_time
    
    def get(
        self,
        name: Optional[str] = None,
        protocol: Optional[str] = None,
        watcher: Optional[bool] = None,
        area: Optional[str] = None,
        page: int = 1,
        per_page: int = 50,
        **query_params
    ) -> Dict[str, Any]:
        """Get paginated nodes from the graph.

        Args:
            name: Optional node name to filter by (exact match on igraph vertex name)
            protocol: Graph-level filter (ospf, ospfv3, isis, yaml)
            watcher: Graph-level filter — True for watcher-uploaded, False for manually parsed
            area: Graph-level filter by area (e.g. "0", "0.0.0.1", "49.0001")
            page: Page number (default: 1)
            per_page: Items per page (default: 50)
            **query_params: Additional flat vertex attribute filters, e.g. location='dc1',
                or node role flags abr=1 / asbr=1 (OSPF), overload=1 / attached=1 (IS-IS)

        Returns:
            Dictionary with:
            - items: List of node dictionaries with node_id, hostname, systemid (IS-IS),
                     pseudo_rid (IS-IS), networks_count, areas, is_isis, and node_attributes
                     (role flags: abr/asbr for OSPF, overload/attached for IS-IS)
            - pagination: Dictionary with page, per_page, total, total_pages
        """
        params: Dict[str, Any] = {'page': page, 'per_page': per_page}
        if name:
            params['name'] = name
        if protocol:
            params['protocol'] = protocol
        if watcher is not None:
            params['watcher'] = str(watcher).lower()
        if area:
            params['area'] = area
        params.update(query_params)

        response = self._client.get(f'/graph/{self.graph_time}/nodes', params=params)
        return response.json()
    
    def get_by_id(self, node_id: int) -> Optional[Node]:
        """Get a specific node by ID.
        
        Args:
            node_id: Node ID
        
        Returns:
            Node object or None if not found
        """
        try:
            response = self._client.get(f'/diagram/{self.graph_time}/nodes/{node_id}')
            node_data = response.json()
            if isinstance(node_data, dict):
                node_data['id'] = node_id
            return Node(node_data, manager=self)
        except Exception:
            return None
    
    def update(self, node_id: int, attributes: Dict[str, Any]) -> Node:
        """Completely replace all attributes of a node (PUT).
        
        Args:
            node_id: Node ID to update
            attributes: Dictionary of attributes to set. Must include 'name' if updating name.
                       Example: {'name': 'new_name', 'location': 'dc1', 'role': 'router'}
        
        Returns:
            Updated Node object
            
        Raises:
            NotFoundError: If node not found
            ValidationError: If request is invalid
        """
        response = self._client.put(
            f'/diagram/{self.graph_time}/nodes/{node_id}',
            json=attributes
        )
        # API returns success message, fetch updated node
        return self.get_by_id(node_id)
    
    def patch(self, node_id: int, attributes: Dict[str, Any]) -> Node:
        """Partially update attributes of a node (PATCH).
        
        Args:
            node_id: Node ID to update
            attributes: Dictionary of attributes to update (only specified attributes are changed).
                       Example: {'name': 'new_name'} or {'location': 'dc2', 'role': 'switch'}
        
        Returns:
            Updated Node object
            
        Raises:
            NotFoundError: If node not found
            ValidationError: If request is invalid
        """
        response = self._client.patch(
            f'/diagram/{self.graph_time}/nodes/{node_id}',
            json=attributes
        )
        # API returns success message, fetch updated node
        return self.get_by_id(node_id)
