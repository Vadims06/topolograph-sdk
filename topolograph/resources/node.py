"""Node resource for Topolograph API."""

import warnings
from itertools import islice
from typing import Any, Dict, Optional

from ..exceptions import NotFoundError
from .query import QueryManager


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


class NodesManager(QueryManager):
    """Nodes of the graph: all(), filter(**kw), count(**kw), get(name=).

    Filters: protocol (graph-level: ospf, ospfv3, isis, yaml; bgp returns BGP
    routers narrowed by vni=, vrf= or rt=), watcher, area, and vertex
    attributes such as name='10.0.0.1', location='dc1', abr=True (OSPF),
    overload=True (IS-IS). Rows: node_id, display_name, hostname, systemid,
    networks_count, areas, node_attributes; BGP routers carry can_build_path.
    """

    def __init__(self, client, graph_time: str):
        """Initialize the NodesManager.

        Args:
            client: Topolograph client instance
            graph_time: Graph time identifier
        """
        super().__init__(client, lambda filters: f'/graph/{graph_time}/nodes')
        self.graph_time = graph_time

    def _encode(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        # watcher is a swagger boolean; role flags are vertex attributes stored as 0/1
        return {
            name: (str(value).lower() if name == 'watcher' else int(value))
            if isinstance(value, bool) else value
            for name, value in filters.items()
        }

    def get(self, name: Optional[str] = None, page: Optional[int] = None,
            per_page: Optional[int] = None, **filters) -> Any:
        """One node by name, or None.

        Called with anything but `name`, it returns the old page dictionary
        for one more version; use filter() for that.
        """
        if name is not None and page is None and per_page is None and not filters:
            nodes = list(islice(self.filter(name=name), 2))
            if len(nodes) > 1:
                raise ValueError(f"more than one node is named {name}; use filter()")
            return nodes[0] if nodes else None
        warnings.warn(
            "NodesManager.get() with filters or paging is deprecated, use .filter() or .count() instead",
            DeprecationWarning,
            stacklevel=2,
        )
        return self._page({'name': name, **filters}, page or 1, per_page or 50)

    def get_by_id(self, node_id: str) -> Optional[Node]:
        """Get a specific node by ID.

        Args:
            node_id: Canonical node name, IS-IS System ID, discovered hostname,
                or operator display override, matched case-insensitively.

        Returns:
            Node object or None if not found
        """
        try:
            response = self._client.get(f'/diagram/{self.graph_time}/nodes/{node_id}')
        except NotFoundError:
            return None
        node_data = response.json()
        if isinstance(node_data, dict) and 'id' not in node_data:
            # older servers (pre-canonical-id) don't echo an id -- fall back
            # to what was requested rather than leaving it unset.
            node_data['id'] = node_id
        return Node(node_data, manager=self)
    
    def update(self, node_id: str, attributes: Dict[str, Any]) -> Node:
        """Completely replace all attributes of a node (PUT).

        Args:
            node_id: Canonical node name, IS-IS System ID, hostname, or display
                override, matched case-insensitively.
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
        # API returns a success message, not the updated node -- refetch by the
        # new canonical name when this call renamed it, else the old id/alias
        # still resolves.
        return self.get_by_id(attributes.get('name', node_id))
    
    def patch(self, node_id: str, attributes: Dict[str, Any]) -> Node:
        """Partially update attributes of a node (PATCH).

        Args:
            node_id: Canonical node name, IS-IS System ID, hostname, or display
                override, matched case-insensitively.
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
        # API returns a success message, not the updated node -- refetch by the
        # new canonical name when this call renamed it, else the old id/alias
        # still resolves.
        return self.get_by_id(attributes.get('name', node_id))
