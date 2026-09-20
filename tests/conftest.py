import pytest


class FakeResponse:
    def __init__(self, body):
        self.body = body

    def json(self):
        return self.body


class FakeClient:
    """Records every call a resource makes and answers each with a canned body."""

    def __init__(self):
        self.calls = []
        self.bodies = {}

    def _call(self, method, path, **kwargs):
        self.calls.append((method, path, kwargs))
        return FakeResponse(self.bodies.get(method, {'ok': True}))

    def get(self, path, **kwargs):
        return self._call('get', path, **kwargs)

    def post(self, path, **kwargs):
        return self._call('post', path, **kwargs)

    def put(self, path, **kwargs):
        return self._call('put', path, **kwargs)

    def patch(self, path, **kwargs):
        return self._call('patch', path, **kwargs)

    def delete(self, path, **kwargs):
        return self._call('delete', path, **kwargs)


@pytest.fixture
def fake_client():
    return FakeClient()
