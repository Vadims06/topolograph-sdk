"""Nornir-based topology collector."""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from nornir import InitNornir
from nornir.core.task import Task, Result
from nornir_scrapli.tasks import send_command as scrapli_send_command
try:
    from nornir_netmiko.tasks import netmiko_send_command
except ImportError:
    netmiko_send_command = None

from .inventory import Inventory, InventoryHost
from .commands import get_commands


@dataclass
class HostResult:
    """Result from a single host collection."""
    hostname: str
    vendor: str
    protocol: str
    commands: List[str]
    outputs: Dict[str, str]
    success: bool
    error: Optional[str] = None


@dataclass
class CollectionResult:
    """Result from topology collection."""
    raw_lsdb_text: str
    host_results: List[HostResult]
    errors: List[str]
    
    def __repr__(self) -> str:
        return f"CollectionResult(hosts={len(self.host_results)}, errors={len(self.errors)})"


class TopologyCollector:
    """Collects LSDB data from network devices via SSH using Nornir."""
    
    def __init__(self, inventory_path: str):
        """Initialize the collector.
        
        Args:
            inventory_path: Path to inventory YAML file
        """
        self.inventory = Inventory(inventory_path)
    
    def collect(self, protocol: Optional[str] = None) -> CollectionResult:
        """Execute topology collection.
        
        Collection process:
        1. Read inventory host metadata
        2. Resolve vendor + protocol for each host
        3. Fetch commands from registry
        4. Execute commands via Nornir
        5. Aggregate outputs deterministically
        
        Args:
            protocol: Optional protocol filter (if None, uses protocol from inventory)
        
        Returns:
            CollectionResult with aggregated LSDB text and per-host results
        """
        # Get hosts to collect from
        hosts = self.inventory.get_hosts(protocol=protocol)
        
        if not hosts:
            return CollectionResult(
                raw_lsdb_text="",
                host_results=[],
                errors=["No hosts found in inventory"]
            )
        
        # Initialize Nornir with custom inventory
        nornir = self._init_nornir(hosts)
        
        # Execute collection
        results = nornir.run(task=self._collect_host)
        
        # Process results
        host_results = []
        errors = []
        aggregated_outputs = []
        
        for host_name, result in results.items():
            if result.failed:
                host = next((h for h in hosts if h.name == host_name), None)
                error_msg = str(result.exception) if result.exception else "Unknown error"
                errors.append(f"{host_name}: {error_msg}")
                
                if host:
                    host_results.append(HostResult(
                        hostname=host.hostname,
                        vendor=host.vendor,
                        protocol=host.protocol,
                        commands=[],
                        outputs={},
                        success=False,
                        error=error_msg
                    ))
                continue
            
            # Extract host info
            host = next((h for h in hosts if h.name == host_name), None)
            if not host:
                errors.append(f"Host {host_name} not found in inventory")
                continue
            
            # Get commands for this host
            try:
                commands = get_commands(host.protocol, host.vendor)
            except ValueError as e:
                errors.append(f"{host_name}: {e}")
                host_results.append(HostResult(
                    hostname=host.hostname,
                    vendor=host.vendor,
                    protocol=host.protocol,
                    commands=[],
                    outputs={},
                    success=False,
                    error=str(e)
                ))
                continue
            
            # Process command outputs
            outputs = {}
            host_outputs = []
            
            if isinstance(result.result, dict):
                # Multiple commands executed
                for cmd, cmd_result in result.result.items():
                    if cmd_result.failed:
                        outputs[cmd] = f"ERROR: {cmd_result.exception}"
                        errors.append(f"{host_name} - {cmd}: {cmd_result.exception}")
                    else:
                        output = cmd_result.result if hasattr(cmd_result, 'result') else str(cmd_result)
                        outputs[cmd] = output
                        host_outputs.append(f"=== {host_name} - {cmd} ===\n{output}\n")
            else:
                # Single command
                output = result.result if hasattr(result, 'result') else str(result)
                if commands:
                    outputs[commands[0]] = output
                    host_outputs.append(f"=== {host_name} - {commands[0]} ===\n{output}\n")
            
            host_results.append(HostResult(
                hostname=host.hostname,
                vendor=host.vendor,
                protocol=host.protocol,
                commands=commands,
                outputs=outputs,
                success=True
            ))
            
            # Aggregate outputs (deterministic order by hostname)
            aggregated_outputs.extend(host_outputs)
        
        # Combine all outputs
        raw_lsdb_text = "\n".join(aggregated_outputs)
        
        return CollectionResult(
            raw_lsdb_text=raw_lsdb_text,
            host_results=host_results,
            errors=errors
        )
    
    def _init_nornir(self, hosts: List[InventoryHost]) -> InitNornir:
        """Initialize Nornir with custom inventory from hosts.
        
        Args:
            hosts: List of inventory hosts
        
        Returns:
            Initialized Nornir instance
        """
        import tempfile
        import yaml
        from pathlib import Path
        
        # Create temporary inventory files
        temp_dir = Path(tempfile.mkdtemp())
        hosts_file = temp_dir / "hosts.yaml"
        groups_file = temp_dir / "groups.yaml"
        defaults_file = temp_dir / "defaults.yaml"
        
        # Build hosts dictionary
        hosts_dict = {}
        for host in hosts:
            hosts_dict[host.name] = {
                'hostname': host.hostname,
                'port': host.port,
                'username': host.username,
                'password': host.password,
                'platform': self._get_nornir_platform(host.vendor),
                'data': {
                    'vendor': host.vendor,
                    'protocol': host.protocol
                }
            }
        
        # Write inventory files
        with open(hosts_file, 'w') as f:
            yaml.dump(hosts_dict, f)
        
        with open(groups_file, 'w') as f:
            yaml.dump({}, f)
        
        with open(defaults_file, 'w') as f:
            yaml.dump({}, f)
        
        # Initialize Nornir with SimpleInventory plugin
        nornir = InitNornir(
            inventory={
                'plugin': 'SimpleInventory',
                'options': {
                    'host_file': str(hosts_file),
                    'group_file': str(groups_file),
                    'defaults_file': str(defaults_file)
                }
            },
            runner={
                'plugin': 'threaded',
                'options': {
                    'num_workers': 10
                }
            }
        )
        
        return nornir
    
    def _get_nornir_platform(self, vendor: str) -> str:
        """Map vendor to Nornir platform name.
        
        Args:
            vendor: Vendor name
        
        Returns:
            Nornir platform name
        """
        platform_map = {
            'cisco': 'ios',
            'juniper': 'junos',
            'arista': 'eos',
            'nokia': 'sros',
            'frr': 'generic',  # Use generic for FRR/Quagga
            'quagga': 'generic',
            'huawei': 'huawei'
        }
        return platform_map.get(vendor.lower(), 'generic')
    
    def _collect_host(self, task: Task) -> Result:
        """Task to collect LSDB from a single host.
        
        Args:
            task: Nornir task
        
        Returns:
            Result with command outputs
        """
        host = task.host
        vendor = host.data.get('vendor', '')
        protocol = host.data.get('protocol', '')
        
        # Get commands for this host
        try:
            commands = get_commands(protocol, vendor)
        except ValueError as e:
            return Result(host=host, failed=True, exception=ValueError(str(e)))
        
        # Execute commands - use netmiko for generic platforms, scrapli for others
        results = {}
        platform = host.platform or 'generic'
        
        for cmd in commands:
            try:
                if platform == 'generic' and netmiko_send_command:
                    # Use netmiko for generic platforms (FRR, Quagga, etc.)
                    result = netmiko_send_command(task=task, command_string=cmd)
                else:
                    # Use scrapli for specific platforms
                    result = scrapli_send_command(task=task, command=cmd)
                results[cmd] = result
            except Exception as e:
                results[cmd] = Result(host=host, failed=True, exception=e)
        
        return Result(host=host, result=results)
