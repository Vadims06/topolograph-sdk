"""Path resource for Topolograph API."""

from typing import List, Tuple


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
        self.overload = data.get('overload')

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

    def shortest(self, src_node: str, dst_node: str, with_lsps: bool = False) -> Path:
        """Compute the shortest path between two nodes.

        Plain IGP shortest path by default. For "what if this link is down"
        backup-path analysis, use `edge_failure_reaction` instead -- that
        question now has its own endpoint (whole-network impact, not just a
        recomputed path).

        Args:
            src_node: Source node identifier
            dst_node: Destination node identifier
            with_lsps: If True, account for autoroute-enabled MPLS-TE tunnels
                as forwarding shortcuts -- the path traffic actually takes
                given the tunnels currently in the graph, not the plain IGP
                path. Off by default (a signaled LSP does not redirect
                traffic on its own without autoroute configured on the tunnel).

        Returns:
            Path object
        """
        params = {'with_lsps': 'true'} if with_lsps else {}
        response = self._client.get(
            f'/graph/{self.graph_time}/path/{src_node}/{dst_node}', params=params)
        return Path(response.json())

    def shortest_network(self, src_ip_or_network: str, dst_ip_or_network: str) -> Path:
        """Compute the shortest path between two IP addresses or networks.

        Args:
            src_ip_or_network: Source IP address or network
            dst_ip_or_network: Destination IP address or network

        Returns:
            Path object
        """
        params = {
            'src_ip_or_network': src_ip_or_network,
            'dst_ip_or_network': dst_ip_or_network,
        }
        response = self._client.get(f'/graph/{self.graph_time}/path/network', params=params)
        return Path(response.json())

    def edge_failure_reaction(self, failed_edges: List[Tuple[str, str]]) -> dict:
        """Predict the whole-network impact if one or more links go down.

        Same shape as a node-failure prediction, for links instead of nodes.

        Args:
            failed_edges: List of (src, dst) node-name tuples identifying each failed link

        Returns:
            Dictionary with 'isGraphStillConnected', 'affectedLinks'
            (sptPathsIncreasedInPercent/sptPathsDecreasedInPercent), and
            'disjointedNodes' (list of node-name groups, if the graph split)
        """
        payload = {
            'graph_time': self.graph_time,
            'failed_edges_list': [[src, dst] for src, dst in failed_edges],
        }
        response = self._client.post('/network_reaction/edge_failure/', json=payload)
        return response.json()
