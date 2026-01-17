"""Inventory handling for topology collection."""

import yaml
from typing import Dict, Any, List
from pathlib import Path


class InventoryHost:
    """Represents a single host in the inventory."""
    
    def __init__(self, name: str, data: Dict[str, Any]):
        """Initialize an InventoryHost.
        
        Args:
            name: Host name/identifier
            data: Host configuration dictionary
        """
        self.name = name
        self.hostname = data.get('hostname') or data.get('host')
        self.username = data.get('username') or data.get('user')
        self.password = data.get('password')
        self.vendor = data.get('vendor', '').lower()
        self.protocol = data.get('protocol', '').lower()
        self.port = data.get('port', 22)
        
        # Additional connection parameters
        self.connection_options = data.get('connection_options', {})
        
        # Validate required fields
        if not self.hostname:
            raise ValueError(f"Host '{name}' missing required 'hostname' field")
        if not self.vendor:
            raise ValueError(f"Host '{name}' missing required 'vendor' field")
        if not self.protocol:
            raise ValueError(f"Host '{name}' missing required 'protocol' field")
    
    def __repr__(self) -> str:
        return f"InventoryHost(name={self.name}, hostname={self.hostname}, vendor={self.vendor}, protocol={self.protocol})"


class Inventory:
    """Manages network device inventory."""
    
    def __init__(self, inventory_path: str):
        """Initialize inventory from YAML file.
        
        Args:
            inventory_path: Path to inventory YAML file
        
        Raises:
            FileNotFoundError: If inventory file doesn't exist
            ValueError: If inventory format is invalid
        """
        self.path = Path(inventory_path)
        
        if not self.path.exists():
            raise FileNotFoundError(f"Inventory file not found: {inventory_path}")
        
        with open(self.path, 'r') as f:
            try:
                data = yaml.safe_load(f)
            except yaml.YAMLError as e:
                raise ValueError(f"Invalid YAML in inventory file: {e}")
        
        if not isinstance(data, dict):
            raise ValueError("Inventory must be a dictionary")
        
        self.hosts: List[InventoryHost] = []
        for name, host_data in data.items():
            if name.startswith('---'):
                continue  # Skip YAML document separator
            try:
                self.hosts.append(InventoryHost(name, host_data))
            except ValueError as e:
                raise ValueError(f"Error parsing host '{name}': {e}")
    
    def get_hosts(self, protocol: str = None, vendor: str = None) -> List[InventoryHost]:
        """Get hosts filtered by protocol and/or vendor.
        
        Args:
            protocol: Optional protocol filter
            vendor: Optional vendor filter
        
        Returns:
            List of matching InventoryHost objects
        """
        hosts = self.hosts
        
        if protocol:
            protocol = protocol.lower()
            hosts = [h for h in hosts if h.protocol == protocol]
        
        if vendor:
            vendor = vendor.lower()
            hosts = [h for h in hosts if h.vendor == vendor]
        
        return hosts
    
    def __len__(self) -> int:
        return len(self.hosts)
    
    def __iter__(self):
        return iter(self.hosts)
