"""Node resource for Topolograph API."""

from typing import Optional, List, Dict, Any


class Node:
    """Represents a network node in a Topolograph graph."""
    
    def __init__(self, data: Dict[str, Any]):
        """Initialize a Node object.
        
        Args:
            data: Node data from API
        """
        self.id = data.get('id')
        self.name = data.get('name')
        self.attributes = {k: v for k, v in data.items() if k not in ('id', 'name')}
    
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
            return [Node(node) for node in nodes_data]
        elif isinstance(nodes_data, dict):
            # If it's a dict, convert to list of nodes
            nodes = []
            for node_id, node_data in nodes_data.items():
                if isinstance(node_data, dict):
                    node_data['id'] = node_id
                    nodes.append(Node(node_data))
                else:
                    nodes.append(Node({'id': node_id, 'name': node_data}))
            return nodes
        
        return [Node(nodes_data)]
    
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
            return Node(node_data)
        except Exception:
            return None
