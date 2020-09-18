"""Operation References corner cases error tests:
"""

import datetime
import json
import uuid

import yaml

from monitoring.monitorlib.infrastructure import default_scope
from monitoring.monitorlib import scd
from monitoring.monitorlib.scd import SCOPE_SC

OP_ID = '00000028-728d-40c4-8eb2-20d19c000000'
OP_ID2 = '0000006e-b4ec-48a3-ae38-426042000000'


def test_ensure_clean_workspace(scd_session):
  for op_id in (OP_ID, OP_ID2):
    resp = scd_session.get('/operation_references/{}'.format(op_id), scope=SCOPE_SC)
    if resp.status_code == 200:
      resp = scd_session.delete('/operation_references/{}'.format(op_id), scope=SCOPE_SC)
      assert resp.status_code == 200, resp.content
    elif resp.status_code == 404:
      # As expected.
      pass
    else:
      assert False, resp.content


@default_scope(SCOPE_SC)
def test_op_ref_area_too_large(scd_session):
  with open('./scd/resources/op_ref_area_too_large.json', 'r') as f:
    req = json.load(f)
  resp = scd_session.post('/operation_references/query', json=req)
  assert resp.status_code == 400, resp.content


@default_scope(SCOPE_SC)
def test_op_ref_start_end_times_past(scd_session):
  with open('./scd/resources/op_ref_start_end_times_past.json', 'r') as f:
    req = json.load(f)
  resp = scd_session.post('/operation_references/query', json=req)
  # It is ok (and useful) to query for past Operations that may not yet have
  # been explicitly deleted.  This is unlike remote ID where ISAs are
  # auto-removed from the perspective of the client immediately after their end
  # time.
  assert resp.status_code == 200, resp.content


@default_scope(SCOPE_SC)
def test_op_ref_incorrect_units(scd_session):
  with open('./scd/resources/op_ref_incorrect_units.json', 'r') as f:
    req = json.load(f)
  resp = scd_session.post('/operation_references/query', json=req)
  assert resp.status_code == 400, resp.content


@default_scope(SCOPE_SC)
def test_op_ref_incorrect_altitude_ref(scd_session):
  with open('./scd/resources/op_ref_incorrect_altitude_ref.json', 'r') as f:
    req = json.load(f)
  resp = scd_session.post('/operation_references/query', json=req)
  assert resp.status_code == 400, resp.content


@default_scope(SCOPE_SC)
def test_op_uss_base_url_non_tls(scd_session):
  with open('./scd/resources/op_uss_base_url_non_tls.json', 'r') as f:
    req = json.load(f)
  resp = scd_session.put('/operation_references/{}'.format(OP_ID), json=req)
  assert resp.status_code == 400, resp.content


@default_scope(SCOPE_SC)
def test_op_bad_subscription_id(scd_session):
  with open('./scd/resources/op_bad_subscription.json', 'r') as f:
    req = json.load(f)
  resp = scd_session.put('/operation_references/{}'.format(OP_ID), json=req)
  assert resp.status_code == 400, resp.content


@default_scope(SCOPE_SC)
def test_op_bad_subscription_id_random(scd_session):
  with open('./scd/resources/op_bad_subscription.json', 'r') as f:
    req = json.load(f)
    req['subscription_id'] = uuid.uuid4().hex
  resp = scd_session.put('/operation_references/{}'.format(OP_ID), json=req)
  assert resp.status_code == 400, resp.content


@default_scope(SCOPE_SC)
def test_op_new_and_existing_subscription(scd_session):
  with open('./scd/resources/op_new_and_existing_subscription.json', 'r') as f:
    req = json.load(f)
  resp = scd_session.put('/operation_references/{}'.format(OP_ID), json=req)
  assert resp.status_code == 400, resp.content


@default_scope(SCOPE_SC)
def test_op_end_time_past(scd_session):
  with open('./scd/resources/op_end_time_past.json', 'r') as f:
    req = json.load(f)
  resp = scd_session.put('/operation_references/{}'.format(OP_ID), json=req)
  assert resp.status_code == 400, resp.content


@default_scope(SCOPE_SC)
def test_op_already_exists(scd_session):
  with open('./scd/resources/op_request_1.json', 'r') as f:
    req = json.load(f)
  resp = scd_session.put('/operation_references/{}'.format(OP_ID), json=req)
  assert resp.status_code == 200, resp.content

  resp = scd_session.put('/operation_references/{}'.format(OP_ID), json=req)
  assert resp.status_code == 409, resp.content

  # Delete operation
  resp = scd_session.delete('/operation_references/{}'.format(OP_ID))
  assert resp.status_code == 200, resp.content

  # Verify deletion
  resp = scd_session.get('/operation_references/{}'.format(OP_ID))
  assert resp.status_code == 404, resp.content


@default_scope(SCOPE_SC)
def test_op_404_version1(scd_session):
  with open('./scd/resources/op_404_version1.json', 'r') as f:
    req = json.load(f)
  resp = scd_session.put('/operation_references/{}'.format(OP_ID), json=req)
  assert resp.status_code == 404, resp.content


@default_scope(SCOPE_SC)
def test_op_bad_state_version0(scd_session):
  with open('./scd/resources/op_bad_state_version0.json', 'r') as f:
    req = json.load(f)
  resp = scd_session.put('/operation_references/{}'.format(OP_ID), json=req)
  assert resp.status_code == 400, resp.content


@default_scope(SCOPE_SC)
def test_op_bad_lat_lon_range(scd_session):
  with open('./scd/resources/op_bad_lat_lon_range.json', 'r') as f:
    req = json.load(f)
  resp = scd_session.put('/operation_references/{}'.format(OP_ID), json=req)
  assert resp.status_code == 400, resp.content


@default_scope(SCOPE_SC)
def test_op_area_too_large_put(scd_session):
  with open('./scd/resources/op_area_too_large_put.json', 'r') as f:
    req = json.load(f)
  resp = scd_session.put('/operation_references/{}'.format(OP_ID), json=req)
  assert resp.status_code == 400, resp.content


@default_scope(SCOPE_SC)
def test_op_bad_time_format(scd_session):
  with open('./scd/resources/op_bad_time_format.json', 'r') as f:
    req = json.load(f)
  resp = scd_session.put('/operation_references/{}'.format(OP_ID), json=req)
  assert resp.status_code == 400, resp.content


@default_scope(SCOPE_SC)
def test_op_repeated_requests(scd_session):
  with open('./scd/resources/op_request_1.json', 'r') as f:
    req = json.load(f)
  resp = scd_session.put('/operation_references/{}'.format(OP_ID), json=req)
  assert resp.status_code == 200, resp.content

  with open('./scd/resources/op_request_1.json', 'r') as f:
    req = json.load(f)
  resp = scd_session.put('/operation_references/{}'.format(OP_ID), json=req)
  assert resp.status_code == 409, resp.content

  # Delete operation
  resp = scd_session.delete('/operation_references/{}'.format(OP_ID))
  assert resp.status_code == 200, resp.content


@default_scope(SCOPE_SC)
def test_op_invalid_id(scd_session):
  with open('./scd/resources/op_request_1.json', 'r') as f:
    req = json.load(f)
  resp = scd_session.put('/operation_references/not_uuid_format', json=req)
  assert resp.status_code == 400, resp.content


@default_scope(SCOPE_SC)
def test_missing_conflicted_operation(scd_session):
  """
  This test reproduces a case where a conflicting Operation did not appear in a
  follow-up area-based query for Operations.
  """
  # Emplace the initial version of Operation 1
  with open('./scd/resources/op_missing_initial.yaml', 'r') as f:
    req = yaml.full_load(f)
  dt = datetime.datetime.utcnow() - scd.start_of(req['extents'])
  req['extents'] = scd.offset_time(req['extents'], dt)
  resp = scd_session.put('/operation_references/{}'.format(OP_ID), json=req)
  assert resp.status_code == 200, resp.content
  ovn1a = resp.json()['operation_reference']['ovn']
  sub_id = resp.json()['operation_reference']['subscription_id']

  # Emplace the pre-existing Operation that conflicted in the original observation
  with open('./scd/resources/op_missing_preexisting_unknown.yaml', 'r') as f:
    req = yaml.full_load(f)
  req['extents'] = scd.offset_time(req['extents'], dt)
  req['key'] = [ovn1a]
  resp = scd_session.put('/operation_references/{}'.format(OP_ID2), json=req)
  assert resp.status_code == 200, resp.content

  # Attempt to update Operation 1 without OVN for the pre-existing Operation
  with open('./scd/resources/op_missing_update.json', 'r') as f:
    req = json.load(f)
  req['extents'] = scd.offset_time(req['extents'], dt)
  req['key'] = [ovn1a]
  req['subscription_id'] = sub_id
  resp = scd_session.put('/operation_references/{}'.format(OP_ID), json=req)
  assert resp.status_code == 409, resp.content
  conflicts = []
  for conflict in resp.json()['entity_conflicts']:
    if conflict.get('operation_reference', None):
      conflicts.append(conflict['operation_reference']['id'])
  assert OP_ID2 in conflicts, resp.content

  # Perform an area-based query on the area occupied by Operation 1
  with open('./scd/resources/op_missing_query.json', 'r') as f:
    req = json.load(f)
  req['area_of_interest'] = scd.offset_time([req['area_of_interest']], dt)[0]
  resp = scd_session.post('/operation_references/query', json=req)
  assert  resp.status_code == 200, resp.content
  ops = [op['id'] for op in resp.json()['operation_references']]
  assert OP_ID in ops, resp.content

  # OP_ID2 not expected here because its ceiling is <575m whereas query floor is
  # >591m.
  assert OP_ID2 not in ops, resp.content


@default_scope(SCOPE_SC)
def test_big_operation_search(scd_session):
  """
  This test reproduces a case where a search resulted in 503 because the
  underlying gRPC backend had crashed.
  """
  with open('./scd/resources/op_big_operation.json', 'r') as f:
    req = json.load(f)
  dt = datetime.datetime.utcnow() - scd.start_of([req['area_of_interest']])
  req['area_of_interest'] = scd.offset_time([req['area_of_interest']], dt)[0]
  resp = scd_session.post('/operation_references/query', json=req)
  assert  resp.status_code == 400, resp.content
