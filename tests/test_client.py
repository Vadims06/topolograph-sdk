"""Topolograph client: how an HTTP error becomes an SDK exception."""
from unittest.mock import MagicMock

import pytest

from topolograph import Topolograph
from topolograph.exceptions import APIError, ValidationError


def _client_answering(status_code, body):
    client = Topolograph(url='http://server', token='token')
    response = MagicMock(status_code=status_code, ok=False, text='raw body')
    response.json.return_value = body
    client.session.request = MagicMock(return_value=response)
    return client


@pytest.mark.parametrize('body, expected_message', [
    ({'error': 'Attribute does not exist'}, 'Attribute does not exist'),
    ({'detail': "Wrong type, expected 'boolean' for query parameter 'is_te_link'"},
     "Wrong type, expected 'boolean' for query parameter 'is_te_link'"),
    ({'unrelated': 1}, 'Invalid request'),
])
def test_a_400_carries_the_servers_own_wording(body, expected_message):
    with pytest.raises(ValidationError) as raised:
        _client_answering(400, body).get('/graph/g/edges')

    assert str(raised.value) == expected_message
    assert raised.value.status_code == 400


def test_a_422_keeps_its_status_and_response_for_the_caller():
    body = {'error': 'no exact level', 'code': 'isis_level_calculation_unavailable'}

    with pytest.raises(APIError) as raised:
        _client_answering(422, body).get('/graph/g/cspf-path/a/b')

    assert raised.value.status_code == 422
    assert raised.value.response.json()['code'] == 'isis_level_calculation_unavailable'
