"""Basic multi-Operation tests:

  - create op1 by uss1
  - create sub2 by uss2
  - use sub2 to create op2 by uss2
  - mutate op1
  - delete op1
  - delete op2
  - delete sub2
"""

import datetime
from typing import Dict, Tuple

from . import common


URL_OP1 = 'https://example.com/op1/dss'
URL_SUB1 = 'https://example.com/subs1/dss'
URL_OP2 = 'https://example.com/op2/dss'
URL_SUB2 = 'https://example.com/subs2/dss'


op1_ovn = None
op2_ovn = None


def _make_op1_request():
  time_start = datetime.datetime.utcnow()
  time_end = time_start + datetime.timedelta(minutes=60)
  return {
    'extents': [common.make_vol4(time_start, time_end, 0, 120, common.make_circle(90, 0, 200))],
    'old_version': 0,
    'state': 'Accepted',
    'uss_base_url': URL_OP1,
    'new_subscription': {
      'uss_base_url': URL_SUB1,
      'notify_for_constraints': False
    }
  }


def _make_op2_request():
  time_start = datetime.datetime.utcnow()
  time_end = time_start + datetime.timedelta(minutes=60)
  return {
    'extents': [common.make_vol4(time_start, time_end, 0, 120, common.make_circle(89.999, 0, 200))],
    'old_version': 0,
    'state': 'Accepted',
    'uss_base_url': URL_OP2,
  }


# Parses `subscribers` response field into Dict[USS base URL, Dict[Subscription ID, Notification index]]
def _parse_subscribers(subscribers: Dict) -> Dict[str, Dict[str, int]]:
  return {to_notify['uss_base_url']: {sub['subscription_id']: sub['notification_index']
                                      for sub in to_notify['subscriptions']}
          for to_notify in subscribers}


# Parses AirspaceConflictResponse entities into Dict[Operation ID, Operation Reference] +
# Dict[Constraint ID, Constraint Reference]
def _parse_conflicts(entities: Dict) -> Tuple[Dict[str, Dict], Dict[str, Dict]]:
  ops = {}
  constraints = {}
  for entity in entities:
    op = entity.get('operation_reference', None)
    if op is not None:
      ops[op['id']] = op
    constraint = entity.get('constraint', None)
    if constraint is not None:
      constraints[constraint['id']] = constraint
  return ops, constraints


# Op1 shouldn't exist by ID for USS1 when starting this sequence
# Preconditions: None
# Mutations: None
def test_op1_does_not_exist_get_1(scd_session, op1_uuid):
  resp = scd_session.get('/operation_references/{}'.format(op1_uuid))
  assert resp.status_code == 404, resp.content


# Op1 shouldn't exist by ID for USS2 when starting this sequence
# Preconditions: None
# Mutations: None
def test_op1_does_not_exist_get_2(scd_session2, op1_uuid):
  resp = scd_session2.get('/operation_references/{}'.format(op1_uuid))
  assert resp.status_code == 404, resp.content


# Op1 shouldn't exist when searching for USS1 when starting this sequence
# Preconditions: None
# Mutations: None
def test_op1_does_not_exist_query_1(scd_session, op1_uuid):
  if scd_session is None:
    return
  time_now = datetime.datetime.utcnow()
  end_time = time_now + datetime.timedelta(hours=1)
  resp = scd_session.post('/operation_references/query', json={
    'area_of_interest': common.make_vol4(time_now, end_time, 0, 5000, common.make_circle(89.999, 180, 300))
  })
  assert resp.status_code == 200, resp.content
  assert op1_uuid not in [op['id'] for op in resp.json().get('operation_references', [])]


# Op1 shouldn't exist when searching for USS2 when starting this sequence
# Preconditions: None
# Mutations: None
def test_op1_does_not_exist_query_2(scd_session2, op1_uuid):
  if scd_session2 is None:
    return
  time_now = datetime.datetime.utcnow()
  end_time = time_now + datetime.timedelta(hours=1)
  resp = scd_session2.post('/operation_references/query', json={
    'area_of_interest': common.make_vol4(time_now, end_time, 0, 5000, common.make_circle(89.999, 180, 300))
  })
  assert resp.status_code == 200, resp.content
  assert op1_uuid not in [op['id'] for op in resp.json().get('operation_references', [])]


# Create Op1 normally from USS1 (also creates implicit Subscription)
# Preconditions: None
# Mutations: Operation op1_uuid created by scd_session user
def test_create_op1(scd_session, op1_uuid):
  req = _make_op1_request()
  resp = scd_session.put('/operation_references/{}'.format(op1_uuid), json=req)
  assert resp.status_code == 200, resp.content

  data = resp.json()
  op = data['operation_reference']
  assert op['id'] == op1_uuid
  assert op['uss_base_url'] == URL_OP1
  assert op['time_start']['value'] == req['extents'][0]['time_start']['value']
  assert op['time_end']['value'] == req['extents'][0]['time_end']['value']
  assert op['version'] == 1
  assert 'subscription_id' in op
  assert 'state' not in op
  assert op.get('ovn', '')

  # Make sure the implicit Subscription exists when queried separately
  resp = scd_session.get('/subscriptions/{}'.format(op['subscription_id']))
  assert resp.status_code == 200, resp.content

  global op1_ovn
  op1_ovn = op['ovn']


# Try (unsuccessfully) to delete the implicit Subscription
# Preconditions: Operation op1_uuid created by scd_session user
# Mutations: None
def test_delete_implicit_sub(scd_session, op1_uuid):
  if scd_session is None:
    return
  resp = scd_session.get('/operation_references/{}'.format(op1_uuid))
  assert resp.status_code == 200, resp.content
  implicit_sub_id = resp.json()['operation_reference']['subscription_id']

  resp = scd_session.delete('/subscriptions/{}'.format(implicit_sub_id))
  assert resp.status_code == 400, resp.content


# Try (unsuccessfully) to delete Op1 from non-owning USS
# Preconditions: Operation op1_uuid created by scd_session user
# Mutations: None
def test_delete_op1_by_uss2(scd_session2, op1_uuid):
  resp = scd_session2.delete('/operation_references/{}'.format(op1_uuid))
  assert resp.status_code == 403, resp.content


# Try to create Op2 without specifying a valid Subscription
# Preconditions: Operation op1_uuid created by scd_session user
# Mutations: None
def test_create_op2_no_sub(scd_session2, op2_uuid):
  req = _make_op2_request()
  resp = scd_session2.put('/operation_references/{}'.format(op2_uuid), json=req)
  assert resp.status_code == 400, resp.content


# Create a Subscription we can use for Op2
# Preconditions: Operation op1_uuid created by scd_session user
# Mutations: Subscription sub2_uuid created by scd_session2 user
def test_create_op2sub(scd_session2, sub2_uuid, op1_uuid):
  if scd_session2 is None:
    return
  time_start = datetime.datetime.utcnow()
  time_end = time_start + datetime.timedelta(minutes=70)
  req = {
    "extents": common.make_vol4(time_start, time_end, 0, 1000, common.make_circle(89.999, 0, 250)),
    "old_version": 0,
    "uss_base_url": URL_SUB2,
    "notify_for_operations": True,
    "notify_for_constraints": False
  }
  resp = scd_session2.put('/subscriptions/{}'.format(sub2_uuid), json=req)
  assert resp.status_code == 200, resp.content

  # The Subscription response should mention Op1, but not include its OVN
  data = resp.json()
  ops = data['operations']
  assert len(ops) > 0
  op = [op for op in ops if op['id'] == op1_uuid][0]
  assert not op.get('ovn', '')

  resp = scd_session2.get('/subscriptions/{}'.format(sub2_uuid))
  assert resp.status_code == 200, resp.content


# Try (unsuccessfully) to create Op2 with a missing key
# Preconditions:
#   * Operation op1_uuid created by scd_session user
#   * Subscription sub2_uuid created by scd_session2 user
# Mutations: None
def test_create_op2_no_key(scd_session2, op2_uuid, sub2_uuid, op1_uuid):
  req = _make_op2_request()
  req['subscription_id'] = sub2_uuid
  resp = scd_session2.put('/operation_references/{}'.format(op2_uuid), json=req)
  assert resp.status_code == 409, resp.content
  data = resp.json()
  assert 'entity_conflicts' in data, data
  missing_ops, _ = _parse_conflicts(data['entity_conflicts'])
  assert op1_uuid in missing_ops


# Create Op2 successfully, referencing the pre-existing Subscription
# Preconditions:
#   * Operation op1_uuid created by scd_session user
#   * Subscription sub2_uuid created by scd_session2 user
# Mutations: Operation op2_uuid created by scd_session2 user
def test_create_op2(scd_session2, op2_uuid, sub2_uuid, op1_uuid):
  req = _make_op2_request()
  req['subscription_id'] = sub2_uuid
  req['key'] = [op1_ovn]
  resp = scd_session2.put('/operation_references/{}'.format(op2_uuid), json=req)
  assert resp.status_code == 200, resp.content

  data = resp.json()
  op = data['operation_reference']
  assert op['id'] == op2_uuid
  assert op['uss_base_url'] == URL_OP2
  assert op['time_start']['value'] == req['extents'][0]['time_start']['value']
  assert op['time_end']['value'] == req['extents'][0]['time_end']['value']
  assert op['version'] == 1
  assert 'subscription_id' in op
  assert 'state' not in op
  assert op.get('ovn', '')

  resp = scd_session2.get('/operation_references/{}'.format(op1_uuid))
  assert resp.status_code == 200, resp.content
  implicit_sub_id = resp.json()['operation_reference']['subscription_id']

  # USS2 should definitely be instructed to notify USS1's implicit Subscription of the new Operation
  subscribers = _parse_subscribers(data.get('subscribers', []))
  assert URL_SUB1 in subscribers, subscribers
  assert implicit_sub_id in subscribers[URL_SUB1], subscribers[URL_SUB1]

  global op2_ovn
  op2_ovn = op['ovn']


# Op1 and Op2 should both be visible to USS1, but Op2 shouldn't have an OVN
# Preconditions:
#   * Operation op1_uuid created by scd_session user
#   * Operation op2_uuid created by scd_session2 user
# Mutations: None
def test_read_ops_from_uss1(scd_session, op1_uuid, op2_uuid):
  if scd_session is None:
    return
  time_now = datetime.datetime.utcnow()
  end_time = time_now + datetime.timedelta(hours=1)
  resp = scd_session.post('/operation_references/query', json={
    'area_of_interest': common.make_vol4(time_now, end_time, 0, 5000, common.make_circle(89.999, 180, 300))
  })
  assert resp.status_code == 200, resp.content

  ops = {op['id']: op for op in resp.json().get('operation_references', [])}
  assert op1_uuid in ops
  assert op2_uuid in ops

  assert ops[op1_uuid].get('ovn', '')
  assert not ops[op2_uuid].get('ovn', '')


# Op1 and Op2 should both be visible to USS2, but Op1 shouldn't have an OVN
# Preconditions:
#   * Operation op1_uuid created by scd_session user
#   * Operation op2_uuid created by scd_session2 user
# Mutations: None
def test_read_ops_from_uss2(scd_session2, op1_uuid, op2_uuid):
  if scd_session2 is None:
    return
  time_now = datetime.datetime.utcnow()
  end_time = time_now + datetime.timedelta(hours=1)
  resp = scd_session2.post('/operation_references/query', json={
    'area_of_interest': common.make_vol4(time_now, end_time, 0, 5000, common.make_circle(89.999, 180, 300))
  })
  assert resp.status_code == 200, resp.content

  ops = {op['id']: op for op in resp.json().get('operation_references', [])}
  assert op1_uuid in ops
  assert op2_uuid in ops

  assert not ops[op1_uuid].get('ovn', '')
  assert ops[op2_uuid].get('ovn', '')


# Try (unsuccessfully) to mutate Op1 with various bad keys
# Preconditions:
#   * Operation op1_uuid created by scd_session user
#   * Operation op2_uuid created by scd_session2 user
# Mutations: None
def test_mutate_op1_bad_key(scd_session, op1_uuid, op2_uuid):
  resp = scd_session.get('/operation_references/{}'.format(op1_uuid))
  assert resp.status_code == 200, resp.content
  existing_op = resp.json().get('operation_reference', None)
  assert existing_op is not None, resp.content

  old_req = _make_op1_request()
  req = {
    'extents': old_req['extents'],
    'old_version': existing_op['version'],
    'state': 'Activated',
    'uss_base_url': URL_OP1,
    'subscription_id': existing_op['subscription_id']
  }
  resp = scd_session.put('/operation_references/{}'.format(op1_uuid), json=req)
  assert resp.status_code == 409, resp.content
  missing_ops, _ = _parse_conflicts(resp.json()['entity_conflicts'])
  assert op1_uuid in missing_ops
  assert op2_uuid in missing_ops

  req['key'] = [op1_ovn]
  resp = scd_session.put('/operation_references/{}'.format(op1_uuid), json=req)
  assert resp.status_code == 409, resp.content
  missing_ops, _ = _parse_conflicts(resp.json()['entity_conflicts'])
  assert op2_uuid in missing_ops

  req['key'] = [op2_ovn]
  resp = scd_session.put('/operation_references/{}'.format(op1_uuid), json=req)
  assert resp.status_code == 409, resp.content
  missing_ops, _ = _parse_conflicts(resp.json()['entity_conflicts'])
  assert op1_uuid in missing_ops


# Successfully mutate Op1
# Preconditions:
#   * Operation op1_uuid created by scd_session user
#   * Subscription sub2_uuid created by scd_session2 user
#   * Operation op2_uuid created by scd_session2 user
# Mutations: Operation op1_uuid mutated to second version
def test_mutate_op1(scd_session, op1_uuid, sub2_uuid):
  resp = scd_session.get('/operation_references/{}'.format(op1_uuid))
  assert resp.status_code == 200, resp.content
  existing_op = resp.json().get('operation_reference', None)
  assert existing_op is not None, resp.content

  global op1_ovn

  old_req = _make_op1_request()
  req = {
    'key': [op1_ovn, op2_ovn],
    'extents': old_req['extents'],
    'old_version': existing_op['version'],
    'state': 'Activated',
    'uss_base_url': URL_OP1,
    'subscription_id': existing_op['subscription_id']
  }
  resp = scd_session.put('/operation_references/{}'.format(op1_uuid), json=req)
  assert resp.status_code == 200, resp.content

  data = resp.json()
  op = data['operation_reference']
  assert op['id'] == op1_uuid
  assert op['uss_base_url'] == URL_OP1
  assert op['version'] == 2
  assert op['subscription_id'] == existing_op['subscription_id']
  assert 'state' not in op
  assert op.get('ovn', '')

  # USS1 should definitely be instructed to notify USS2's Subscription of the updated Operation
  subscribers = _parse_subscribers(data.get('subscribers', []))
  assert URL_SUB2 in subscribers, subscribers
  assert sub2_uuid in subscribers[URL_SUB2], subscribers[URL_SUB2]

  op1_ovn = op['ovn']


# Try (unsuccessfully) to delete the stand-alone Subscription that Op2 is relying on
# Preconditions:
#   * Subscription sub2_uuid created by scd_session2 user
#   * Operation op2_uuid created by scd_session2 user
# Mutations: None
def test_delete_dependent_sub(scd_session2, sub2_uuid):
  if scd_session2 is None:
    return
  resp = scd_session2.delete('/subscriptions/{}'.format(sub2_uuid))
  assert resp.status_code == 400, resp.content


# Mutate the stand-alone Subscription
# Preconditions:
#   * Operation op1_uuid created by scd_session user
#   * Subscription sub2_uuid created by scd_session2 user
#   * Operation op2_uuid created by scd_session2 user
# Mutations: Subscription sub2_uuid mutated
def test_mutate_sub2(scd_session2, sub2_uuid, op1_uuid, op2_uuid):
  if scd_session2 is None:
    return
  time_now = datetime.datetime.utcnow()
  time_start = time_now - datetime.timedelta(minutes=1)
  time_end = time_now + datetime.timedelta(minutes=61)

  # Create a good mutation request
  req = _make_op2_request()
  req['uss_base_url'] = URL_SUB2
  req['extents'] = req['extents'][0]
  del req['state']
  req['old_version'] = 1
  req['notify_for_operations'] = True
  req['notify_for_constraints'] = False
  req['extents']['time_start'] = common.make_time(time_start)
  req['extents']['time_end'] = common.make_time(time_end)

  # Attempt mutation with wrong version
  req['old_version'] = 0
  resp = scd_session2.put('/subscriptions/{}'.format(sub2_uuid), json=req)
  assert resp.status_code == 409, resp.content
  req['old_version'] = 1

  # # Attempt mutation with start time that doesn't cover Op2
  # req['extents']['time_start'] = common.make_time(time_now + datetime.timedelta(seconds=5))
  # resp = scd_session2.put('/subscriptions/{}'.format(sub2_uuid), json=req)
  # assert resp.status_code == 400, resp.content
  # req['extents']['time_start'] = common.make_time(time_start)
  #
  # # Attempt mutation with end time that doesn't cover Op2
  # req['extents']['time_end'] = common.make_time(time_now)
  # resp = scd_session2.put('/subscriptions/{}'.format(sub2_uuid), json=req)
  # assert resp.status_code == 400, resp.content
  # req['extents']['time_end'] = common.make_time(time_end)
  #
  # # Attempt mutation with minimum altitude that doesn't cover Op2
  # req['extents']['altitude_lower'] = common.make_altitude(10)
  # resp = scd_session2.put('/subscriptions/{}'.format(sub2_uuid), json=req)
  # assert resp.status_code == 400, resp.content
  # req['extents']['altitude_lower'] = common.make_altitude(0)
  #
  # # Attempt mutation with maximum altitude that doesn't cover Op2
  # req['extents']['altitude_upper'] = common.make_altitude(10)
  # resp = scd_session2.put('/subscriptions/{}'.format(sub2_uuid), json=req)
  # assert resp.status_code == 400, resp.content
  # req['extents']['altitude_upper'] = common.make_altitude(200)
  #
  # # Attempt mutation with outline that doesn't cover Op2
  # old_lat = req['extents']['outline_circle']['center']['lat']
  # req['extents']['outline_circle']['center']['lat'] = 45
  # resp = scd_session2.put('/subscriptions/{}'.format(sub2_uuid), json=req)
  # assert resp.status_code == 400, resp.content
  # req['extents']['outline_circle']['center']['lat'] = old_lat

  # Attempt mutation without notifying for Operations
  req['notify_for_operations'] = False
  resp = scd_session2.put('/subscriptions/{}'.format(sub2_uuid), json=req)
  assert resp.status_code == 400, resp.content
  req['notify_for_operations'] = True

  # Perform a valid mutation
  resp = scd_session2.put('/subscriptions/{}'.format(sub2_uuid), json=req)
  assert resp.status_code == 200, resp.content

  # The Subscription response should mention Op1 and Op2, but not include Op1's OVN
  data = resp.json()
  ops = {op['id']: op for op in data['operations']}
  assert len(ops) >= 2
  assert not ops[op1_uuid].get('ovn', '')
  assert ops[op2_uuid].get('ovn', '')

  # Make sure the Subscription is still retrievable specifically
  resp = scd_session2.get('/subscriptions/{}'.format(sub2_uuid))
  assert resp.status_code == 200, resp.content


# Delete Op1
# Preconditions:
#   * Subscription sub2_uuid created/mutated by scd_session2 user
#   * Operation op2_uuid created by scd_session2 user
# Mutations: Operation op1_uuid deleted
def test_delete_op1(scd_session, op1_uuid, sub2_uuid):
  resp = scd_session.delete('/operation_references/{}'.format(op1_uuid))
  print(resp.content)
  assert resp.status_code == 200, resp.content

  data = resp.json()
  op = data['operation_reference']

  # USS1 should be instructed to notify USS2's Subscription of the deleted Operation
  subscribers = _parse_subscribers(data.get('subscribers', []))
  assert URL_SUB2 in subscribers, subscribers
  assert sub2_uuid in subscribers[URL_SUB2], subscribers[URL_SUB2]

  resp = scd_session.get('/subscriptions/{}'.format(op['subscription_id']))
  assert resp.status_code == 404, resp.content


# Delete Op2
# Preconditions:
#   * Operation op1_uuid deleted
#   * Subscription sub2_uuid created/mutated by scd_session2 user
#   * Operation op2_uuid created by scd_session2 user
# Mutations: Operation op2_uuid deleted
def test_delete_op2(scd_session2, op2_uuid, sub2_uuid):
  resp = scd_session2.delete('/operation_references/{}'.format(op2_uuid))
  assert resp.status_code == 200, resp.content

  data = resp.json()
  op = data['operation_reference']
  assert op['subscription_id'] == sub2_uuid

  # USS2 should be instructed to notify Sub2 of the deleted Operation
  subscribers = _parse_subscribers(data.get('subscribers', []))
  assert URL_SUB2 in subscribers, subscribers
  assert sub2_uuid in subscribers[URL_SUB2], subscribers[URL_SUB2]

  resp = scd_session2.get('/subscriptions/{}'.format(sub2_uuid))
  assert resp.status_code == 200, resp.content


# Delete Subscription used to serve Op2
# Preconditions:
#   * Operation op1_uuid deleted
#   * Subscription sub2_uuid created/mutated by scd_session2 user
#   * Operation op2_uuid deleted
# Mutations: Subscription sub2_uuid deleted
def test_delete_sub2(scd_session2, sub2_uuid):
  if scd_session2 is None:
    return
  resp = scd_session2.delete('/subscriptions/{}'.format(sub2_uuid))
  assert resp.status_code == 200, resp.content
