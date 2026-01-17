"""Upload pipeline for raw LSDB data."""

from typing import List, Dict, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from ..client import Topolograph

from ..resources.graph import Graph


class Uploader:
    """Handles uploading LSDB data to Topolograph."""
    
    def __init__(self, client: "Topolograph"):
        """Initialize the uploader.
        
        Args:
            client: Topolograph client instance
        """
        self._client = client
    
    def upload_raw(
        self,
        lsdb_text: str,
        vendor: str,
        protocol: str,
        watcher_name: Optional[str] = None
    ) -> Graph:
        """Upload raw LSDB text to Topolograph.
        
        Args:
            lsdb_text: Raw LSDB text output
            vendor: Vendor name (e.g., 'Cisco', 'Juniper', 'FRR')
            protocol: Protocol name (ospf, ospfv3, isis)
            watcher_name: Optional watcher name
        
        Returns:
            Graph object with diff information
        """
        # Map vendor names to API-expected format
        vendor_map = {
            'cisco': 'Cisco',
            'juniper': 'Juniper',
            'arista': 'Arista',
            'nokia': 'Nokia',
            'frr': 'FRR',
            'quagga': 'Quagga',
            'huawei': 'Huawei',
            'bird': 'Bird',
            'mikrotik': 'Mikrotik',
            'paloalto': 'Paloalto',
            'ubiquiti': 'Ubiquiti',
            'alliedtelesis': 'AlliedTelesis',
            'zte': 'ZTE',
            'extreme': 'Extreme',
            'ericsson': 'Ericsson',
            'ruckus': 'Ruckus',
            'fortinet': 'Fortinet'
        }
        
        # Normalize vendor name
        vendor_normalized = vendor_map.get(vendor.lower(), vendor)
        
        payload = {
            'lsdb_output': lsdb_text,
            'vendor_device': vendor_normalized,
            'igp_protocol': protocol
        }
        if watcher_name:
            payload['watcher_name'] = watcher_name
        
        response = self._client.post('/graph/', json=payload)
        return Graph(self._client, response.json())
    
    def upload_multi(self, lsdb_array: List[Dict[str, Any]]) -> Graph:
        """Upload multiple LSDB files to Topolograph.
        
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
