"""CLI entry point for Topolograph SDK."""

import os
import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

from topolograph import Topolograph, TopologyCollector

app = typer.Typer(help="Topolograph Python SDK CLI")
console = Console()


def get_client(url: Optional[str] = None, token: Optional[str] = None) -> Topolograph:
    """Get Topolograph client instance.
    
    Args:
        url: Optional API URL (defaults to TOPOLOGRAPH_URL env var or http://localhost:8080)
        token: Optional API token (defaults to TOPOLOGRAPH_TOKEN env var)
    
    Returns:
        Topolograph client instance
    """
    api_url = url or os.environ.get('TOPOLOGRAPH_URL', 'http://localhost:8080')
    api_token = token or os.environ.get('TOPOLOGRAPH_TOKEN')
    
    return Topolograph(url=api_url, token=api_token)


@app.command()
def graphs(
    list_all: bool = typer.Option(False, "--list", "-l", help="List all graphs"),
    latest: bool = typer.Option(False, "--latest", help="Get latest graph"),
    protocol: Optional[str] = typer.Option(None, "--protocol", "-p", help="Filter by protocol"),
    area: Optional[str] = typer.Option(None, "--area", "-a", help="Filter by area"),
    watcher: Optional[str] = typer.Option(None, "--watcher", "-w", help="Filter by watcher name"),
    url: Optional[str] = typer.Option(None, "--url", help="Topolograph API URL"),
    token: Optional[str] = typer.Option(None, "--token", "-t", help="API token"),
):
    """List or get graphs from Topolograph."""
    client = get_client(url=url, token=token)
    
    if list_all or (not latest and not list_all):
        # List graphs
        graphs_list = client.graphs.list(
            protocol=protocol,
            area=area,
            watcher_name=watcher,
            latest_only=False
        )
        
        if not graphs_list:
            console.print("[yellow]No graphs found[/yellow]")
            return
        
        table = Table(title="Graphs")
        table.add_column("Graph Time", style="cyan")
        table.add_column("Protocol", style="magenta")
        table.add_column("Watcher", style="green")
        table.add_column("Hosts", justify="right")
        table.add_column("Networks", justify="right")
        table.add_column("Timestamp", style="dim")
        
        for graph in graphs_list:
            hosts_count = graph.hosts.get('count', 0) if isinstance(graph.hosts, dict) else 0
            networks_count = graph.networks_data.get('count', 0) if isinstance(graph.networks_data, dict) else 0
            table.add_row(
                graph.graph_time or "N/A",
                graph.protocol or "N/A",
                graph.watcher_name or "N/A",
                str(hosts_count),
                str(networks_count),
                graph.timestamp or "N/A"
            )
        
        console.print(table)
    else:
        # Get latest graph
        graph = client.graphs.get(
            latest=True,
            protocol=protocol,
            area=area,
            watcher_name=watcher
        )
        
        if not graph:
            console.print("[yellow]No graph found[/yellow]")
            return
        
        console.print(f"[green]Graph Time:[/green] {graph.graph_time}")
        console.print(f"[green]Protocol:[/green] {graph.protocol}")
        console.print(f"[green]Watcher:[/green] {graph.watcher_name or 'N/A'}")
        if isinstance(graph.hosts, dict):
            console.print(f"[green]Hosts:[/green] {graph.hosts.get('count', 0)}")
        if isinstance(graph.networks_data, dict):
            console.print(f"[green]Networks:[/green] {graph.networks_data.get('count', 0)}")
        console.print(f"[green]Timestamp:[/green] {graph.timestamp}")


@app.command()
def ingest(
    inventory: str = typer.Argument(..., help="Path to inventory YAML file"),
    protocol: Optional[str] = typer.Option(None, "--protocol", "-p", help="Protocol filter"),
    output: Optional[str] = typer.Option(None, "--output", "-o", help="Output file for LSDB"),
    url: Optional[str] = typer.Option(None, "--url", help="Topolograph API URL"),
    token: Optional[str] = typer.Option(None, "--token", "-t", help="API token"),
    upload: bool = typer.Option(False, "--upload", "-u", help="Upload collected LSDB to Topolograph"),
):
    """Collect LSDB data from network devices and optionally upload to Topolograph."""
    inventory_path = Path(inventory)
    
    if not inventory_path.exists():
        console.print(f"[red]Error: Inventory file not found: {inventory}[/red]")
        sys.exit(1)
    
    try:
        collector = TopologyCollector(str(inventory_path))
        console.print(f"[cyan]Collecting topology data from {len(collector.inventory)} host(s)...[/cyan]")
        
        result = collector.collect(protocol=protocol)
        
        if result.errors:
            console.print(f"[yellow]Warnings/Errors:[/yellow]")
            for error in result.errors:
                console.print(f"  [yellow]- {error}[/yellow]")
        
        console.print(f"[green]Collection complete![/green]")
        console.print(f"  [green]Successful hosts:[/green] {sum(1 for h in result.host_results if h.success)}")
        console.print(f"  [green]Failed hosts:[/green] {sum(1 for h in result.host_results if not h.success)}")
        
        if output:
            output_path = Path(output)
            output_path.write_text(result.raw_lsdb_text)
            console.print(f"[green]LSDB saved to:[/green] {output_path}")
        else:
            console.print("\n[cyan]LSDB Output:[/cyan]")
            console.print(result.raw_lsdb_text)
        
        if upload:
            if not result.raw_lsdb_text:
                console.print("[red]Error: No LSDB data to upload[/red]")
                sys.exit(1)
            
            # Determine vendor and protocol from first successful host
            successful_hosts = [h for h in result.host_results if h.success]
            if not successful_hosts:
                console.print("[red]Error: No successful hosts to determine vendor/protocol[/red]")
                sys.exit(1)
            
            first_host = successful_hosts[0]
            client = get_client(url=url, token=token)
            
            console.print(f"[cyan]Uploading LSDB to Topolograph...[/cyan]")
            graph = client.uploader.upload_raw(
                lsdb_text=result.raw_lsdb_text,
                vendor=first_host.vendor.capitalize(),
                protocol=first_host.protocol
            )
            
            console.print(f"[green]Upload successful![/green]")
            console.print(f"  [green]Graph Time:[/green] {graph.graph_time}")
            console.print(f"  [green]Protocol:[/green] {graph.protocol}")
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@app.command()
def path(
    src: str = typer.Option(..., "--src", "-s", help="Source node or IP"),
    dst: str = typer.Option(..., "--dst", "-d", help="Destination node or IP"),
    graph_time: Optional[str] = typer.Option(None, "--graph-time", "-g", help="Graph time (default: latest)"),
    network: bool = typer.Option(False, "--network", "-n", help="Compute path between networks/IPs"),
    url: Optional[str] = typer.Option(None, "--url", help="Topolograph API URL"),
    token: Optional[str] = typer.Option(None, "--token", "-t", help="API token"),
):
    """Compute shortest path between two nodes or networks."""
    client = get_client(url=url, token=token)
    
    # Get graph
    if graph_time:
        graph = client.graphs.get_by_time(graph_time)
    else:
        graph = client.graphs.get(latest=True)
    
    if not graph:
        console.print("[red]Error: No graph found[/red]")
        sys.exit(1)
    
    try:
        if network:
            path_result = graph.paths.shortest_network(src, dst)
        else:
            path_result = graph.paths.shortest(src, dst)
        
        console.print(f"[green]Shortest Path (Cost: {path_result.cost}):[/green]")
        for i, path_nodes in enumerate(path_result.paths, 1):
            console.print(f"  [cyan]Path {i}:[/cyan] {' -> '.join(path_nodes)}")
        
        if path_result.unbackup_paths:
            console.print(f"\n[yellow]Unbackup Paths:[/yellow]")
            for i, path_nodes in enumerate(path_result.unbackup_paths, 1):
                console.print(f"  [yellow]Path {i}:[/yellow] {' -> '.join(path_nodes)}")
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


@app.command()
def upload(
    file: str = typer.Option(..., "--file", "-f", help="Path to LSDB file"),
    vendor: str = typer.Option(..., "--vendor", "-v", help="Vendor name (e.g., Cisco, Juniper)"),
    protocol: str = typer.Option(..., "--protocol", "-p", help="Protocol (ospf, ospfv3, isis)"),
    watcher: Optional[str] = typer.Option(None, "--watcher", "-w", help="Watcher name"),
    url: Optional[str] = typer.Option(None, "--url", help="Topolograph API URL"),
    token: Optional[str] = typer.Option(None, "--token", "-t", help="API token"),
):
    """Upload a LSDB file to Topolograph."""
    file_path = Path(file)
    
    if not file_path.exists():
        console.print(f"[red]Error: File not found: {file}[/red]")
        sys.exit(1)
    
    try:
        lsdb_text = file_path.read_text()
        client = get_client(url=url, token=token)
        
        console.print(f"[cyan]Uploading LSDB to Topolograph...[/cyan]")
        graph = client.uploader.upload_raw(
            lsdb_text=lsdb_text,
            vendor=vendor,
            protocol=protocol,
            watcher_name=watcher
        )
        
        console.print(f"[green]Upload successful![/green]")
        console.print(f"  [green]Graph Time:[/green] {graph.graph_time}")
        console.print(f"  [green]Protocol:[/green] {graph.protocol}")
        if isinstance(graph.hosts, dict):
            console.print(f"  [green]Hosts:[/green] {graph.hosts.get('count', 0)}")
        if isinstance(graph.networks_data, dict):
            console.print(f"  [green]Networks:[/green] {graph.networks_data.get('count', 0)}")
    
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    app()
