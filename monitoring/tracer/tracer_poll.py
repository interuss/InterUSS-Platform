#!env/bin/python3

import argparse
import datetime
import os
import sys
import time
from typing import Callable, Dict, List, Optional

import s2sphere

from monitoring.monitorlib import auth, infrastructure, versioning
from monitoring.tracer import formatting, geo, tracerlog, polling


def parseArgs() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Test Interoperability of DSSs")

    # Required arguments
    parser.add_argument('--auth', help='Auth spec for obtaining authorization to DSS and USSs; see README.md')
    parser.add_argument('--dss', help='Base URL of DSS instance to query')
    parser.add_argument('--area', help='`lat,lng,lat,lng` for box containing the area to trace interactions for')
    parser.add_argument('--output-folder', help='Path of folder in which to write logs')

    # Feature arguments
    parser.add_argument('--rid-isa-poll-interval', type=float, default=0, help='Seconds beteween each poll of the DSS for ISAs, 0 to disable DSS polling for ISAs')
    parser.add_argument('--rid-subscription-poll-interval', type=float, default=0, help='Seconds beteween each poll of the DSS for RID Subscriptions, 0 to disable DSS polling for RID Subscriptions')
    parser.add_argument('--scd-operation-poll-interval', type=float, default=0, help='Seconds between each poll of the DSS for Operations, 0 to disable DSS polling for Operations')
    parser.add_argument('--scd-constraint-poll-interval', type=float, default=0, help='Seconds between each poll of the DSS for Constraints, 0 to disable DSS polling for Constraints')
    parser.add_argument('--scd-subscription-poll-interval', type=float, default=0, help='Seconds beteween each poll of the DSS for SCD Subscriptions, 0 to disable DSS polling for SCD Subscriptions')

    return parser.parse_args()


def print_no_newline(s):
  sys.stdout.write(s)
  sys.stdout.flush()


def main() -> int:
    args = parseArgs()

    # Required resources
    adapter: auth.AuthAdapter = auth.make_auth_adapter(args.auth)
    dss_client = infrastructure.DSSTestSession(args.dss, adapter)
    area: s2sphere.LatLngRect = geo.make_latlng_rect(args.area)
    logger = tracerlog.Logger(args.output_folder)
    resources = polling.ResourceSet(dss_client, area, logger)

    config = vars(args)
    config['code_version'] = versioning.get_code_version()
    logger.logconfig(config)

    # Prepare pollers
    pollers: List[polling.Poller] = []

    if args.rid_isa_poll_interval > 0:
      pollers.append(polling.Poller(
        name='ridisa',
        object_diff_text=formatting.isa_diff_text,
        interval=datetime.timedelta(seconds=args.rid_isa_poll_interval),
        poll=lambda: polling.poll_rid_isas(resources)))

    if len(pollers) == 0:
      sys.stderr.write('Bad arguments: No data types had polling requests')
      return os.EX_USAGE

    # Execute the polling loop
    abort = False
    while not abort:
      try:
        most_urgent_dt = datetime.timedelta(days=999999999)
        most_urgent_poller = None
        for poller in pollers:
          dt = poller.time_to_next_poll()
          if dt < most_urgent_dt:
            most_urgent_poller = poller
            most_urgent_dt = dt

        if most_urgent_dt.total_seconds() > 0:
          time.sleep(most_urgent_dt.total_seconds())

        result = most_urgent_poller.poll()

        if result.has_different_content_than(most_urgent_poller.last_result):
          logger.log(result.initiated_at, most_urgent_poller.name, result.to_json())
          print(most_urgent_poller.diff_text(result))
          most_urgent_poller.last_result = result
        else:
          logger.log(result.initiated_at, most_urgent_poller.name, None)
          print_no_newline('.')
      except KeyboardInterrupt:
        abort = True

    return os.EX_OK

if __name__ == "__main__":
    sys.exit(main())
