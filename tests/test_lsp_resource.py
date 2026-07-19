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


def test_graph_lsp_crud_uses_lsp_api_paths():
    client = _Client()
    graph = Graph(client, {'graph_time': 'graph-time'})

    assert graph.lsps_list() == {'ok': True}
    graph.lsp('LSP-1')
    graph.add_lsp({'name': 'LSP-1'})
    graph.update_lsp('LSP-1', color='red')
    graph.delete_lsp('LSP-1')
    graph.delete_lsps()

    assert client.calls == [
        ('get', '/graph/graph-time/lsps', {}),
        ('get', '/graph/graph-time/lsps/LSP-1', {}),
        ('post', '/graph/graph-time/lsps', {'json': {'name': 'LSP-1'}}),
        ('patch', '/graph/graph-time/lsps/LSP-1', {'json': {'color': 'red'}}),
        ('delete', '/graph/graph-time/lsps/LSP-1', {}),
        ('delete', '/graph/graph-time/lsps', {}),
    ]
