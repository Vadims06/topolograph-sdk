"""
SDK sync for the MPLS TE plan (docs/todo/2026-07-16-mpls-lsp-tunnels-plan.md,
flask-visual repo): cspf_path, edges_list(include=), lsps_list filters,
paths.shortest(with_lsps=), paths.edge_failure_reaction.
"""
from topolograph.resources.graph import Graph


class _Response:
    def __init__(self, body):
        self.body = body

    def json(self):
        return self.body


class _Client:
    def __init__(self):
        self.calls = []

    def _call(self, method, path, **kwargs):
        self.calls.append((method, path, kwargs))
        return _Response({'ok': True})

    def get(self, path, **kwargs):
        return self._call('get', path, **kwargs)

    def post(self, path, **kwargs):
        return self._call('post', path, **kwargs)

    def patch(self, path, **kwargs):
        return self._call('patch', path, **kwargs)

    def delete(self, path, **kwargs):
        return self._call('delete', path, **kwargs)


def test_lsps_list_without_filters_matches_old_bare_call():
    client = _Client()
    graph = Graph(client, {'graph_time': 'graph-time'})

    graph.lsps_list()

    assert client.calls == [('get', '/graph/graph-time/lsps', {})]


def test_lsps_list_with_filters_builds_query_params():
    client = _Client()
    graph = Graph(client, {'graph_time': 'graph-time'})

    graph.lsps_list(status='unplaced', via_node='R2', via_edge='R1,R2',
                     via_edge_key='R1|R2|0', include_path=True)

    assert client.calls == [(
        'get', '/graph/graph-time/lsps',
        {'params': {
            'status': 'unplaced', 'via_node': 'R2', 'via_edge': 'R1,R2',
            'via_edge_key': 'R1|R2|0', 'include': 'path',
        }},
    )]


def test_edges_list_include_param():
    client = _Client()
    graph = Graph(client, {'graph_time': 'graph-time'})

    graph.edges_list(include=['lsp_left_bw', 'edge_key'])

    ((method, path, kwargs),) = client.calls
    assert method == 'get'
    assert path == '/graph/graph-time/edges'
    assert kwargs['params']['include'] == 'lsp_left_bw,edge_key'


def test_cspf_path_builds_query_params():
    client = _Client()
    graph = Graph(client, {'graph_time': 'graph-time'})

    result = graph.cspf_path(
        'R1', 'R3', bandwidth='2G', metric_type='te',
        admin_exclude_any=['red'], srlg_exclude=[1001, 1002])

    assert result == {'ok': True}
    ((method, path, kwargs),) = client.calls
    assert method == 'get'
    assert path == '/graph/graph-time/cspf-path/R1/R3'
    assert kwargs['params'] == {
        'metric_type': 'te', 'setup_priority': 7, 'bandwidth': '2G',
        'admin_exclude_any': 'red', 'srlg_exclude': '1001,1002',
    }


def test_paths_shortest_without_with_lsps_omits_query_param():
    client = _Client()
    graph = Graph(client, {'graph_time': 'graph-time'})

    graph.paths.shortest('R1', 'R2')

    assert client.calls == [
        ('get', '/graph/graph-time/path/R1/R2', {'params': {}}),
    ]


def test_paths_shortest_with_lsps_sets_query_param():
    client = _Client()
    graph = Graph(client, {'graph_time': 'graph-time'})

    graph.paths.shortest('R1', 'R2', with_lsps=True)

    assert client.calls == [
        ('get', '/graph/graph-time/path/R1/R2', {'params': {'with_lsps': 'true'}}),
    ]


def test_paths_shortest_network():
    client = _Client()
    graph = Graph(client, {'graph_time': 'graph-time'})

    graph.paths.shortest_network('192.1.112.99', '192.1.213.0/24')

    assert client.calls == [
        ('get', '/graph/graph-time/path/network', {'params': {
            'src_ip_or_network': '192.1.112.99', 'dst_ip_or_network': '192.1.213.0/24',
        }}),
    ]


def test_paths_edge_failure_reaction():
    client = _Client()
    graph = Graph(client, {'graph_time': 'graph-time'})

    graph.paths.edge_failure_reaction([('R1', 'R2')])

    assert client.calls == [
        ('post', '/network_reaction/edge_failure/', {'json': {
            'graph_time': 'graph-time',
            'failed_edges_list': [['R1', 'R2']],
        }}),
    ]
