from datetime import datetime
from typing import Dict, List, Optional, Tuple


TIME_FORMAT_CODE = 'RFC3339'

DATE_FORMAT = '%Y-%m-%dT%H:%M:%S.%fZ'



def make_vol4(
  t0: Optional[datetime] = None,
  t1: Optional[datetime] = None,
  alt0: Optional[float] = None,
  alt1: Optional[float] = None,
  circle: Dict = None,
  polygon: Dict = None) -> Dict:
  vol3 = dict()
  if circle is not None:
    vol3['outline_circle'] = circle
  if polygon is not None:
    vol3['outline_polygon'] = polygon
  if alt0 is not None:
    vol3['altitude_lower'] = make_altitude(alt0)
  if alt1 is not None:
    vol3['altitude_upper'] = make_altitude(alt1)
  vol4 = {'volume': vol3}
  if t0 is not None:
    vol4['time_start'] = make_time(t0)
  if t1 is not None:
    vol4['time_end'] = make_time(t1)
  return vol4


def make_time(t: datetime) -> Dict:
  return {
    'value': t.isoformat() + 'Z',
    'format': 'RFC3339'
  }


def make_altitude(alt: float) -> Dict:
  return {
    'value': alt,
    'reference': 'W84',
    'units': 'M'
  }


def make_circle(lat: float, lng: float, radius: float) -> Dict:
  return {
    "type": "Feature",
    "geometry": {
      "type": "Point",
      "coordinates": [lng, lat]
    },
    "properties": {
      "radius": {
        "value": radius,
        "units": "M"
      }
    }
  }


def make_polygon(coords: List[Tuple[float, float]]) -> Dict:
  full_coords = coords.copy()
  full_coords.append(coords[0])
  return {
    "type": "Polygon",
    "coordinates": [ [[lng, lat] for (lat, lng) in full_coords] ]
  }
