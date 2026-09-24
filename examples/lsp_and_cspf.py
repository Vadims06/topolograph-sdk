"""Create an MPLS-TE LSP and run two CSPF feasibility checks (one placeable, one not).

The defaults below are two node IDs from the public TE demo topology. Point
TOPOLOGRAPH_SRC_NODE/TOPOLOGRAPH_DST_NODE at a source/destination pair that
exists in *your* latest graph and has a TE-enabled path between them.

Run:
    export TOPOLOGRAPH_API_TOKEN=...        # from your Topolograph profile
    export TOPOLOGRAPH_SRC_NODE=...         # optional, defaults to the demo topology
    export TOPOLOGRAPH_DST_NODE=...
    python examples/lsp_and_cspf.py
"""
import os

from topolograph import Topolograph
from topolograph.exceptions import NotFoundError

LSP_NAME = 'SDK-EXAMPLE'

client = Topolograph('https://topolograph.com', token=os.environ['TOPOLOGRAPH_API_TOKEN'])
graph = client.graphs.get(latest=True)
print(f'\n  Topolograph SDK — MPLS-TE demo')
print(f'  graph: {graph.graph_time}  ({", ".join(graph.protocols).upper()})\n')

src = os.environ.get('TOPOLOGRAPH_SRC_NODE', '123.123.31.31')
dst = os.environ.get('TOPOLOGRAPH_DST_NODE', '123.14.14.14')

# A tunnel left over from a previous failed run would make add_lsp reject
# this name as a duplicate -- clear it first, best-effort.
try:
    graph.delete_lsp(LSP_NAME)
except NotFoundError:
    pass

# 1) Create an LSP tunnel (persisted on the graph, placed by CSPF on save).
lsp = graph.add_lsp({
    'name': LSP_NAME,
    'src': src,
    'dst': dst,
    'metric_type': 'te',
    'bandwidth': '500M',
    'setup_priority': 7,
    'paths': {'primary': {'role': 'primary', 'bandwidth': '500M'}},
})
try:
    primary = lsp['paths']['primary']
    print(f'  LSP "{lsp["name"]}"  {src} -> {dst}')
    print(f'     bandwidth : {lsp["bandwidth"]}')
    print(f'     placed    : {primary["placed"]}   cost {primary["cost"]}')
    print(f'     path      : {" -> ".join(primary["path"])}\n')

    # 2a) On the demo topology, 500M fits the reservable bandwidth.
    ok = graph.cspf_path(src, dst, bandwidth='500M', metric_type='te')
    status = 'PLACED' if ok['cost'] is not None else 'UNPLACED'
    print(f'  CSPF  bw=500M   {status:<10} cost {ok["cost"]}, {len(ok["path"])} hops')

    # 2b) On the demo topology, 20G exceeds available bandwidth on every path.
    bad = graph.cspf_path(src, dst, bandwidth='20G', metric_type='te')
    status = 'PLACED' if bad['cost'] is not None else 'UNPLACED'
    print(f'  CSPF  bw=20G    {status:<10} {bad["reason"]}\n')
finally:
    # Clean up the tunnel we created, even if a check above failed.
    graph.delete_lsp(LSP_NAME)
    print('  cleaned up.\n')
