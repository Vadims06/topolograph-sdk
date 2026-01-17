"""Integration tests for Topolograph SDK with containerlab router1."""

import os
import pytest
from topolograph import Topolograph, TopologyCollector


# Test configuration
API_URL = os.environ.get('TOPOLOGRAPH_URL', 'http://localhost:8080')
API_TOKEN = os.environ.get('TOPOLOGRAPH_TOKEN')
INVENTORY_PATH = os.path.join(os.path.dirname(__file__), 'fixtures', 'inventory.yaml')


@pytest.fixture
def client():
    """Create Topolograph client."""
    return Topolograph(url=API_URL, token=API_TOKEN)


@pytest.fixture
def collector():
    """Create topology collector."""
    return TopologyCollector(INVENTORY_PATH)


class TestSDKIntegration:
    """Integration tests for SDK functionality."""
    
    def test_collect_lsdb(self, collector):
        """Test collecting LSDB from router1."""
        result = collector.collect()
        
        assert result is not None
        assert len(result.host_results) > 0
        
        # Check that we have at least one successful host
        successful_hosts = [h for h in result.host_results if h.success]
        assert len(successful_hosts) > 0, "At least one host should succeed"
        
        # Check that we have LSDB output
        assert result.raw_lsdb_text, "Should have LSDB output"
        assert "IS-IS" in result.raw_lsdb_text or "isis" in result.raw_lsdb_text.lower(), \
            "LSDB should contain IS-IS data"
    
    def test_upload_lsdb(self, collector, client):
        """Test uploading LSDB to Topolograph."""
        # Collect LSDB
        result = collector.collect()
        
        if not result.raw_lsdb_text:
            pytest.skip("No LSDB data collected")
        
        # Get first successful host for vendor/protocol
        successful_hosts = [h for h in result.host_results if h.success]
        if not successful_hosts:
            pytest.skip("No successful hosts")
        
        first_host = successful_hosts[0]
        
        # Upload LSDB
        graph = client.uploader.upload_raw(
            lsdb_text=result.raw_lsdb_text,
            vendor=first_host.vendor.capitalize(),
            protocol=first_host.protocol
        )
        
        assert graph is not None
        assert graph.graph_time is not None
        assert graph.protocol == first_host.protocol
    
    def test_retrieve_graph(self, client):
        """Test retrieving latest graph."""
        graph = client.graphs.get(latest=True)
        
        # Graph might not exist, so we just check the method works
        # If graph exists, verify structure
        if graph:
            assert graph.graph_time is not None
            assert hasattr(graph, 'protocol')
            assert hasattr(graph, 'hosts')
    
    def test_graph_status(self, client):
        """Test getting graph status."""
        graph = client.graphs.get(latest=True)
        
        if not graph:
            pytest.skip("No graph available")
        
        status = graph.status()
        
        assert status is not None
        assert 'status' in status
        assert status['status'] in ['ok', 'warning', 'critical', 'no_monitoring_data']
    
    def test_compute_path(self, client):
        """Test computing shortest path."""
        graph = client.graphs.get(latest=True)
        
        if not graph:
            pytest.skip("No graph available")
        
        # Get nodes from graph
        nodes = graph.nodes.get()
        
        if len(nodes) < 2:
            pytest.skip("Not enough nodes for path computation")
        
        # Compute path between first two nodes
        src = nodes[0].name or nodes[0].id
        dst = nodes[1].name or nodes[1].id
        
        path = graph.paths.shortest(str(src), str(dst))
        
        assert path is not None
        assert hasattr(path, 'paths')
        assert hasattr(path, 'cost')
    
    def test_get_events(self, client):
        """Test getting events."""
        graph = client.graphs.get(latest=True)
        
        if not graph:
            pytest.skip("No graph available")
        
        # Get network events
        network_events = graph.events.get_network_events(last_minutes=60)
        
        assert network_events is not None
        assert 'network_up_down_events' in network_events
        assert 'network_cost_change_events' in network_events
        
        # Get adjacency events
        adjacency_events = graph.events.get_adjacency_events(last_minutes=60)
        
        assert adjacency_events is not None
        assert 'all_host_up_down_events' in adjacency_events
        assert 'adjacency_cost_change_events' in adjacency_events
    
    def test_find_networks(self, client):
        """Test finding networks."""
        graph = client.graphs.get(latest=True)
        
        if not graph:
            pytest.skip("No graph available")
        
        # Get all networks
        networks = graph.networks.get_all()
        
        # Networks might be empty, but method should work
        assert isinstance(networks, list)
        
        # If we have networks, test finding by IP
        if networks:
            # Try to find network by first network's address
            first_network = networks[0]
            found = graph.networks.find_by_network(first_network.network)
            assert found is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
