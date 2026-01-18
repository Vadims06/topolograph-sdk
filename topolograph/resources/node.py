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
    
    def get(self, name: Optional[str] = None, **query_params) -> List[Node]:
        """Get nodes from the graph.
        
        Args:
            name: Optional node name to filter by
            **query_params: Additional query parameters (e.g., location='dc1', ha_role='primary')
        
        Returns:
            List of Node objects
        """
        params = {}
        if name:
            params['name'] = name
        # Add query params directly - API accepts them as individual query parameters
        # For deepObject style, we need to format them properly
        if query_params:
            # Format as node_query_params[location]=dc1&node_query_params[ha_role]=primary
            for key, value in query_params.items():
                params[f'node_query_params[{key}]'] = value
        
        response = self._client.get(
            f'/diagram/{self.graph_time}/nodes',
            params=params
        )
        nodes_data = response.json()
        
        if not nodes_data:
            return []
        
        # Handle different response formats
        if isinstance(nodes_data, list):
            return [Node(node, manager=self) for node in nodes_data]
        elif isinstance(nodes_data, dict):
            # If it's a dict, convert to list of nodes
            nodes = []
            for node_id, node_data in nodes_data.items():
                if isinstance(node_data, dict):
                    node_data['id'] = node_id
                    nodes.append(Node(node_data, manager=self))
                else:
                    nodes.append(Node({'id': node_id, 'name': node_data}, manager=self))
            return nodes
        
        return [Node(nodes_data, manager=self)]
    
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
