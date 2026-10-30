"""Offline checks of API request/release behavior; no network or HA access."""
import ast
import asyncio
import dataclasses
import datetime
import logging
from pathlib import Path
from types import SimpleNamespace
from typing import Any

root = Path(__file__).parent / 'custom_components' / 'aneo_mobility'
for path in root.glob('*.py'):
    ast.parse(path.read_text(), filename=str(path))

class Timeout:
    def __init__(self, seconds): pass
    async def __aenter__(self): return self
    async def __aexit__(self, *args): pass

class Response:
    status = 200
    released = False
    async def json(self):
        return dict(id='test-user', accountId='test-account', userName='test-user',
                    accessToken='test-token', refreshToken='test-refresh',
                    refreshTokenExpiresAt='2099-01-01T00:00:00Z')
    def raise_for_status(self): pass
    def release(self): self.released = True

class Session:
    async def post(self, url, **kwargs):
        assert url.startswith('https://api.aneomobility.com/')
        assert kwargs['allow_redirects'] is False
        self.response = Response()
        self.last_body = kwargs['json']
        return self.response

session = Session()
source = ast.parse((root / 'api.py').read_text())
# Exercise the actual API classes with an offline HTTP double and no HA import.
classes = ast.Module(body=[n for n in source.body if isinstance(n, ast.ClassDef)], type_ignores=[])
ns = dict(Any=Any, dataclass=dataclasses.dataclass, datetime=datetime.datetime,
          timedelta=datetime.timedelta, timezone=datetime.timezone,
          async_get_clientsession=lambda hass: session,
          aiohttp=SimpleNamespace(ClientError=OSError, ClientResponseError=OSError),
          async_timeout=SimpleNamespace(timeout=Timeout), TIMEOUT=20,
          AUTH_PATH='/api/account/authenticate', REFRESH_PATH='/api/account/token/refresh',
          ACCESS_TOKEN_LIFETIME_MINUTES=55, _LOGGER=logging.getLogger('test'))
exec(compile(classes, 'api.py', 'exec'), ns)

async def verify():
    client = ns['AneoMobilityClient'](None, 'https://api.aneomobility.com')
    token = await client.authenticate('test-user', 'test-password')
    assert token.access_token == 'test-token'
    assert session.response.released
    assert client.is_access_token_valid()
    await client.start_charging('test-charger', 1, 'test-subscription')
    assert session.last_body == dict(identifier='test-charger', socketId=1, subscriptionId='test-subscription')
    assert session.response.released
    try:
        ns['AneoMobilityClient'](None, 'http://other-host')
    except ValueError:
        pass
    else:
        raise AssertionError('Unexpected endpoint accepted')

asyncio.run(verify())
print('PASS: Python syntax, login response release, start payload, HTTPS endpoint and redirect restrictions')

# Exercise the real diagnostic property's handling of service states and absent data.
sensor_source = ast.parse((root / 'sensor.py').read_text())
sensor_class = next(n for n in sensor_source.body if isinstance(n, ast.ClassDef) and n.name == 'ActualSocketStatus')
value_fn = next(n for n in sensor_class.body if isinstance(n, ast.FunctionDef) and n.name == 'native_value')
value_fn.decorator_list = []
namespace = {}
module = ast.fix_missing_locations(ast.Module(body=[value_fn], type_ignores=[]))
exec(compile(module, 'sensor.py', 'exec'), namespace)
def read_socket(data):
    return namespace['native_value'](SimpleNamespace(coordinator=SimpleNamespace(data=data), _charger_id='charger'))
for status in ('Preparing', 'Charging', 'SuspendedEVSE', 'Finishing'):
    assert read_socket({'charger': {'state': {'sockets': [{'status': status}]}}}) == status
assert read_socket(None) is None
assert read_socket({'charger': {'state': {'sockets': []}}}) is None
print('PASS: raw socket values and missing data')
