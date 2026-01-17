"""Command registry for vendor and protocol-specific LSDB collection commands."""

COMMAND_REGISTRY = {
    "ospf": {
        "cisco": [
            "show ip ospf database router",
            "show ip ospf database network",
            "show ip ospf database external"
        ],
        "juniper": [
            "show ospf database router extensive | no-more",
            "show ospf database network extensive | no-more",
            "show ospf database external extensive | no-more"
        ],
        "frr": [
            "show ip ospf database router",
            "show ip ospf database network",
            "show ip ospf database external"
        ],
        "quagga": [
            "show ip ospf database router",
            "show ip ospf database network",
            "show ip ospf database external"
        ],
        "arista": [
            "show ip ospf database router detail",
            "show ip ospf database network detail",
            "show ip ospf database external detail"
        ],
        "nokia": [
            "show router ospf database type router detail",
            "show router ospf database type network detail",
            "show router ospf database type external detail"
        ],
        "cisco_nxos": [
            "show ip ospf database router detail",
            "show ip ospf database network detail",
            "show ip ospf database external detail"
        ],
        "fortinet": [
            "get router info ospf database router lsa",
            "get router info ospf database network lsa",
            "get router info ospf database external lsa"
        ],
        "ruckus": [
            "show ip ospf database link-state router",
            "show ip ospf database link-state network",
            "show ip ospf database external-link-state"
        ],
        "bird": [
            "show ospf state all",
            "show ospf state all",
            "show ospf state all"
        ],
        "mikrotik": [
            "/routing ospf lsa print detail file=lsa.txt",
            "/routing ospf lsa print detail file=lsa.txt",
            "/routing ospf lsa print detail file=lsa.txt"
        ],
        "huawei": [
            "display ospf lsdb router",
            "display ospf lsdb network",
            "display ospf lsdb ase"
        ],
        "paloalto": [
            "show routing protocol ospf dumplsdb",
            "show routing protocol ospf dumplsdb",
            "show routing protocol ospf dumplsdb"
        ],
        "ubiquiti": [
            "show ip ospf database router",
            "show ip ospf database network",
            "show ip ospf database external"
        ],
        "allied_telesis": [
            "show ip ospf database router",
            "show ip ospf database network",
            "show ip ospf database external"
        ],
        "extreme": [
            "show ospf lsdb detail lstype router",
            "show ospf lsdb detail lstype network",
            "show ospf lsdb detail lstype as-external"
        ],
        "ericsson": [
            "show ospf database router detail",
            "show ospf database network detail",
            "show ospf database external detail"
        ]
    },
    "ospfv3": {
        "arista": [
            "show ipv6 ospf database detail"
        ]
    },
    "isis": {
        "cisco": [
            "show isis database detail"
        ],
        "juniper": [
            "show isis database extensive"
        ],
        "frr": [
            "show isis database detail"
        ],
        "nokia": [
            "show router isis database detail"
        ],
        "huawei": [
            "display isis lsdb verbose"
        ]
    }
}


def get_commands(protocol: str, vendor: str) -> list:
    """Get commands for a specific protocol and vendor.
    
    Args:
        protocol: Protocol name (ospf, ospfv3, isis)
        vendor: Vendor name (cisco, juniper, frr, etc.)
    
    Returns:
        List of commands to execute
    
    Raises:
        ValueError: If protocol or vendor not found in registry
    """
    protocol = protocol.lower()
    vendor = vendor.lower()
    
    if protocol not in COMMAND_REGISTRY:
        raise ValueError(f"Protocol '{protocol}' not found in command registry")
    
    if vendor not in COMMAND_REGISTRY[protocol]:
        raise ValueError(
            f"Vendor '{vendor}' not found for protocol '{protocol}'. "
            f"Available vendors: {list(COMMAND_REGISTRY[protocol].keys())}"
        )
    
    return COMMAND_REGISTRY[protocol][vendor].copy()


def list_protocols() -> list:
    """List all supported protocols.
    
    Returns:
        List of protocol names
    """
    return list(COMMAND_REGISTRY.keys())


def list_vendors(protocol: str) -> list:
    """List all supported vendors for a protocol.
    
    Args:
        protocol: Protocol name
    
    Returns:
        List of vendor names
    
    Raises:
        ValueError: If protocol not found
    """
    protocol = protocol.lower()
    if protocol not in COMMAND_REGISTRY:
        raise ValueError(f"Protocol '{protocol}' not found in command registry")
    
    return list(COMMAND_REGISTRY[protocol].keys())
