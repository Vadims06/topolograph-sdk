"""Graph resource for Topolograph API."""

from typing import Optional, List, Dict, Any, Union
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
        self.is_monitored = data.get('is_monitored', self.is_from_watcher)
        self.is_live = data.get('is_live', False)
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
            - details: is_monitored, is_connected, event counts, and
              top_unstable_devices (top-N {device, event_count} sorted desc)
        """
        response = self._client.get(f'/graph/{self.graph_time}/status')
        return response.json()
    
    def networks_list(
        self,
        page: int = 1,
        per_page: int = 20,
        filter_type: str = 'all'
    ) -> Dict[str, Any]:
        """Get paginated list of networks with optional filtering.
        
        Args:
            page: Page number (default: 1)
            per_page: Items per page (default: 20)
            filter_type: Filter type - 'all', 'backuped_only', or 'non_backuped_only' (default: 'all')
        
        Returns:
            Dictionary with:
            - items: List of network dictionaries with subnet, termination_points, is_backuped, cost, area
            - pagination: Dictionary with page, per_page, total, total_pages
        """
        params = {
            'page': page,
            'per_page': per_page,
            'filter_type': filter_type
        }
        response = self._client.get(f'/graph/{self.graph_time}/networks', params=params)
        return response.json()
    
    def nodes_list(
        self,
        page: int = 1,
        per_page: int = 50,
        protocol: Optional[str] = None,
        watcher: Optional[bool] = None,
        area: Optional[str] = None,
        abr: Optional[bool] = None,
        asbr: Optional[bool] = None,
        overload: Optional[bool] = None,
        attached: Optional[bool] = None,
        maxmetric: Optional[bool] = None,
    ) -> Dict[str, Any]:
        """Get paginated list of nodes/routers.

        Args:
            page: Page number (default: 1)
            per_page: Items per page (default: 50)
            protocol: Filter — only return if graph matches protocol (ospf, ospfv3, isis, yaml)
            watcher: Filter — True for watcher-uploaded graphs, False for manually parsed
            area: Filter — only return if graph contains this area (e.g. "0", "0.0.0.1", "49.0001")
            abr: OSPF role filter — True for Area Border Routers only (False for non-ABRs)
            asbr: OSPF role filter — True for AS Boundary Routers only (False for non-ASBRs)
            overload: IS-IS filter — True for routers with the overload (OL) bit set
            attached: IS-IS filter — True for routers with the attached (ATT) bit set
            maxmetric: OSPF filter — True for routers in max-metric (RFC 3137 stub router) state

        Returns:
            Dictionary with:
            - items: List of node dictionaries with node_id, hostname, systemid (IS-IS),
                     pseudo_rid (IS-IS), networks_count, areas, is_isis, and node_attributes
                     (role flags: abr/asbr/maxmetric for OSPF, overload/attached for IS-IS)
            - pagination: Dictionary with page, per_page, total, total_pages
        """
        params: Dict[str, Any] = {'page': page, 'per_page': per_page}
        if protocol:
            params['protocol'] = protocol
        if watcher is not None:
            params['watcher'] = str(watcher).lower()
        if area:
            params['area'] = area
        for flag_name, flag_value in (('abr', abr), ('asbr', asbr), ('overload', overload), ('attached', attached), ('maxmetric', maxmetric)):
            if flag_value is not None:
                params[flag_name] = int(flag_value)
        response = self._client.get(f'/graph/{self.graph_time}/nodes', params=params)
        return response.json()
    
    def areas_list(self) -> Dict[str, Any]:
        """Get list of areas (no pagination needed, typically < 20 areas).

        Works for both OSPF and IS-IS graphs.
        OSPF: area_id is "0", "1", or dotted quad; is_backbone is included.
        IS-IS: area_id is the IS-IS area address string ("49.0001"); is_backbone is omitted.

        Returns:
            Dictionary with:
            - items: List of area dicts with area_id, nodes_count, networks_count,
                     and is_backbone (OSPF only)
        """
        response = self._client.get(f'/graph/{self.graph_time}/areas')
        return response.json()
    
    def edges_list(
        self,
        src_node: Optional[str] = None,
        dst_node: Optional[str] = None,
        protocol: Optional[str] = None,
        watcher: Optional[bool] = None,
        area: Optional[str] = None,
        include: Optional[List[str]] = None,
        page: int = 1,
        per_page: int = 50,
        **edge_query_params: Union[str, int, float]
    ) -> Dict[str, Any]:
        """Get paginated list of edges with optional filters and TE link attribute querying.

        Supports exact match (e.g. weight=10) and range operators __gt, __lt, __gte, __lte
        for numeric/float attributes (e.g. temetric__gt=100, unreserved_bw_0__lt=1000000000).
        TE attributes when present: temetric, admin_group, max_link_bw, max_rsrv_link_bw,
        unreserved_bw_0 through unreserved_bw_7. IS-IS: isis_level=1 or 2.
        Arbitrary user-defined attributes (e.g. isp_provider='verizon') are also supported.

        Args:
            src_node: Filter edges by source node name.
            dst_node: Filter edges by destination node name.
            protocol: Graph-level filter (ospf, ospfv3, isis, yaml).
            watcher: Graph-level filter — True for watcher-uploaded, False for manually parsed.
            area: Graph-level filter by area (e.g. "0", "0.0.0.1", "49.0001").
            include: Extra MPLS-TE fields, hidden by default: 'lsp_left_bw' (how much TE
                bandwidth is left per edge after accounting for placed LSP tunnels —
                lsp_left_bw_0..7 plus a human-readable lsp_reserved_bw/lsp_left_bw/
                lsp_bandwidth_usage pair at the default priority-7 pool), 'lsps' (which
                LSP tunnels traverse this edge), 'is_te_link' (whether the edge is
                TE-enabled), 'edge_key' (stable identity, needed for lsps_list(via_edge_key=)
                on parallel/ECMP edges).
            page: Page number (default: 1).
            per_page: Items per page (default: 50).
            **edge_query_params: Per-edge attribute filters. Exact match or range suffix
                (e.g. weight=10, temetric__gt=100, unreserved_bw_0__lt=1e9).

        Returns:
            Dictionary with:
            - items: List of edge dictionaries with src, dst, weight, and optional TE/IS-IS/user attrs
            - pagination: Dictionary with page, per_page, total, total_pages
        """
        params: Dict[str, Any] = {'page': page, 'per_page': per_page}
        if src_node is not None:
            params['src_node'] = src_node
        if dst_node is not None:
            params['dst_node'] = dst_node
        if protocol:
            params['protocol'] = protocol
        if watcher is not None:
            params['watcher'] = str(watcher).lower()
        if area:
            params['area'] = area
        if include:
            params['include'] = ','.join(include)
        params.update(edge_query_params)
        response = self._client.get(f'/graph/{self.graph_time}/edges', params=params)
        return response.json()

    def lsps_list(
        self,
        status: Optional[str] = None,
        via_node: Optional[str] = None,
        via_edge: Optional[str] = None,
        via_edge_key: Optional[str] = None,
        include_path: bool = False,
    ) -> Dict[str, Any]:
        """Get MPLS TE LSP tunnels attached to this graph.

        Each returned path carries its last CSPF placement outcome: placed
        (bool), reason (why placement failed, null when placed), cost (total
        path metric, null when unplaced).

        Args:
            status: 'placed' or 'unplaced' — keep only paths matching.
            via_node: Keep only paths whose CSPF-computed path visits this node.
            via_edge: 'srcNode,dstNode' — keep only paths traversing this hop.
            via_edge_key: Exact stable edge_key (from edges_list(include=['edge_key']))
                — disambiguates parallel/ECMP edges that via_edge alone cannot.
            include_path: Also return each path's expanded node-name path
                (omitted by default to keep the list light with many tunnels).
        """
        params: Dict[str, Any] = {}
        if status:
            params['status'] = status
        if via_node:
            params['via_node'] = via_node
        if via_edge:
            params['via_edge'] = via_edge
        if via_edge_key:
            params['via_edge_key'] = via_edge_key
        if include_path:
            params['include'] = 'path'
        kwargs = {'params': params} if params else {}
        return self._client.get(f'/graph/{self.graph_time}/lsps', **kwargs).json()

    def lsp(self, name: str) -> Dict[str, Any]:
        """Get one MPLS TE LSP tunnel by name (always includes each path's expanded path)."""
        return self._client.get(f'/graph/{self.graph_time}/lsps/{name}').json()

    def add_lsp(self, lsp: Dict[str, Any]) -> Dict[str, Any]:
        """Add an MPLS TE LSP tunnel."""
        return self._client.post(f'/graph/{self.graph_time}/lsps', json=lsp).json()

    def update_lsp(self, name: str, **changes: Any) -> Dict[str, Any]:
        """Update or rename an MPLS TE LSP tunnel."""
        return self._client.patch(f'/graph/{self.graph_time}/lsps/{name}', json=changes).json()

    def delete_lsp(self, name: str) -> Dict[str, Any]:
        """Delete one MPLS TE LSP tunnel."""
        return self._client.delete(f'/graph/{self.graph_time}/lsps/{name}').json()

    def delete_lsps(self) -> Dict[str, Any]:
        """Delete all MPLS TE LSP tunnels attached to this graph."""
        return self._client.delete(f'/graph/{self.graph_time}/lsps').json()

    def cspf_path(
        self,
        node_a: str,
        node_b: str,
        bandwidth: Optional[str] = None,
        metric_type: str = 'igp',
        admin_exclude_any: Optional[List[str]] = None,
        admin_include_any: Optional[List[str]] = None,
        admin_include_all: Optional[List[str]] = None,
        srlg_exclude: Optional[List[int]] = None,
        setup_priority: int = 7,
    ) -> Dict[str, Any]:
        """Constrained-shortest-path (CSPF) feasibility check between two nodes.

        On-demand computation, same class as `paths.shortest` — just over a
        graph pre-filtered by the given TE constraints instead of the plain
        one. No tunnel is created or persisted.

        Returns:
            Dictionary with 'path' (list of node names, empty if none satisfies
            the constraints), 'cost' (null if unplaced), 'reason' (why
            placement failed; empty string on success).
        """
        params: Dict[str, Any] = {'metric_type': metric_type, 'setup_priority': setup_priority}
        if bandwidth:
            params['bandwidth'] = bandwidth
        if admin_exclude_any:
            params['admin_exclude_any'] = ','.join(admin_exclude_any)
        if admin_include_any:
            params['admin_include_any'] = ','.join(admin_include_any)
        if admin_include_all:
            params['admin_include_all'] = ','.join(admin_include_all)
        if srlg_exclude:
            params['srlg_exclude'] = ','.join(str(value) for value in srlg_exclude)
        response = self._client.get(
            f'/graph/{self.graph_time}/cspf-path/{node_a}/{node_b}', params=params)
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
        is_monitored: Optional[bool] = None,
        name: Optional[str] = None,
    ) -> Optional[Graph]:
        """Retrieve a graph.

        Args:
            latest: If True, return only the latest graph (default: True)
            protocol: Filter by protocol (ospf, ospfv3, isis, yaml)
            area: Filter by area number
            is_monitored: True = only watcher-received graphs, False = only manually uploaded
            name: Case-insensitive substring over graph_time or watcher_name

        Returns:
            Graph object or None if not found
        """
        params: Dict[str, Any] = {}
        if latest:
            params['latest_only'] = True
        if protocol:
            params['protocol'] = protocol
        if area:
            params['area'] = area
        if is_monitored is not None:
            params['is_monitored'] = str(is_monitored).lower()
        if name:
            params['name'] = name

        response = self._client.get('/graph/', params=params)
        body = response.json()
        items = body.get('items', []) if isinstance(body, dict) else (body or [])
        if items:
            return Graph(self._client, items[0])
        return None

    def list(
        self,
        protocol: Optional[str] = None,
        area: Optional[str] = None,
        is_monitored: Optional[bool] = None,
        name: Optional[str] = None,
        latest_only: bool = False,
        page: int = 1,
        per_page: int = 50,
    ) -> List[Graph]:
        """List graphs with optional filters.

        Args:
            protocol: Filter by protocol (ospf, ospfv3, isis, yaml)
            area: Filter by area number
            is_monitored: True = only watcher-received graphs, False = only manually uploaded
            name: Case-insensitive substring over graph_time or watcher_name (e.g. "before_maintenance")
            latest_only: Return only the single newest graph among those matching the filters
            page: Page number, 1-indexed
            per_page: Items per page

        Returns:
            List of Graph objects (each exposing is_monitored and is_live)
        """
        params: Dict[str, Any] = {'page': page, 'per_page': per_page}
        if protocol:
            params['protocol'] = protocol
        if area:
            params['area'] = area
        if is_monitored is not None:
            params['is_monitored'] = str(is_monitored).lower()
        if name:
            params['name'] = name
        if latest_only:
            params['latest_only'] = True

        response = self._client.get('/graph/', params=params)
        body = response.json()
        items = body.get('items', []) if isinstance(body, dict) else (body or [])
        return [Graph(self._client, g) for g in items]
    
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
        watcher_name: Optional[str] = None,
        graph_description: Optional[str] = None
    ) -> Graph:
        """Upload a raw LSDB and create a new graph.

        Args:
            lsdb_data: Raw LSDB text output
            vendor: Vendor name (e.g., 'Cisco', 'Juniper', 'FRR')
            protocol: Protocol name (ospf, ospfv3, isis)
            watcher_name: Optional watcher name
            graph_description: Optional human-readable suffix to tell saved graphs apart

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
        if graph_description:
            payload['graph_description'] = graph_description

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
    
    def upload_diagram(self, yaml_str: str) -> Graph:
        """Upload a YAML diagram and create a new graph.
        
        Args:
            yaml_str: YAML diagram as a string. Format:
                nodes:
                  - name: node1
                  - name: node2
                edges:
                  - src: node1
                    dst: node2
                    weight: 10
        
        Returns:
            Graph object representing the uploaded diagram
            
        Raises:
            ValidationError: If YAML is invalid or empty
        """
        payload = {'yaml_diagram_str': yaml_str}
        response = self._client.post('/diagram', json=payload)
        diagram_data = response.json()
        # DIAGRAM response has: url, graph_time, timestamp
        # Convert to Graph-compatible format
        graph_data = {
            'graph_time': diagram_data['graph_time'],
            'timestamp': diagram_data.get('timestamp'),
            'protocol': 'yaml',
            'is_from_watcher': False
        }
        return Graph(self._client, graph_data)
