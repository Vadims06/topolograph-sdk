"""Graph edge methods: they wrap the /diagram/{graph_time}/edges endpoints."""
import pytest

from topolograph.resources.graph import Graph

KEY = 'R1|R2|ord:0'
EDGE = {'id': 7, 'edge_key': KEY, 'src': 'R1', 'dst': 'R2', 'cost': 10}
BY_KEY = ('get', '/diagram/graph-time/edges', {'params': {'edge_key': KEY}})


@pytest.fixture
def graph(fake_client):
    fake_client.bodies['get'] = EDGE
    return Graph(fake_client, {'graph_time': 'graph-time'})


def test_edge_reads_one_edge_by_key(graph, fake_client):
    assert graph.edge(KEY) == EDGE
    assert fake_client.calls == [BY_KEY]


def test_add_edge_posts_endpoints_and_attributes_together(graph, fake_client):
    fake_client.bodies['post'] = EDGE

    assert graph.add_edge('R1', 'R2', weight=10, srlg=[100]) == EDGE
    assert fake_client.calls == [
        ('post', '/diagram/graph-time/edges', {'json': {'src': 'R1', 'dst': 'R2', 'weight': 10, 'srlg': [100]}})]


@pytest.mark.parametrize('isis_level, expected_params', [(None, {}), (1, {'isis_level': 1}), (2, {'isis_level': 2})])
def test_update_edge_patches_then_returns_the_stored_edge(graph, fake_client, isis_level, expected_params):
    assert graph.update_edge(KEY, isis_level=isis_level, srlg=[100]) == EDGE

    assert fake_client.calls == [
        ('patch', '/diagram/graph-time/edges', {'params': expected_params, 'json': {'srlg': [100], 'edge_key': KEY}}),
        BY_KEY,
    ]


def test_replace_edge_puts_only_the_given_attributes(graph, fake_client):
    assert graph.replace_edge(KEY, weight=5) == EDGE

    assert fake_client.calls == [
        ('put', '/diagram/graph-time/edges', {'json': {'weight': 5, 'edge_key': KEY}}),
        BY_KEY,
    ]


def test_delete_edge_returns_nothing(graph, fake_client):
    assert graph.delete_edge(KEY) is None
    assert fake_client.calls == [('delete', '/diagram/graph-time/edges', {'params': {'edge_key': KEY}})]


@pytest.mark.parametrize('call, expected', [
    (lambda graph: graph.edge(7), [('get', '/diagram/graph-time/edges/7', {})]),
    (lambda graph: graph.edge(edge_id=7), [('get', '/diagram/graph-time/edges/7', {})]),
    (lambda graph: graph.update_edge(7, srlg=[1]), [
        ('patch', '/diagram/graph-time/edges/7', {'params': {}, 'json': {'srlg': [1]}}),
        ('get', '/diagram/graph-time/edges/7', {})]),
    (lambda graph: graph.replace_edge(7, weight=5), [
        ('put', '/diagram/graph-time/edges/7', {'json': {'weight': 5}}),
        ('get', '/diagram/graph-time/edges/7', {})]),
    (lambda graph: graph.delete_edge(7), [('delete', '/diagram/graph-time/edges/7', {})]),
], ids=['edge', 'edge_id_keyword', 'update', 'replace', 'delete'])
def test_an_integer_id_still_uses_the_index_routes_and_warns(graph, fake_client, call, expected):
    with pytest.warns(DeprecationWarning, match='edge_key') as warnings_seen:
        call(graph)

    assert len(warnings_seen) == 1
    assert fake_client.calls == expected


def test_an_edge_needs_a_key(graph):
    with pytest.raises(TypeError, match='edge_key'):
        graph.edge()
