"""
SDK sync for the MPLS TE plan (docs/todo/2026-07-16-mpls-lsp-tunnels-plan.md,
flask-visual repo): cspf_path, edges_list(include=), lsps_list filters,
paths.shortest(with_lsps=), paths.edge_failure_reaction.
"""
import pytest

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


@pytest.mark.parametrize('is_te_link, expected', [(True, 'true'), (False, 'false')])
def test_edges_list_is_te_link_filter_is_sent_as_a_lowercase_boolean(is_te_link, expected):
    client = _Client()
    graph = Graph(client, {'graph_time': 'graph-time'})

    graph.edges_list(is_te_link=is_te_link)

    ((_method, _path, kwargs),) = client.calls
    assert kwargs['params']['is_te_link'] == expected


def test_edges_list_without_is_te_link_sends_no_filter():
    client = _Client()
    graph = Graph(client, {'graph_time': 'graph-time'})

    graph.edges_list()

    ((_method, _path, kwargs),) = client.calls
    assert 'is_te_link' not in kwargs['params']


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


def test_cspf_path_level_param():
    client = _Client()
    graph = Graph(client, {'graph_time': 'graph-time'})

    graph.cspf_path('R1', 'R3', level=1)

    ((method, path, kwargs),) = client.calls
    assert method == 'get'
    assert path == '/graph/graph-time/cspf-path/R1/R3'
    assert kwargs['params']['level'] == 1


def test_cspf_path_without_level_omits_query_param():
    client = _Client()
    graph = Graph(client, {'graph_time': 'graph-time'})

    graph.cspf_path('R1', 'R3')

    ((method, path, kwargs),) = client.calls
    assert 'level' not in kwargs['params']


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


@pytest.mark.parametrize('method, failed, path, body', [
    ('edge_failure_reaction', [('R1', 'R2')], '/network-reaction/edge-failure/', {'failed_edges_list': [['R1', 'R2']]}),
    ('node_failure_reaction', ['R2', 'R4'], '/network-reaction/node-failure/', {'failed_nodes_list': ['R2', 'R4']}),
])
def test_paths_failure_reaction(method, failed, path, body):
    client = _Client()
    graph = Graph(client, {'graph_time': 'graph-time'})

    getattr(graph.paths, method)(failed)

    assert client.calls == [('post', path, {'json': {'graph_time': 'graph-time', **body}})]


def test_graph_analyse_reads_the_kind_at_a_moment():
    client = _Client()
    graph = Graph(client, {'graph_time': 'graph-time'})

    graph.analyse('single-point-of-failure', at='2026-11-01T10:00:00Z')

    assert client.calls == [
        ('get', '/graph/graph-time/analyse/single-point-of-failure',
         {'params': {'at': '2026-11-01T10:00:00Z'}}),
    ]


@pytest.mark.parametrize('call, expected', [
    (lambda paths: paths.tree('R1', direction='in'),
     ('get', '/graph/graph-time/path/R1', {'params': {'direction': 'in'}})),
    (lambda paths: paths.underlay(['R1', 'R2'], ['R3'], at='2026-11-01T10:00:00Z'),
     ('post', '/graph/graph-time/analyse/underlay',
      {'json': {'from': ['R1', 'R2'], 'to': ['R3']}, 'params': {'at': '2026-11-01T10:00:00Z'}})),
    (lambda paths: paths.backup_in_inter_area(neighbors_with_ecmp_only=True),
     ('post', '/graph/graph-time/analyse/backup-paths-in-inter-area',
      {'json': {'neighbors_with_ecmp_only': True}, 'params': {}})),
])
def test_paths_analyses(call, expected):
    client = _Client()
    graph = Graph(client, {'graph_time': 'graph-time'})

    call(graph.paths)

    assert client.calls == [expected]


def test_nodes_patch_many_sends_one_request():
    client = _Client()
    graph = Graph(client, {'graph_time': 'graph-time'})
    changes = [{'name': '10.0.0.1', 'hostname': 'r1'}, {'name': '10.0.0.2', 'router_id': '2.2.2.2'}]

    graph.nodes.patch_many(changes)

    assert client.calls == [('patch', '/graph/graph-time/nodes', {'json': changes})]


def test_paths_backup_path_sends_only_what_is_given():
    client = _Client()
    graph = Graph(client, {'graph_time': 'graph-time'})

    graph.paths.backup_path(
        'R1', 'R4', failed_edges=['k1', 'k2'], changed_costs=[{'edge_key': 'k3', 'cost': 50}],
        at='2026-11-01T10:00:00Z')

    assert client.calls == [
        ('post', '/graph/graph-time/analyse/spt-edge-failure', {
            'json': {'from': 'R1', 'to': 'R4', 'shared_media': False, 'failed_edges': ['k1', 'k2'],
                     'changed_costs': [{'edge_key': 'k3', 'cost': 50}]},
            'params': {'at': '2026-11-01T10:00:00Z'}}),
    ]
