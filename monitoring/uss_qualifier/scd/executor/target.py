import uuid
from datetime import datetime
from typing import Dict, Callable, Tuple, Optional
import requests

from monitoring.monitorlib import infrastructure, auth, fetch
from monitoring.monitorlib.clients.scd_automated_testing import create_flight, delete_flight
from monitoring.monitorlib.scd_automated_testing.scd_injection_api import InjectFlightResult, \
    DeleteFlightResult, InjectFlightResponse, DeleteFlightResponse
from monitoring.monitorlib.typing import ImplicitDict
from monitoring.uss_qualifier.rid.utils import InjectionTargetConfiguration
from monitoring.uss_qualifier.scd.data_interfaces import FlightInjectionAttempt, TestStep
from monitoring.uss_qualifier.scd.reports import Interaction, Report

class TestTarget():
    """A class managing the state and the interactions with a target"""

    def __init__(self, name: str, config: InjectionTargetConfiguration, auth_spec: str):
        self.name = name
        self.config = config
        self.client = infrastructure.DSSTestSession(
            self.config.injection_base_url,
            auth.make_auth_adapter(auth_spec))

        # Flights injected by this target.
        # Key: flight name
        # Value: flight id
        self.created_flight_ids: Dict[str, str] = {}


    def __repr__(self):
        return "TestTarget({}, {})".format(self.name, self.config.injection_base_url)

    def inject_flight(self, flight_request: FlightInjectionAttempt) -> Tuple[InjectFlightResponse, fetch.Query]:
        flight_id, resp, query = create_flight(self.client, self.config.injection_base_url, flight_request.test_injection)
        if resp.result == InjectFlightResult.Planned:
            self.created_flight_ids[flight_request.name] = flight_id
        return resp, query

    def delete_flight(self, flight_name: str) -> Tuple[DeleteFlightResponse, fetch.Query]:
        flight_id = self.created_flight_ids[flight_name]
        resp, query = delete_flight(self.client, self.config.injection_base_url, flight_id)
        if resp.result == DeleteFlightResult.Closed:
            del self.created_flight_ids[flight_name]
        return resp, query

    def delete_all_flights(self, capture_interaction: Optional[Callable[[fetch.Query], None]]) -> int:
        flights_count = len(self.created_flight_ids.keys())
        print("[SCD]    - Deleting {} flights for target {}.".format(flights_count, self.name))
        for flight_name, flight_id in list(self.created_flight_ids.items()):
            resp, query = self.delete_flight(flight_name)
            if capture_interaction:
                capture_interaction(query)
        return flights_count

    def is_managing_flight(self, flight_name: str) -> bool:
        return flight_name in self.created_flight_ids.keys()
