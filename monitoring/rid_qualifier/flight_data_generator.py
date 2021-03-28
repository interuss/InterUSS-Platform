from shapely.geometry import Point, Polygon
import shapely.geometry
from pyproj import Geod, Transformer
import json
from pathlib import Path
from typing import List, NamedTuple, Any
import arrow
import datetime
from datetime import datetime, timedelta
import uuid

class QueryBoundingBox(NamedTuple):
    ''' This is the object that stores details of query bounding box '''

    name: str
    shape: Polygon
    timestamp_before: timedelta
    timestamp_after: timedelta
    
class FlightPoint(NamedTuple):
    ''' This object holds basic information about a point on the flight track, it has latitude, longitude and altitude in WGS 1984 datum '''

    lat: float # Degrees of latitude north of the equator, with reference to the WGS84 ellipsoid. For more information see: https://github.com/uastech/standards/blob/master/remoteid/canonical.yaml#L1160
    lng: float # Degrees of longitude east of the Prime Meridian, with reference to the WGS84 ellipsoid. For more information see: https://github.com/uastech/standards/blob/master/remoteid/canonical.yaml#L1170
    alt: float

class AircraftPosition(NamedTuple):
    ''' A object to hold AircraftPosition details for Remote ID purposes. For more information see, the definition in the standard: https://github.com/uastech/standards/blob/36e7ea23a010ff91053f82ac4f6a9bfc698503f9/remoteid/canonical.yaml#L1091 '''

    lat : float 
    lng : float 
    alt : float
    accuracy_h : str
    accuracy_v : str
    extrapolated: bool
    pressure_altitude : float

class AircraftHeight(NamedTuple):
    ''' A object to hold relative altitude for the purposes of Remote ID. For more information see: https://github.com/uastech/standards/blob/36e7ea23a010ff91053f82ac4f6a9bfc698503f9/remoteid/canonical.yaml#L1142 '''

    distance: float
    reference: str

class AircraftState(NamedTuple):
    ''' A object to hold Aircraft state details for remote ID purposes. For more information see the published standard API specification at https://github.com/uastech/standards/blob/36e7ea23a010ff91053f82ac4f6a9bfc698503f9/remoteid/canonical.yaml#L1604 '''

    reference_time : datetime # This a additional field in the object that is not contained in the standard and is used for simulations. This is normally the time when the simulation started and time delta should be used against this value
    timestamp: datetime # A date time object at which this state is valid. This is generated by the simulator and can be used to test out different flight test scenarios. 
    operational_status: str # Operational status of the aircraft, we only use Airborne for the purpose of the simulation. For more information about this: https://github.com/uastech/standards/blob/36e7ea23a010ff91053f82ac4f6a9bfc698503f9/remoteid/canonical.yaml#L1393
    position: AircraftPosition # See the definition above 
    height: AircraftHeight # See the definition above 
    track: float # A object to hold the direction of flight https://github.com/uastech/standards/blob/36e7ea23a010ff91053f82ac4f6a9bfc698503f9/remoteid/canonical.yaml#L1641
    speed: float # Ground speed of flight in meters / second , please see: https://github.com/uastech/standards/blob/36e7ea23a010ff91053f82ac4f6a9bfc698503f9/remoteid/canonical.yaml#L1651 
    speed_accuracy: str # Accuracy of Ground speed, for the purposes of the simulation only SA3mps is used. For other vlues see: https://github.com/uastech/standards/blob/36e7ea23a010ff91053f82ac4f6a9bfc698503f9/remoteid/canonical.yaml#L1651
    vertical_speed: float # Speed up in WGS84-HAE , see https://github.com/uastech/standards/blob/36e7ea23a010ff91053f82ac4f6a9bfc698503f9/remoteid/canonical.yaml#L1662
    group_count: int # When operating in group, the number of aircraft https://github.com/uastech/standards/blob/36e7ea23a010ff91053f82ac4f6a9bfc698503f9/remoteid/canonical.yaml#L1691
    group_radius: float # Farthest horizontal distance from reported location, for more informatoin see ;https://github.com/uastech/standards/blob/36e7ea23a010ff91053f82ac4f6a9bfc698503f9/remoteid/canonical.yaml#L1669
    group_ceiling: float # Maximum altitude (meters in WGS 1984) For more information see: https://github.com/uastech/standards/blob/36e7ea23a010ff91053f82ac4f6a9bfc698503f9/remoteid/canonical.yaml#L1678 
    group_floor: float # Minimum altitude of group operation https://github.com/uastech/standards/blob/36e7ea23a010ff91053f82ac4f6a9bfc698503f9/remoteid/canonical.yaml#L1684
    group_time_start : datetime # Time at which Group operations start, for the sake of simulation, we just use the start time, this field is not used but populated to ensure consistency with RIDAircraft State object https://github.com/uastech/standards/blob/36e7ea23a010ff91053f82ac4f6a9bfc698503f9/remoteid/canonical.yaml#L1684
    group_time_end: datetime


class RIDFlight(NamedTuple):
    ''' A object to store details of a remoteID flight ''' 
    id: str # ID of the flight for Remote ID purposes, e.g. uss1.JA6kHYCcByQ-6AfU, we for this simulation we use just numeric : https://github.com/uastech/standards/blob/36e7ea23a010ff91053f82ac4f6a9bfc698503f9/remoteid/canonical.yaml#L943
    aircraft_type: str  # Generic type of aircraft https://github.com/uastech/standards/blob/36e7ea23a010ff91053f82ac4f6a9bfc698503f9/remoteid/canonical.yaml#L1711
    current_state: AircraftState # See above for definition


class GridCellFlight(NamedTuple):
    ''' A object to hold details of a grid location and the track within it '''
    bounds: shapely.geometry.polygon.Polygon
    track: List[FlightPoint]

class AdjacentCircularFlightsSimulator():

    ''' A class to generate Flight Paths given a bounding box, this is the main module to generate flight path datasets, the data is generated as latitude / longitude pairs with assoiated with the flights. Additional flight metadata e.g. flight id, altitude, registration number can also be generated '''

    def __init__(self, minx: float, miny: float, maxx: float, maxy: float) -> None: 

        """ Create an AdjacentCircularFlightsSimulator with the specified bounding box.

            Once these extents are specified, a grid will be created with two rows.  The idea is that multiple flights tracks will be created within the extents.
            Args:
            minx: Western edge of bounding box (degrees longitude)
            maxx: Eastern edge of bounding box (degrees longitude)
            miny: Southern edge of bounding box (degrees latitude)
            maxy: Northern edge of bounding box (degrees latitude)

            Raises:
            ValueError: If bounding box has more area than a 500m x 500m square.
        """

        self.minx = minx 
        self.miny = miny
        self.maxx = maxx
        self.maxy = maxy   
        
        self.grid_cells_flight_tracks: List[GridCellFlight] = []

        
        self.query_bboxes: List[QueryBoundingBox] = [] # This object holds the name and the polygon object of the query boxes. The number of bboxes are controlled by the `box_diagonals` variable

        self.flight_telemetry: List[List[RIDAircraftState]] = []
        
        self.input_extents_valid()
        

    def input_extents_valid(self) -> None:

        ''' This method checks if the input extents are valid i.e. small enough, if the extent is too large, we reject them, at the moment it checks for extents less than 500m x 500m square but can be changed as necessary.''' 

        box = shapely.geometry.box(self.minx, self.miny, self.maxx, self.maxy)
        geod = Geod(ellps="WGS84")
        area = abs(geod.geometry_area_perimeter(box)[0])
        
        if (area) < 250000 and (area) > 90000: # Have a area less than 500m x 500m square and more than 300m x 300m square to ensure a 70 m diameter tracks
            return
        else: 
            raise ValueError("The extents provided are too large, please provide extents that are less than 500m x 500m and more than 300m x 300m square")
        
    def generate_query_bboxes(self):

        ''' For the differnet Remote ID checks: No, we need to generate three bounding boxes for the display provider, this method generates the 1 km diagonal length bounding box '''
        # Get center of of the bounding box that is inputted into the generator
        box = shapely.geometry.box(self.minx, self.miny, self.maxx, self.maxy)
        center = box.centroid
        # Transform to geographic co-ordinates to get areas
        transformer = Transformer.from_crs("epsg:4326", "epsg:3857")
        transformed_x,transformed_y = transformer.transform(center.x, center.y)
        pt = Point(transformed_x,transformed_y)
        # Now we have a point, we can buffer the point and create bounding boxes of the buffer to get the appropriate polygons, more than three boxes can be created, for the tests three will suffice.
        now = datetime.now()
        
        box_diagonals = [
            {'length':150, 'name':'zoomed_in_detail', 'timestamp_after':now + timedelta(seconds=60),'timestamp_before':now + timedelta(seconds=90)},
            {'length':380, 'name':"whole_flight_area",'timestamp_after':now + timedelta(seconds=30),'timestamp_before':now + timedelta(seconds=60)},
            {'length':3000, 'name':'too_large_query','timestamp_after':now + timedelta(seconds=10),'timestamp_before':now + timedelta(seconds=30)}
            ]

        for box_id, box_diagonal in enumerate(box_diagonals):
            # Buffer the point with the appropriate length
            buffer = pt.buffer(box_diagonal['length'])                   
            buffer_bounds = buffer.bounds
            buffer_bounds_polygon  =  shapely.geometry.box(buffer_bounds[0], buffer_bounds[1], buffer_bounds[2], buffer_bounds[3])
            buffer_points =  zip(buffer_bounds_polygon.exterior.coords.xy[0], buffer_bounds_polygon.exterior.coords.xy[1])
            proj_buffer_points = []
            # reproject back to ESPG 4326
            transformer2 = Transformer.from_crs("epsg:3857", "epsg:4326")
            for point in buffer_points:
                x = point[0]
                y = point[1]
                x, y = transformer2.transform(x, y)
                proj_buffer_points.append((x, y))
            
            buffered_box = Polygon(proj_buffer_points)
            # Get the bounds of the buffered box, this is the one that will will be fed to the remote ID display provider to query            
            self.query_bboxes.append(QueryBoundingBox(name=box_diagonals[box_id]['name'], shape=buffered_box, timestamp_after = box_diagonals[box_id]['timestamp_after'], timestamp_before = box_diagonals[box_id]['timestamp_before']))
            

    
    def generate_flight_grid_and_path_points(self):

        ''' Generate a series of boxes (grid) within the given bounding box to have areas for different flight tracks within each box '''
        # Compute the box where the flights will be created. For a the sample bounds given, over Bern, Switzerland, a division by 2 produces a cell_size of 0.0025212764739985793, a division of 3 is 0.0016808509826657196 and division by 4 0.0012606382369992897. As the cell size goes smaller more number of flights can be accomodated within the grid. For the study area bounds we build a 3x2 box for six flights by creating 3 column 2 row grid. 
        N_COLS = 3
        N_ROWS = 2
        cell_size_x = (self.maxx - self.minx)/(N_COLS) # create three columns
        cell_size_y = (self.maxy - self.miny)/(N_ROWS) # create two rows
        grid_cells = [] 
        for u0 in range(0, N_COLS):  # 3 columns           
            x0 =  self.minx + (u0 * cell_size_x)            
            for v0 in range(0,N_ROWS): # 2 rows
                y0 = self.miny + (v0 *cell_size_y)
                x1 = x0 + cell_size_x
                y1 = y0 + cell_size_y
                grid_cells.append(shapely.geometry.box(x0, y0, x1, y1))                
                           

        all_grid_cell_tracks =[]
        flight_points  = []
        ''' For each of the boxes (grid) allocated to the operator, get the centroid and buffer to generate a flight path. A 70 m radius is provided to have flight paths within each of the boxes '''

        # Iterate over the flight_grid
        for grid_cell in grid_cells:
            center = grid_cell.centroid
            ## Transfrom to buffer 140 m diameter circle on which the drone will fly            
            transformer = Transformer.from_crs("epsg:4326", "epsg:3857")
            transformed_x,transformed_y = transformer.transform(center.x, center.y)
            pt = Point(transformed_x,transformed_y)
            buffer = pt.buffer(70) # build a buffer so that the radius is 70m for the track
            buffer_points =  zip(buffer.exterior.coords.xy[0], buffer.exterior.coords.xy[1])
            proj_buffer_points = []
            # reproject back to ESPG 4326
            transformer2 = Transformer.from_crs("epsg:3857", "epsg:4326")
            for point in buffer_points:
                x = point[0]
                y = point[1]
                x, y = transformer2.transform(x, y)
                proj_buffer_points.append((x, y))
            buffered_path = Polygon(proj_buffer_points)
            altitude_agl = 50.0
            altitude_of_ground_level_wgs_84 = 48.73 #  height of the geoid above the WGS84 ellipsoid (using EGM 96) for Bern, rom https://geographiclib.sourceforge.io/cgi-bin/GeoidEval?input=46%B056%26%238242%3B53%26%238243%3BN+7%B026%26%238242%3B51%26%238243%3BE&option=Submit 
            altitude = altitude_of_ground_level_wgs_84 + altitude_agl # meters WGS 84
            flight_points_with_altitude = []
            x, y = buffered_path.exterior.coords.xy
            for coord in range(0,len(x)):
                flight_points_with_altitude.append(FlightPoint(lat = x[coord],lng = y[coord],alt= altitude))
            
            # Build a list of points so that they can be fed to the sim and outputted.             
            flight_points.append(flight_points_with_altitude)
            all_grid_cell_tracks.append(GridCellFlight(bounds = grid_cell, track = flight_points_with_altitude))

        self.grid_cells_flight_tracks = all_grid_cell_tracks

    def make_json_compatible(self, struct: Any) -> Any:
        if isinstance(struct, tuple) and hasattr(struct, '_asdict'):
            return {k: self.make_json_compatible(v) for k, v in struct._asdict().items()}
        elif isinstance(struct, dict):
            return {k: self.make_json_compatible(v) for k, v in struct.items()}
        elif isinstance(struct, str):
            return struct
        try:
            return [self.make_json_compatible(v) for v in struct]
        except TypeError:
            return struct

    def generate_rid_state(self, duration = 180):
        '''
        
        flight_points: A list of flight points each in FlightPoint format, generated from generate_flight_paths_points method in the AdjacentCircularFlightsSimulator method. This method generates a RIDState object from flight tracks and adds time stamp and other information


        '''
        all_flight_telemetry = {}
        flight_lenghts = {} # Develop a index of flight length and their index
        flight_current_index = {} # Store where on the track the current index is, since the tracks are circular, once the end of the track is reached, the index is reset to 0 to indicate beginning of the track again. 
        num_flights = len(self.grid_cells_flight_tracks) # Get the number of flights 
        now = arrow.now() 
        now_isoformat = now.isoformat()
        for i in range(num_flights):
            flight_lenghts[i]= len(self.grid_cells_flight_tracks[i].track)
            flight_current_index[i] = 0
            all_flight_telemetry[i] = []
        
        for j in range(duration):
            if j == 0:
                timestamp = now.shift(seconds = 1)
            else:
                timestamp = timestamp.shift(seconds = 1)
            timestamp_isoformat = timestamp.isoformat()
            seconds_diff = (now - timestamp).total_seconds()
            
            for k in range(num_flights):
                list_end = flight_lenghts[k] - flight_current_index[k]            
                if list_end != 1:             
                    flight_point = self.grid_cells_flight_tracks[k].track[flight_current_index[k]]
                    aircraft_position = AircraftPosition(lat = flight_point.lat, 
                                                         lng = flight_point.lng, 
                                                         alt = flight_point.alt, 
                                                         accuracy_h= "HAUnkown", 
                                                         accuracy_v = "VAUnknown", 
                                                         extrapolated = 0, 
                                                         pressure_altitude = 0)
                    aircraft_height = AircraftHeight(distance =70, reference="TakeoffLocation")
                    rid_aircraft_state = AircraftState(
                        reference_time = now_isoformat, 
                        timestamp= timestamp_isoformat,
                        operational_status="Airborne", 
                        position=aircraft_position, 
                        height= aircraft_height,
                        track=45.0,
                        speed=1.9, 
                        speed_accuracy="SA3mps",
                        vertical_speed= 0.0,
                        group_radius=20.0, 
                        group_ceiling= 80.0, 
                        group_floor= 10.0, 
                        group_count= 1, 
                        group_time_start= now_isoformat, 
                        group_time_end= now_isoformat)

                    rid_aircraft_flight = RIDFlight(id=k, aircraft_type = "Other", current_state = rid_aircraft_state)


                    rid_aircraft_state_deserialized = self.make_json_compatible(rid_aircraft_flight)
                    all_flight_telemetry[k].append(rid_aircraft_state_deserialized)
                    flight_current_index[k]+= 1
                else:
                    flight_current_index[k] = 0
                
        telemetry_data = all_flight_telemetry.values()
        telemetery_data_list = list(telemetry_data)
        self.flight_telemetry = telemetery_data_list

 



class TrackWriter():

    """
        Write the tracks created by AdjacentCircularFlightsSimulator into disk (in the outputs directory) as GeoJSON FeatureCollection 
        Args:
        flight_path_points: A set of flight path points generated by generate_flight_paths_points method in the AdjacentCircularFlightsSimulator class
        bboxes: A set of bounding boxes generated by generate_query_bboxes method in the AdjacentCircularFlightsSimulator class
        country_code: An ISO 3166-1 alpha-3 code for a country

        Outputs: 
        GeoJSON files for bboxes created in the `test_definitions/{country_code}` folder 
        
        
    """

    def __init__(self, grid_tracks: List[GridCellFlight], bboxes: List[QueryBoundingBox], country_code='CHE') -> None:
        ''' This class uses the same output directory as the AdjacentCircularFlightsSimulator class and requires the path points (Tracks) and the bounding boxes from that class.

        '''
        
        self.grid_cells_flight_tracks = grid_tracks
        self.bboxes = bboxes
        self.country_code = country_code        
        self.output_directory = Path('test_definitions', self.country_code)
        self.output_directory.mkdir(parents=True, exist_ok=True) # Create test_definition directory if it does not exist

    def write_bboxes(self):

        ''' This module writes the bboxes as a GeoJSON FeatureCollection '''
        for buffered_bbox_details in self.bboxes:
            
            features = json.dumps({'type': 'Feature', 'properties': {"timestamp_before":buffered_bbox_details.timestamp_before.isoformat(), "timestamp_after":buffered_bbox_details.timestamp_after.isoformat()}, 'geometry': shapely.geometry.mapping(buffered_bbox_details.shape)})
            bbox_file_name = 'box_%s.geojson'% buffered_bbox_details.name
            bbox_output_path = self.output_directory / bbox_file_name

            with open(bbox_output_path,'w') as f:
                f.write(features)
                
    def write_tracks(self):

        ''' This module writes tracks as a GeoJSON FeatureCollection (of Point Feature) for use in other software '''       
        
        flight_point_current_index = {}
        num_flights = len(self.grid_cells_flight_tracks)
        for i in range(num_flights):
            flight_point_current_index[i] = 0
            
        for track_id, grid_cell_flight_track in enumerate(self.grid_cells_flight_tracks):
            feature_collection = {"type":"FeatureCollection", "features": []}
            for cur_track_point in grid_cell_flight_track.track:                
                p = Point((cur_track_point.lat, cur_track_point.lng, cur_track_point.alt))
                point_feature = {'type': 'Feature', 'properties': {}, 'geometry': shapely.geometry.mapping(p)}                
                feature_collection['features'].append(point_feature)

            path_file_name = 'track_%s.geojson'% str(track_id+1)
            tracks_file_path = self.output_directory / path_file_name
            with open(tracks_file_path,'w') as f:
                f.write(json.dumps(feature_collection))

class RIDAircraftStateWriter():

    """Write tracks in RIDAircraftState object to disk (refer. https://github.com/uastech/standards/blob/36e7ea23a010ff91053f82ac4f6a9bfc698503f9/remoteid/canonical.yaml#L1604)

       
    """

    def __init__(self, flight_telemetry, country_code='che') -> None:

        """ Atleast single flight points array is necessary and a ouptut directory  
        Args:
        flight_telemetry: 
        country_code: An ISO 3166-1 alpha-3 code for a country, this is used to create a sub-directory to store output.
        
        Outputs: 
        A JSON datastructure as a file that can be submitted as a part of the test harness to a USS that implements the automatic remote id testing interface. 
        
        """

        self.flight_telemetry = flight_telemetry
        self.country_code = country_code
        self.flight_telemetry_check()

        self.output_directory = Path('test_definitions', self.country_code)
        self.output_directory.mkdir(parents=True, exist_ok=True) # Create test_definition directory if it does not exist

    def flight_telemetry_check(self) -> None:

        ''' Check if atleast one track is provided, if no tracks are provided, then RIDAircraftState and Test JSON cannot be generated.''' 

        if (self.flight_telemetry): # Empty flight points cannot be converted to a Aircraft State, check if the list has 
            return
        else:
            raise ValueError("At least one flight track is necessary to create a AircraftState and a test JSON, please generate the tracks first using AdjacentCircularFlightsSimulator class")

    def write_rid_state(self, duration = 180):

        ''' This method iterates over flight tracks and geneates AircraftState JSON objects and writes to disk in the test_definitions folder, these files can be used to submit the data in the test harness '''
        

        for flight_id, single_flight_telemetry_data in enumerate(self.flight_telemetry):
            
            
            rid_test_file_name = 'flight_' + str(flight_id) + '_rid_aircraft_state' + '.json'
            rid_test_file_path = self.output_directory / rid_test_file_name
            
            with open(rid_test_file_path,'w') as f:
                f.write(json.dumps(single_flight_telemetry_data))


        
if __name__ == '__main__':
    #TODO: accept these parameters as values so that other locations can be supplied
    my_path_generator = AdjacentCircularFlightsSimulator(minx = 7.4735784530639648, miny = 46.9746744128218410, maxx = 7.4786210060119620, maxy= 46.9776318195799121)
    COUNTRY_CODE = 'che'
    flight_points = []
    query_bboxes = []


    my_path_generator.generate_flight_grid_and_path_points()
    my_path_generator.generate_query_bboxes()

    grid_tracks = my_path_generator.grid_cells_flight_tracks    
    
    my_path_generator.generate_rid_state(duration =180)   
    flight_telemetry = my_path_generator.flight_telemetry

    query_bboxes = my_path_generator.query_bboxes
  
    my_track_writer = TrackWriter(grid_tracks = grid_tracks,bboxes=query_bboxes, country_code = COUNTRY_CODE)
    my_track_writer.write_bboxes()
    my_track_writer.write_tracks()
    
    my_state_generator = RIDAircraftStateWriter(flight_telemetry = flight_telemetry, country_code= COUNTRY_CODE)
    my_state_generator.write_rid_state()
