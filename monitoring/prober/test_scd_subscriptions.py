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
import re

from . import scd_common


def _check_sub1(data, sub1_uuid):
  assert data['subscription']['id'] == sub1_uuid
  assert (('notification_index' not in data['subscription']) or
          (data['subscription']['notification_index'] == 0))
  assert data['subscription']['version'] == 1
  assert data['subscription']['uss_base_url'] == 'https://example.com/foo'
  assert data['subscription']['time_start']['format'] == scd_common.TIME_FORMAT_CODE
  assert data['subscription']['time_end']['format'] == scd_common.TIME_FORMAT_CODE
  assert data['subscription']['notify_for_operations'] == True
  assert (('notify_for_constraints' not in data['subscription']) or
          (data['subscription']['notify_for_constraints'] == False))
  assert (('implicit_subscription' not in data['subscription']) or
            (data['subscription']['implicit_subscription'] == False))
  assert (('dependent_operations' not in data['subscription'])
          or len(data['subscription']['dependent_operations']) == 0)
  assert 'operations' in data


def test_scd_sub_does_not_exist_get(scd_session, sub1_uuid):
  if scd_session is None:
    return
  resp = scd_session.get('/subscriptions/{}'.format(sub1_uuid))
  assert resp.status_code == 404, resp.content
  assert resp.json()['message'] == 'resource not found: {}'.format(sub1_uuid)


def test_scd_sub_does_not_exist_query(scd_session, sub1_uuid):
  if scd_session is None:
    return
  resp = scd_session.put('/subscriptions/query')
  assert resp.status_code == 200, resp.content
  assert resp.json()['message'] == 'resource not found: {}'.format(sub1_uuid)


def test_scd_create_sub(scd_session, sub1_uuid):
  if scd_session is None:
    return
  time_start = datetime.datetime.utcnow()
  time_end = time_start + datetime.timedelta(minutes=60)

  resp = scd_session.put(
      '/subscriptions/{}'.format(sub1_uuid),
      json={
        "extents": scd_common.make_vol4(time_start, time_end, 0, 1000, scd_common.make_circle(12, -34, 300)),
        "old_version": 0,
        "uss_base_url": "https://example.com/foo",
        "notify_for_operations": True,
        "notify_for_constraints": False
      })
  assert resp.status_code == 200, resp.content

  data = resp.json()
  assert data['subscription']['time_start']['value'] == time_start.strftime(
      scd_common.DATE_FORMAT)
  assert data['subscription']['time_end']['value'] == time_end.strftime(
      scd_common.DATE_FORMAT)
  _check_sub1(data, sub1_uuid)


def test_scd_get_sub_by_id(scd_session, sub1_uuid):
  if scd_session is None:
    return
  resp = scd_session.get('/subscriptions/{}'.format(sub1_uuid))
  assert resp.status_code == 200, resp.content

  data = resp.json()
  _check_sub1(data, sub1_uuid)


def test_scd_get_sub_by_search(scd_session, sub1_uuid):
  if scd_session is None:
    return
  time_now = datetime.datetime.utcnow()
  resp = scd_session.post(
      '/subscriptions/query',
      json={
        "area_of_interest": scd_common.make_vol4(time_now, time_now, 0, 120,
                                                 scd_common.make_circle(12.00001, -34.00001, 50))
      })
  if resp.status_code != 200:
    print(resp.content)
  assert resp.status_code == 200, resp.content
  assert sub1_uuid in [x['id'] for x in resp.json()['subscriptions']]


def test_scd_delete_sub(scd_session, sub1_uuid):
  if scd_session is None:
    return
  resp = scd_session.delete('/subscriptions/{}'.format(sub1_uuid))
  assert resp.status_code == 200, resp.content


def test_scd_get_deleted_sub_by_id(scd_session, sub1_uuid):
  if scd_session is None:
    return
  resp = scd_session.get('/subscriptions/{}'.format(sub1_uuid))
  assert resp.status_code == 404, resp.content


def test_scd_get_deleted_sub_by_search(scd_session, sub1_uuid):
  if scd_session is None:
    return
  time_now = datetime.datetime.utcnow()
  resp = scd_session.post(
    '/subscriptions/query',
    json={
      "area_of_interest": scd_common.make_vol4(time_now, time_now, 0, 120,
                                               scd_common.make_circle(12.00001, -34.00001, 50))
    })
  assert resp.status_code == 200, resp.content
  assert sub1_uuid not in [x['id'] for x in resp.json()['subscriptions']]
