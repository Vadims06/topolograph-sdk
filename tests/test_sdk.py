#!/usr/bin/env python3
"""Manual test script for Topolograph SDK with router1."""

import os
import sys
from pathlib import Path

# Add SDK to path
sys.path.insert(0, str(Path(__file__).parent))

from topolograph import Topolograph, TopologyCollector

def test_collector():
    """Test LSDB collection from router1."""
    print("=" * 60)
    print("Testing Topology Collector")
    print("=" * 60)
    
    inventory_path = Path(__file__).parent / "fixtures" / "inventory.yaml"
    
    if not inventory_path.exists():
        print(f"ERROR: Inventory file not found: {inventory_path}")
        return False
    
    try:
        collector = TopologyCollector(str(inventory_path))
        print(f"✓ Collector initialized with {len(collector.inventory)} host(s)")
        
        print("\nCollecting LSDB data...")
        result = collector.collect()
        
        print(f"✓ Collection complete")
        print(f"  Successful hosts: {sum(1 for h in result.host_results if h.success)}")
        print(f"  Failed hosts: {sum(1 for h in result.host_results if not h.success)}")
        
        if result.errors:
            print(f"\nWarnings/Errors:")
            for error in result.errors:
                print(f"  - {error}")
        
        if result.raw_lsdb_text:
            print(f"\n✓ LSDB data collected ({len(result.raw_lsdb_text)} characters)")
            print(f"  Preview: {result.raw_lsdb_text[:200]}...")
            return (True, result)
        else:
            print("✗ No LSDB data collected")
            return (False, None)
    
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def test_upload(result, api_url=None, api_token=None):
    """Test uploading LSDB to Topolograph."""
    if not result or not result.raw_lsdb_text:
        print("\nSkipping upload test - no LSDB data")
        return False
    
    print("\n" + "=" * 60)
    print("Testing LSDB Upload")
    print("=" * 60)
    
    api_url = api_url or os.environ.get('TOPOLOGRAPH_URL', 'http://localhost:8080')
    api_token = api_token or os.environ.get('TOPOLOGRAPH_TOKEN')
    
    try:
        client = Topolograph(url=api_url, token=api_token)
        print(f"✓ Client initialized (URL: {api_url})")
        
        # Get first successful host
        successful_hosts = [h for h in result.host_results if h.success]
        if not successful_hosts:
            print("✗ No successful hosts for upload")
            return False
        
        first_host = successful_hosts[0]
        print(f"  Using vendor: {first_host.vendor}, protocol: {first_host.protocol}")
        
        print("\nUploading LSDB...")
        # Map vendor to API format (FRR, Cisco, etc.)
        vendor_map = {
            'frr': 'FRR',
            'cisco': 'Cisco',
            'juniper': 'Juniper',
            'arista': 'Arista',
            'nokia': 'Nokia',
            'quagga': 'Quagga',
            'huawei': 'Huawei'
        }
        vendor_api = vendor_map.get(first_host.vendor.lower(), first_host.vendor.capitalize())
        
        graph = client.uploader.upload_raw(
            lsdb_text=result.raw_lsdb_text,
            vendor=vendor_api,
            protocol=first_host.protocol
        )
        
        print(f"✓ Upload successful!")
        print(f"  Graph Time: {graph.graph_time}")
        print(f"  Protocol: {graph.protocol}")
        if isinstance(graph.hosts, dict):
            print(f"  Hosts: {graph.hosts.get('count', 0)}")
        if isinstance(graph.networks_data, dict):
            print(f"  Networks: {graph.networks_data.get('count', 0)}")
        
        return (True, graph)
    
    except Exception as e:
        print(f"✗ Upload error: {e}")
        import traceback
        traceback.print_exc()
        return False, None


def test_graph_operations(client):
    """Test graph retrieval and operations."""
    print("\n" + "=" * 60)
    print("Testing Graph Operations")
    print("=" * 60)
    
    try:
        # Get latest graph
        print("Retrieving latest graph...")
        graph = client.graphs.get(latest=True)
        
        if not graph:
            print("✗ No graph found")
            return False
        
        print(f"✓ Graph retrieved: {graph.graph_time}")
        print(f"  Protocol: {graph.protocol}")
        
        # Get status
        print("\nGetting graph status...")
        status = graph.status()
        print(f"✓ Status: {status.get('status', 'unknown')}")
        if 'details' in status:
            details = status['details']
            print(f"  Monitored: {details.get('is_monitored', False)}")
            print(f"  Connected: {details.get('is_connected', False)}")
        
        # Get nodes
        print("\nGetting nodes...")
        nodes = graph.nodes.get()
        print(f"✓ Found {len(nodes)} nodes")
        if nodes:
            print(f"  First node: {nodes[0]}")
        
        # Get networks
        print("\nGetting networks...")
        networks = graph.networks.get_all()
        print(f"✓ Found {len(networks)} networks")
        if networks:
            print(f"  First network: {networks[0].network}")
        
        # Test path computation if we have nodes
        if len(nodes) >= 2:
            print("\nComputing shortest path...")
            src = str(nodes[0].name or nodes[0].id)
            dst = str(nodes[1].name or nodes[1].id)
            path = graph.paths.shortest(src, dst)
            print(f"✓ Path computed (cost: {path.cost})")
            if path.paths:
                print(f"  Path: {' -> '.join(path.paths[0])}")
        
        # Get events
        print("\nGetting events...")
        network_events = graph.events.get_network_events(last_minutes=60)
        adjacency_events = graph.events.get_adjacency_events(last_minutes=60)
        print(f"✓ Network events: {len(network_events['network_up_down_events'])} up/down, "
              f"{len(network_events['network_cost_change_events'])} cost changes")
        print(f"✓ Adjacency events: {len(adjacency_events['all_host_up_down_events'])} total")
        
        return True
    
    except Exception as e:
        print(f"✗ Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("Topolograph SDK Integration Test")
    print("=" * 60)
    
    # Test collector
    success, result = test_collector()
    if not success:
        print("\n✗ Collector test failed. Cannot continue.")
        sys.exit(1)
    
    # Test upload
    api_url = os.environ.get('TOPOLOGRAPH_URL', 'http://localhost:8080')
    api_token = os.environ.get('TOPOLOGRAPH_TOKEN')
    
    upload_success, graph = test_upload(result, api_url, api_token)
    
    # Test graph operations if upload succeeded
    if upload_success and graph:
        client = Topolograph(url=api_url, token=api_token)
        test_graph_operations(client)
    
    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
