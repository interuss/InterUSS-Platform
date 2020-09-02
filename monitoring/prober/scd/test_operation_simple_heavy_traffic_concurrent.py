"""Basic Operation tests with hundreds of NON-OVERLAPPING operations created CONCURRENTLY.
   The core actions are performed in parallel while others like cleanup, assert response, etc are intended to remain
   sequential.

  - make sure operations do not exist with get or query
  - create 100 operations concurrently, with has non-overlapping volume4d in 2ds, altitude ranges and time windows.
  - get by IDs concurrently
  - search by areas concurrently
  - mutate operations concurrently
  - delete operations concurrently
  - confirm deletion by get and query
"""

import datetime
import functools
import json
from concurrent.futures.thread import ThreadPoolExecutor

from monitoring.monitorlib.infrastructure import default_scope
from monitoring.monitorlib import scd
from monitoring.monitorlib.scd import SCOPE_SC


def _load_op_ids():
  with open('./scd/resources/op_ids_heavy_traffic_concurrent.json', 'r') as f:
    return json.load(f)


def _populate_idx():
  map = {}
  for idx, op_id in enumerate(OP_IDS):
    map[op_id] = idx
  return map


# This test is implemented to fire requests concurrently, given there are several concurrent related issues:
# - https://github.com/interuss/dss/issues/417
# - https://github.com/interuss/dss/issues/418
# - https://github.com/interuss/dss/issues/419
# - https://github.com/interuss/dss/issues/420
# - https://github.com/interuss/dss/issues/421
# We intended to keep the thread count to be 1 to enforce sequential execution till the above issues are resolved.
# By then, just update the 'THREAD_COUNT' to a reasonable thread pool size and everything should still work without
# need to touch anything else.
THREAD_COUNT = 1
BASE_URL = 'https://example.com/uss'
OP_IDS = _load_op_ids()
GROUP_SIZE = len(OP_IDS) // 3
OP_ID_TO_IDX = _populate_idx()

ovn_map = {}


def _calculate_lat(idx):
  return -56 - 0.1 * idx


def _make_op_request_with_extents(extents):
  return {
    'extents': [extents],
    'old_version': 0,
    'state': 'Accepted',
    'uss_base_url': BASE_URL,
    'new_subscription': {
      'uss_base_url': BASE_URL,
      'notify_for_constraints': False
    }
  }


# Generate request with volumes that cover a circle area that initially centered at (-56, 178)
# The circle's center lat shifts 0.1 degree (11.1 km) per sequential idx change
# The altitude and time window won't change with idx
def _make_op_request_differ_in_2d(idx):
  time_start = datetime.datetime.utcnow() + datetime.timedelta(minutes=20)
  time_end = time_start + datetime.timedelta(minutes=60)
  lat = _calculate_lat(idx)

  vol4 = scd.make_vol4(time_start, time_end, 0, 120, scd.make_circle(lat, 178, 50))
  return _make_op_request_with_extents(vol4)


# Generate request with volumes that cover the circle area that centered at (-56, 178)
# The altitude starts with [0, 19] and increases 20 per sequential idx change
# The 2D area and time window won't change with idx
def _make_op_request_differ_in_altitude(idx):
  time_start = datetime.datetime.utcnow() + datetime.timedelta(minutes=20)
  time_end = time_start + datetime.timedelta(minutes=60)
  delta = 20
  alt0 = delta * idx
  alt1 = alt0 + delta - 1

  vol4 = scd.make_vol4(time_start, time_end, alt0, alt1, scd.make_circle(-56, 178, 50))
  return _make_op_request_with_extents(vol4)


# Generate request with volumes that cover the circle area that centered at (-56, 178), with altitude 0 to 120
# The operation lasts 9 mins and the time window is one after one per sequential idx change
# The 2D area and altitude won't change with idx
def _make_op_request_differ_in_time(idx):
  delta = 10
  time_start = datetime.datetime.utcnow() + datetime.timedelta(minutes=20) + datetime.timedelta(minutes=delta * idx)
  time_end = time_start + datetime.timedelta(minutes=delta - 1)

  vol4 = scd.make_vol4(time_start, time_end, 0, 120, scd.make_circle(-56, 178, 50))
  return _make_op_request_with_extents(vol4)


# Generate request with non-overlapping operations in volume4d.
# 1/3 operations will be generated with different 2d areas, altitude ranges and time windows respectively
def _make_op_request(idx):
  if idx < GROUP_SIZE:
    return _make_op_request_differ_in_2d(idx)
  elif idx < GROUP_SIZE * 2:
    return _make_op_request_differ_in_altitude(idx)
  else:
    return _make_op_request_differ_in_time(idx)


def _intersection(list1, list2):
  return list(set(list1) & set(list2))


def _put_operation(req, op_id, scd_session):
  return scd_session.put('/operation_references/{}'.format(op_id), json=req, scope=SCOPE_SC)


def _get_operation(op_id, scd_session):
  return scd_session.get('/operation_references/{}'.format(op_id), scope=SCOPE_SC)


def _query_operation(idx, scd_session):
  lat = _calculate_lat(idx)
  return scd_session.post('/operation_references/query', json={
    'area_of_interest': scd.make_vol4(None, None, 0, 5000, scd.make_circle(lat, 178, 12000))
  }, scope=SCOPE_SC)


def _build_mutate_request(idx, op_id, op_map, scd_session):
  # GET current op
  resp = scd_session.get('/operation_references/{}'.format(op_id))
  assert resp.status_code == 200, resp.content
  existing_op = resp.json().get('operation_reference', None)
  assert existing_op is not None
  op_map[op_id] = existing_op

  req = _make_op_request(idx)
  req = {
    'key': [existing_op["ovn"]],
    'extents': req['extents'],
    'old_version': existing_op['version'],
    'state': 'Activated',
    'uss_base_url': 'https://example.com/uss2',
    'subscription_id': existing_op['subscription_id']
  }
  return req


def _delete_operation(op_id, scd_session):
  return scd_session.delete('/operation_references/{}'.format(op_id), scope=SCOPE_SC)


def _collect_resp_callback(key, op_resp_map, future):
  op_resp_map[key] = future.result()


def test_ensure_clean_workspace(scd_session):
  for op_id in OP_IDS:
    resp = scd_session.get('/operation_references/{}'.format(op_id), scope=SCOPE_SC)
    if resp.status_code == 200:
      resp = scd_session.delete('/operation_references/{}'.format(op_id), scope=SCOPE_SC)
      assert resp.status_code == 200, resp.content
    elif resp.status_code == 404:
      # As expected.
      pass
    else:
      assert False, resp.content


# Preconditions: None
# Mutations: Operations with ids in OP_IDS created by scd_session user
def test_create_ops_concurrent(scd_session):
  assert len(ovn_map) == 0

  op_req_map = {}
  op_resp_map = {}

  # Create opetions concurrently
  with ThreadPoolExecutor(max_workers=THREAD_COUNT) as executor:
    for idx, op_id in enumerate(OP_IDS):
      req = _make_op_request(idx)
      op_req_map[op_id] = req

      future = executor.submit(_put_operation, req, op_id, scd_session)
      future.add_done_callback(functools.partial(_collect_resp_callback, op_id, op_resp_map))

  for op_id, resp in op_resp_map.items():
    assert resp.status_code == 200, resp.content

    req = op_req_map[op_id]
    data = resp.json()
    op = data['operation_reference']
    assert op['id'] == op_id
    assert op['uss_base_url'] == BASE_URL
    assert scd.iso8601_equal(op['time_start']['value'], req['extents'][0]['time_start']['value'])
    assert scd.iso8601_equal(op['time_end']['value'], req['extents'][0]['time_end']['value'])
    assert op['version'] == 1
    assert op['ovn']
    assert 'subscription_id' in op
    assert 'state' not in op

    ovn_map[op_id] = op['ovn']

  assert len(ovn_map) == len(OP_IDS)


# Preconditions: Operations with ids in OP_IDS created by scd_session user
# Mutations: None
def test_get_ops_by_ids_concurrent(scd_session):
  op_resp_map = {}

  # Get opetions concurrently
  with ThreadPoolExecutor(max_workers=THREAD_COUNT) as executor:
    for op_id in OP_IDS:
      future = executor.submit(_get_operation, op_id, scd_session)
      future.add_done_callback(functools.partial(_collect_resp_callback, op_id, op_resp_map))

  for op_id, resp in op_resp_map.items():
    assert resp.status_code == 200, resp.content

    data = resp.json()
    op = data['operation_reference']
    assert op['id'] == op_id
    assert op['uss_base_url'] == BASE_URL
    assert op['version'] == 1
    assert 'state' not in op


# Preconditions: Operations with ids in OP_IDS created by scd_session user
# Mutations: None
@default_scope(SCOPE_SC)
def test_get_ops_by_search_concurrent(scd_session):
  op_resp_map = {}
  total_found_ids = set()

  # Query opetions concurrently
  with ThreadPoolExecutor(max_workers=THREAD_COUNT) as executor:
    for idx in range(len(OP_IDS)):
      future = executor.submit(_query_operation, idx, scd_session)
      future.add_done_callback(functools.partial(_collect_resp_callback, idx, op_resp_map))

  for idx, resp in op_resp_map.items():
    assert resp.status_code == 200, resp.content
    found_ids = [op['id'] for op in resp.json().get('operation_references', [])]
    total_found_ids.update(found_ids)

  assert len(_intersection(OP_IDS, total_found_ids)) == len(OP_IDS)


# Preconditions: Operations with ids in OP_IDS created by scd_session user
# Mutations: Operations with ids in OP_IDS mutated to second version
@default_scope(SCOPE_SC)
def test_mutate_ops_concurrent(scd_session):
  op_req_map = {}
  op_resp_map = {}
  op_map = {}

  # Build mutate requests
  for idx, op_id in enumerate(OP_IDS):
    op_req_map[op_id] = _build_mutate_request(idx, op_id, op_map, scd_session)
  assert len(op_req_map) == len(OP_IDS)

  # Mutate operations in parallel
  with ThreadPoolExecutor(max_workers=THREAD_COUNT) as executor:
    for op_id in OP_IDS:
      req = op_req_map[op_id]
      future = executor.submit(_put_operation, req, op_id, scd_session)
      future.add_done_callback(functools.partial(_collect_resp_callback, op_id, op_resp_map))

  ovn_map.clear()

  for op_id, resp in op_resp_map.items():
    existing_op = op_map[op_id]
    assert existing_op

    assert resp.status_code == 200, resp.content
    data = resp.json()
    op = data['operation_reference']
    assert op['id'] == op_id
    assert op['uss_base_url'] == 'https://example.com/uss2'
    assert op['version'] == 2
    assert op['subscription_id'] == existing_op['subscription_id']
    assert 'state' not in op

    ovn_map[op_id] = op['ovn']

  assert len(ovn_map) == len(OP_IDS)


# Preconditions: Operations with ids in OP_IDS mutated to second version
# Mutations: Operations with ids in OP_IDS deleted
def test_delete_op_concurrent(scd_session):
  op_resp_map = {}

  # Delete operations concurrently
  with ThreadPoolExecutor(max_workers=THREAD_COUNT) as executor:
    for op_id in OP_IDS:
      future = executor.submit(_delete_operation, op_id, scd_session)
      future.add_done_callback(functools.partial(_collect_resp_callback, op_id, op_resp_map))

  assert len(op_resp_map) == len(OP_IDS)

  for resp in op_resp_map.values():
    assert resp.status_code == 200, resp.content
