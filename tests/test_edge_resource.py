"""Graph edge methods: they wrap the /diagram/{graph_time}/edges endpoints."""
import pytest

from topolograph.resources.graph import Graph

EDGE = {'id': 7, 'src': 'R1', 'dst': 'R2', 'cost': 10}


@pytest.fixture
def graph(fake_client):
    fake_client.bodies['get'] = EDGE
    return Graph(fake_client, {'graph_time': 'graph-time'})


def test_edge_reads_one_edge_by_id(graph, fake_client):
    assert graph.edge(7) == EDGE
    assert fake_client.calls == [('get', '/diagram/graph-time/edges/7', {})]


def test_add_edge_posts_endpoints_and_attributes_together(graph, fake_client):
    fake_client.bodies['post'] = EDGE

    assert graph.add_edge('R1', 'R2', weight=10, srlg=[100]) == EDGE
    assert fake_client.calls == [
        ('post', '/diagram/graph-time/edges', {'json': {'src': 'R1', 'dst': 'R2', 'weight': 10, 'srlg': [100]}})]


@pytest.mark.parametrize('isis_level, expected_params', [(None, {}), (1, {'isis_level': 1}), (2, {'isis_level': 2})])
def test_update_edge_patches_then_returns_the_stored_edge(graph, fake_client, isis_level, expected_params):
    assert graph.update_edge(7, isis_level=isis_level, srlg=[100]) == EDGE

    assert fake_client.calls == [
        ('patch', '/diagram/graph-time/edges/7', {'params': expected_params, 'json': {'srlg': [100]}}),
        ('get', '/diagram/graph-time/edges/7', {}),
    ]


def test_replace_edge_puts_only_the_given_attributes(graph, fake_client):
    assert graph.replace_edge(7, weight=5) == EDGE

    assert fake_client.calls == [
        ('put', '/diagram/graph-time/edges/7', {'json': {'weight': 5}}),
        ('get', '/diagram/graph-time/edges/7', {}),
    ]


def test_delete_edge_returns_nothing(graph, fake_client):
    assert graph.delete_edge(7) is None
    assert fake_client.calls == [('delete', '/diagram/graph-time/edges/7', {})]
