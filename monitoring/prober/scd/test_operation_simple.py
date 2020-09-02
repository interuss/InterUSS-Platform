"""Basic Operation tests:

  - make sure the Operation doesn't exist with get or query
  - create the Operation with a 60 minute length
  - get by ID
  - search with earliest_time and latest_time
  - mutate
  - delete
"""

import datetime

from monitoring.monitorlib.infrastructure import default_scope
from monitoring.monitorlib import scd
from monitoring.monitorlib.scd import SCOPE_SC, SCOPE_CI, SCOPE_CM


BASE_URL = 'https://example.com/uss'
OP_ID = '0000008c-91c8-4afc-927d-d923f5000000'


def test_ensure_clean_workspace(scd_session):
  resp = scd_session.get('/operation_references/{}'.format(OP_ID), scope=SCOPE_SC)
  if resp.status_code == 200:
    resp = scd_session.delete('/operation_references/{}'.format(OP_ID), scope=SCOPE_SC)
    assert resp.status_code == 200, resp.content
  elif resp.status_code == 404:
    # As expected.
    pass
  else:
    assert False, resp.content


def _make_op1_request():
  time_start = datetime.datetime.utcnow() + datetime.timedelta(minutes=20)
  time_end = time_start + datetime.timedelta(minutes=60)
  return {
    'extents': [scd.make_vol4(time_start, time_end, 0, 120, scd.make_circle(-56, 178, 50))],
    'old_version': 0,
    'state': 'Accepted',
    'uss_base_url': BASE_URL,
    'new_subscription': {
      'uss_base_url': BASE_URL,
      'notify_for_constraints': False
    }
  }


# Preconditions: None
# Mutations: None
@default_scope(SCOPE_SC)
def test_op_does_not_exist_get(scd_session):
  resp = scd_session.get('/operation_references/{}'.format(OP_ID))
  assert resp.status_code == 404, resp.content


# Preconditions: None
# Mutations: None
@default_scope(SCOPE_SC)
def test_op_does_not_exist_query(scd_session):
  time_now = datetime.datetime.utcnow()
  end_time = time_now + datetime.timedelta(hours=1)
  resp = scd_session.post('/operation_references/query', json={
    'area_of_interest': scd.make_vol4(time_now, end_time, 0, 5000, scd.make_circle(-56, 178, 300))
  }, scope=SCOPE_SC)
  assert resp.status_code == 200, resp.content
  assert OP_ID not in [op['id'] for op in resp.json().get('operation_references', [])]

  resp = scd_session.post('/operation_references/query', json={
    'area_of_interest': scd.make_vol4(time_now, end_time, 0, 5000, scd.make_circle(-56, 178, 300))
  }, scope=SCOPE_CI)
  assert resp.status_code == 403, resp.content

  resp = scd_session.post('/operation_references/query', json={
    'area_of_interest': scd.make_vol4(time_now, end_time, 0, 5000, scd.make_circle(-56, 178, 300))
  }, scope=SCOPE_CM)
  assert resp.status_code == 403, resp.content


# Preconditions: None
# Mutations: None
@default_scope(SCOPE_SC)
def test_create_op_single_extent(scd_session):
  req = _make_op1_request()
  req['extents'] = req['extents'][0]
  resp = scd_session.put('/operation_references/{}'.format(OP_ID), json=req)
  assert resp.status_code == 400, resp.content


# Preconditions: None
# Mutations: None
@default_scope(SCOPE_SC)
def test_create_op_missing_time_start(scd_session):
  req = _make_op1_request()
  del req['extents'][0]['time_start']
  resp = scd_session.put('/operation_references/{}'.format(OP_ID), json=req)
  assert resp.status_code == 400, resp.content


# Preconditions: None
# Mutations: None
@default_scope(SCOPE_SC)
def test_create_op_missing_time_end(scd_session):
  req = _make_op1_request()
  del req['extents'][0]['time_end']
  resp = scd_session.put('/operation_references/{}'.format(OP_ID), json=req)
  assert resp.status_code == 400, resp.content


# Preconditions: None
# Mutations: Operation OP_ID created by scd_session user
def test_create_op(scd_session):
  req = _make_op1_request()

  resp = scd_session.put('/operation_references/{}'.format(OP_ID), json=req, scope=SCOPE_CI)
  assert resp.status_code == 403, resp.content

  resp = scd_session.put('/operation_references/{}'.format(OP_ID), json=req, scope=SCOPE_CM)
  assert resp.status_code == 403, resp.content

  resp = scd_session.put('/operation_references/{}'.format(OP_ID), json=req, scope=SCOPE_SC)
  assert resp.status_code == 200, resp.content

  data = resp.json()
  op = data['operation_reference']
  assert op['id'] == OP_ID
  assert op['uss_base_url'] == BASE_URL
  assert op['time_start']['value'] == req['extents'][0]['time_start']['value']
  assert op['time_end']['value'] == req['extents'][0]['time_end']['value']
  assert op['version'] == 1
  assert 'subscription_id' in op
  assert 'state' not in op


# Preconditions: Operation OP_ID created by scd_session user
# Mutations: None
def test_get_op_by_id(scd_session):
  resp = scd_session.get('/operation_references/{}'.format(OP_ID), scope=SCOPE_CI)
  assert resp.status_code == 403, resp.content

  resp = scd_session.get('/operation_references/{}'.format(OP_ID), scope=SCOPE_CM)
  assert resp.status_code == 403, resp.content

  resp = scd_session.get('/operation_references/{}'.format(OP_ID), scope=SCOPE_SC)
  assert resp.status_code == 200, resp.content

  data = resp.json()
  op = data['operation_reference']
  assert op['id'] == OP_ID
  assert op['uss_base_url'] == BASE_URL
  assert op['version'] == 1
  assert 'state' not in op


# Preconditions: None, though preferably Operation OP_ID created by scd_session user
# Mutations: None
@default_scope(SCOPE_SC)
def test_get_op_by_search_missing_params(scd_session):
  resp = scd_session.post('/operation_references/query')
  assert resp.status_code == 400, resp.content


# Preconditions: Operation OP_ID created by scd_session user
# Mutations: None
@default_scope(SCOPE_SC)
def test_get_op_by_search(scd_session):
  resp = scd_session.post('/operation_references/query', json={
    'area_of_interest': scd.make_vol4(None, None, 0, 5000, scd.make_circle(-56, 178, 300))
  })
  assert resp.status_code == 200, resp.content
  assert OP_ID in [x['id'] for x in resp.json().get('operation_references', [])]


# Preconditions: Operation OP_ID created by scd_session user
# Mutations: None
@default_scope(SCOPE_SC)
def test_get_op_by_search_earliest_time_included(scd_session):
  earliest_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=59)
  resp = scd_session.post('/operation_references/query', json={
    'area_of_interest': scd.make_vol4(earliest_time, None, 0, 5000, scd.make_circle(-56, 178, 300))
  })
  assert resp.status_code == 200, resp.content
  assert OP_ID in [x['id'] for x in resp.json()['operation_references']]


# Preconditions: Operation OP_ID created by scd_session user
# Mutations: None
@default_scope(SCOPE_SC)
def test_get_op_by_search_earliest_time_excluded(scd_session):
  earliest_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=81)
  resp = scd_session.post('/operation_references/query', json={
    'area_of_interest': scd.make_vol4(earliest_time, None, 0, 5000, scd.make_circle(-56, 178, 300))
  })
  assert resp.status_code == 200, resp.content
  assert OP_ID not in [x['id'] for x in resp.json()['operation_references']]


# Preconditions: Operation OP_ID created by scd_session user
# Mutations: None
@default_scope(SCOPE_SC)
def test_get_op_by_search_latest_time_included(scd_session):
  latest_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=20)
  resp = scd_session.post('/operation_references/query', json={
    'area_of_interest': scd.make_vol4(None, latest_time, 0, 5000, scd.make_circle(-56, 178, 300))
  })
  assert resp.status_code == 200, resp.content
  assert OP_ID in [x['id'] for x in resp.json()['operation_references']]


# Preconditions: Operation OP_ID created by scd_session user
# Mutations: None
@default_scope(SCOPE_SC)
def test_get_op_by_search_latest_time_excluded(scd_session):
  latest_time = datetime.datetime.utcnow() + datetime.timedelta(minutes=1)
  resp = scd_session.post('/operation_references/query', json={
    'area_of_interest': scd.make_vol4(None, latest_time, 0, 5000, scd.make_circle(-56, 178, 300))
  })
  assert resp.status_code == 200, resp.content
  assert OP_ID not in [x['id'] for x in resp.json()['operation_references']]


# Preconditions: Operation OP_ID created by scd_session user
# Mutations: Operation OP_ID mutated to second version
@default_scope(SCOPE_SC)
def test_mutate_op(scd_session):
  # GET current op
  resp = scd_session.get('/operation_references/{}'.format(OP_ID))
  assert resp.status_code == 200, resp.content
  existing_op = resp.json().get('operation_reference', None)
  assert existing_op is not None

  req = _make_op1_request()
  req = {
    'key': [existing_op["ovn"]],
    'extents': req['extents'],
    'old_version': existing_op['version'],
    'state': 'Activated',
    'uss_base_url': 'https://example.com/uss2',
    'subscription_id': existing_op['subscription_id']
  }

  resp = scd_session.put('/operation_references/{}'.format(OP_ID), json=req, scope=SCOPE_CI)
  assert resp.status_code == 403, resp.content

  resp = scd_session.put('/operation_references/{}'.format(OP_ID), json=req, scope=SCOPE_CM)
  assert resp.status_code == 403, resp.content

  resp = scd_session.put('/operation_references/{}'.format(OP_ID), json=req, scope=SCOPE_SC)
  assert resp.status_code == 200, resp.content

  data = resp.json()
  op = data['operation_reference']
  assert op['id'] == OP_ID
  assert op['uss_base_url'] == 'https://example.com/uss2'
  assert op['version'] == 2
  assert op['subscription_id'] == existing_op['subscription_id']
  assert 'state' not in op


# Preconditions: Operation OP_ID mutated to second version
# Mutations: Operation OP_ID deleted
def test_delete_op(scd_session):
  resp = scd_session.delete('/operation_references/{}'.format(OP_ID), scope=SCOPE_CI)
  assert resp.status_code == 403, resp.content

  resp = scd_session.delete('/operation_references/{}'.format(OP_ID), scope=SCOPE_CM)
  assert resp.status_code == 403, resp.content

  resp = scd_session.delete('/operation_references/{}'.format(OP_ID), scope=SCOPE_SC)
  assert resp.status_code == 200, resp.content


# Preconditions: Operation OP_ID deleted
# Mutations: None
@default_scope(SCOPE_SC)
def test_get_deleted_op_by_id(scd_session):
  resp = scd_session.get('/operation_references/{}'.format(OP_ID))
  assert resp.status_code == 404, resp.content


# Preconditions: Operation OP_ID deleted
# Mutations: None
@default_scope(SCOPE_SC)
def test_get_deleted_op_by_search(scd_session):
  resp = scd_session.post('/operation_references/query', json={
    'area_of_interest': scd.make_vol4(None, None, 0, 5000, scd.make_circle(-56, 178, 300))
  })
  assert resp.status_code == 200, resp.content
  assert OP_ID not in [x['id'] for x in resp.json()['operation_references']]

