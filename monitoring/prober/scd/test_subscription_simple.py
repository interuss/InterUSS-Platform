"""Basic strategic conflict detection Subscription tests:

  - make sure Subscription doesn't exist by ID
  - make sure Subscription doesn't exist by search
  - create the Subscription with a 60 minute expiry
  - get by ID
  - get by searching a circular area
  - delete
  - make sure Subscription can't be found by ID
  - make sure Subscription can't be found by search
"""

import datetime

from monitoring.monitorlib.infrastructure import default_scope
from monitoring.monitorlib import scd
from monitoring.monitorlib.scd import SCOPE_SC

SUB_ID = '000000b7-cf7e-4d9a-af00-6963ca000000'


def test_ensure_clean_workspace(scd_session):
  resp = scd_session.get('/subscriptions/{}'.format(SUB_ID), scope=SCOPE_SC)
  if resp.status_code == 200:
    resp = scd_session.delete('/subscriptions/{}'.format(SUB_ID), scope=SCOPE_SC)
    assert resp.status_code == 200, resp.content
  elif resp.status_code == 404:
    # As expected.
    pass
  else:
    assert False, resp.content


def _make_sub1_req():
  time_start = datetime.datetime.utcnow()
  time_end = time_start + datetime.timedelta(minutes=60)
  return {
    "extents": scd.make_vol4(time_start, time_end, 0, 1000, scd.make_circle(12, -34, 300)),
    "old_version": 0,
    "uss_base_url": "https://example.com/foo",
    "notify_for_operations": True,
    "notify_for_constraints": False
  }


def _check_sub1(data, sub_id):
  assert data['subscription']['id'] == sub_id
  assert (('notification_index' not in data['subscription']) or
          (data['subscription']['notification_index'] == 0))
  assert data['subscription']['version'] == 1
  assert data['subscription']['uss_base_url'] == 'https://example.com/foo'
  assert data['subscription']['time_start']['format'] == scd.TIME_FORMAT_CODE
  assert data['subscription']['time_end']['format'] == scd.TIME_FORMAT_CODE
  assert data['subscription']['notify_for_operations'] == True
  assert (('notify_for_constraints' not in data['subscription']) or
          (data['subscription']['notify_for_constraints'] == False))
  assert (('implicit_subscription' not in data['subscription']) or
            (data['subscription']['implicit_subscription'] == False))
  assert (('dependent_operations' not in data['subscription'])
          or len(data['subscription']['dependent_operations']) == 0)


@default_scope(SCOPE_SC)
def test_sub_does_not_exist_get(scd_session):
  if scd_session is None:
    return
  resp = scd_session.get('/subscriptions/{}'.format(SUB_ID))
  assert resp.status_code == 404, resp.content


@default_scope(SCOPE_SC)
def test_sub_does_not_exist_query(scd_session):
  if scd_session is None:
    return
  time_now = datetime.datetime.utcnow()
  resp = scd_session.post('/subscriptions/query', json={
    'area_of_interest': scd.make_vol4(None, None, 0, 5000, scd.make_circle(12, -34, 300))
  })
  assert resp.status_code == 200, resp.content
  assert SUB_ID not in [sub['id'] for sub in resp.json().get('subscriptions', [])]


@default_scope(SCOPE_SC)
def test_create_sub(scd_session):
  if scd_session is None:
    return
  req = _make_sub1_req()
  resp = scd_session.put('/subscriptions/{}'.format(SUB_ID), json=req)
  assert resp.status_code == 200, resp.content

  data = resp.json()
  assert data['subscription']['time_start']['value'] == req['extents']['time_start']['value']
  assert data['subscription']['time_end']['value'] == req['extents']['time_end']['value']
  _check_sub1(data, SUB_ID)


@default_scope(SCOPE_SC)
def test_get_sub_by_id(scd_session):
  if scd_session is None:
    return
  resp = scd_session.get('/subscriptions/{}'.format(SUB_ID))
  assert resp.status_code == 200, resp.content

  data = resp.json()
  _check_sub1(data, SUB_ID)


@default_scope(SCOPE_SC)
def test_get_sub_by_search(scd_session):
  if scd_session is None:
    return
  time_now = datetime.datetime.utcnow()
  resp = scd_session.post(
      '/subscriptions/query',
      json={
        "area_of_interest": scd.make_vol4(time_now, time_now, 0, 120,
                                          scd.make_circle(12.00001, -34.00001, 50))
      })
  if resp.status_code != 200:
    print(resp.content)
  assert resp.status_code == 200, resp.content
  assert SUB_ID in [x['id'] for x in resp.json()['subscriptions']]


@default_scope(SCOPE_SC)
def test_mutate_sub(scd_session):
  if scd_session is None:
    return

  # GET current sub1 before mutation
  resp = scd_session.get('/subscriptions/{}'.format(SUB_ID))
  assert resp.status_code == 200, resp.content
  existing_sub = resp.json().get('subscription', None)
  assert existing_sub is not None

  req = _make_sub1_req()
  req['old_version'] = existing_sub['version']
  req['notify_for_constraints'] = True

  resp = scd_session.put('/subscriptions/{}'.format(SUB_ID), json=req)
  assert resp.status_code == 200, resp.content

  data = resp.json()
  assert scd.iso8601_equal(data['subscription']['time_start']['value'], req['extents']['time_start']['value'])
  assert scd.iso8601_equal(data['subscription']['time_end']['value'], req['extents']['time_end']['value'])


@default_scope(SCOPE_SC)
def test_delete_sub(scd_session):
  if scd_session is None:
    return
  resp = scd_session.delete('/subscriptions/{}'.format(SUB_ID))
  assert resp.status_code == 200, resp.content


@default_scope(SCOPE_SC)
def test_get_deleted_sub_by_id(scd_session):
  if scd_session is None:
    return
  resp = scd_session.get('/subscriptions/{}'.format(SUB_ID))
  assert resp.status_code == 404, resp.content


@default_scope(SCOPE_SC)
def test_get_deleted_sub_by_search(scd_session):
  if scd_session is None:
    return
  time_now = datetime.datetime.utcnow()
  resp = scd_session.post(
    '/subscriptions/query',
    json={
      "area_of_interest": scd.make_vol4(time_now, time_now, 0, 120,
                                        scd.make_circle(12.00001, -34.00001, 50))
    })
  assert resp.status_code == 200, resp.content
  assert SUB_ID not in [x['id'] for x in resp.json()['subscriptions']]
