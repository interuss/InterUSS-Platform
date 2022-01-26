from monitoring.monitorlib.scd_automated_testing.scd_injection_api import OperationalIntentTestInjection,FlightAuthorisationData, InjectFlightRequest
from monitoring.uss_qualifier.scd.data_interfaces import FlightInjectionAttempt, InjectionTarget, KnownIssueFields, KnownResponses, AutomatedTest
from utils import GeneratedGeometry, GeometryGenerationRule, OutputSubDirectories
from shapely.geometry import asShape
from shapely.geometry import LineString
from monitoring.monitorlib.scd import Time, Volume3D, Volume4D, Polygon, Altitude, LatLngPoint
from typing import List
from pathlib import Path
import geojson
from itertools import cycle
import string
import json
from pyproj import Geod, Proj
import arrow
import random
from typing import List, Union
import shapely.geometry
import os

class ProximateOperationalIntentGenerator():
    ''' A class to generate operational intents. As a input the module takes in a bounding box for which to generate the volumes within. '''

    def __init__(self, minx: float, miny: float, maxx: float, maxy: float, utm_zone:str) -> None:
        ''' Create a ProximateVolumeGenerator within a given geographic bounding box. 

        Once these extents are specified, a grid will be created with two rows. A combination of LineStrings and Polygons will be generated withing these bounds. While linestrings can extend to the full boundaries of the box, polygon areas are generated within the grid. 

        Args:
        minx: Western edge of bounding box (degrees longitude)
        maxx: Eastern edge of bounding box (degrees longitude)
        miny: Southern edge of bounding box (degrees latitude)
        maxy: Northern edge of bounding box (degrees latitude)
        utm_zone: UTM Zone string for the location, see https://en.wikipedia.org/wiki/Universal_Transverse_Mercator_coordinate_system to identify the zone for the location.


        Raises:
        ValueError : If the bounding box is more than 500m x 500m square
        
        
        '''
        self.minx = minx
        self.miny = miny
        self.maxx = maxx
        self.maxy = maxy
        self.utm_zone = utm_zone

        self.altitude_agl:float = 50.0
        self.altitude_envelope: int = 15 # the buffer in meters for flight when a path is converted into a volume
        self.first_flight_geometry: Union[LineString, Polygon] # the initial flight path or geometry against which subsequent flight paths are generated, this flag
        
        self.raw_geometries: List[GeneratedGeometry] # Object to hold polyons or linestrings, and the rule that generated the geometry (e.g. should this geometry intersect with the control)
        self.now = arrow.now()        
        self.geod = Geod(ellps='WGS84')
        self.grid_cells : List[shapely.geometry.box] # When a bounding box is given, it is split into smaller boxes this object holds the grids
        self._input_extents_valid()
        self._generate_grid_cells()
        
    def _generate_grid_cells(self):
        # Compute the box where the flights will be created. For a the sample bounds given, over Bern, Switzerland, a division by 2 produces a cell_size of 0.0025212764739985793, a division of 3 is 0.0016808509826657196 and division by 4 0.0012606382369992897. As the cell size goes smaller more number of flights can be accomodated within the grid. For the study area bounds we build a 3x2 box for six flights by creating 3 column 2 row grid.
        N_COLS = 3
        N_ROWS = 2
        cell_size_x = (self.maxx - self.minx)/(N_COLS)  # create three columns
        cell_size_y = (self.maxy - self.miny)/(N_ROWS)  # create two rows
        grid_cells = []
        for u0 in range(0, N_COLS):  # 3 columns
            x0 = self.minx + (u0 * cell_size_x)
            for v0 in range(0, N_ROWS):  # 2 rows
                y0 = self.miny + (v0 * cell_size_y)
                x1 = x0 + cell_size_x
                y1 = y0 + cell_size_y
                grid_cells.append(shapely.geometry.box(x0, y0, x1, y1))
        self.grid_cells = grid_cells

    def utm_converter(self, shapely_shape: shapely.geometry, inverse:bool=False) -> shapely.geometry.shape:
        ''' A helper function to convert from lat / lon to UTM coordinates for buffering. tracks. This is the UTM projection (https://en.wikipedia.org/wiki/Universal_Transverse_Mercator_coordinate_system), we use Zone 33T which encompasses Switzerland, this zone has to be set for each locale / city. Adapted from https://gis.stackexchange.com/questions/325926/buffering-geometry-with-points-in-wgs84-using-shapely '''

        proj = Proj(proj='utm', zone=self.utm_zone, ellps='WGS84', datum='WGS84')

        geo_interface = shapely_shape.__geo_interface__
        feature_type = geo_interface['type']
        coordinates = geo_interface['coordinates']
        if feature_type == 'Polygon':
            new_coordinates = [[proj(*point, inverse=inverse) for point in linring] for linring in coordinates]
        elif feature_type == 'LineString':
            new_coordinates = [proj(*point, inverse=inverse) for point in coordinates]
        else:
            raise RuntimeError('Unexpected geo_interface type: {}'.format(feature_type))

        return shapely.geometry.shape({'type': feature_type, 'coordinates': tuple(new_coordinates)})

    def _input_extents_valid(self) -> None:
        ''' This method checks if the input extents are valid i.e. small enough, if the extent is too large, we reject them, at the moment it checks for extents less than 500m x 500m square but can be changed as necessary.'''

        box = shapely.geometry.box(self.minx, self.miny, self.maxx, self.maxy)
        area = abs(self.geod.geometry_area_perimeter(box)[0])

        # Have a area less than 500m x 500m square and more than 300m x 300m square to ensure enough space for tracks
        if (area) < 250000 and (area) > 90000:
            return
        else:
            raise ValueError('The extents provided are not of the correct size, please provide extents that are less than 500m x 500m and more than 300m x 300m square')
        
    def _generate_random_flight_path(self) -> LineString:
        '''Generate a random flight path. this code uses the `generate_random` method (https://github.com/jazzband/geojson/blob/master/geojson/utils.py#L131) to generate the initial linestring.  '''
        
        random_flight_path = geojson.utils.generate_random(featureType = 'LineString', numberVertices=2, boundingBox=[self.minx, self.miny, self.maxx, self.maxy])

        return random_flight_path
               
    def _generate_random_flight_polygon(self) -> Polygon:
        '''Generate a random polygon, if a polygon is specified then this method picks one of the grid cells to generate the flight path within that, this is to ensure that a polygon geometry does not take over the entire bounding box. '''        
        
        grid_cell = random.choice(self.grid_cells) # Pick a random grid cell
        random_flight_polygon = geojson.utils.generate_random(featureType = 'LineString', numberVertices=2, boundingBox=grid_cell.bounds)
        random_flight_polygon = asShape(random_flight_polygon).envelope # Get the envelope of the linestring and create a box
        return random_flight_polygon
        
    def _generate_single_flight_geometry(self, geometry_generation_rule:GeometryGenerationRule, injection_number:int) -> Union[LineString, Polygon]:
        ''' A method to generates flight geometry within a geographic bounds. The geometry can be a linestring or a polygon, simple rules for generation can be specificed. At the moment the method check if the geometry should intersect with the control and based on that, linestring / polygons are created '''
        
        coin_flip = random.choice([0,0,1])         
        if coin_flip:
            flight_geometry = self._generate_random_flight_polygon()
        else:
            flight_geometry = self._generate_random_flight_path()

        if injection_number == 0:
            self.first_flight_geometry = asShape(flight_geometry)

        if geometry_generation_rule.intersect_space: # This is not the first geometry, check if it should intersect with the control
            geometry_intersects = False
            while (geometry_intersects == False):
                coin_flip = random.choice([0,0,1]) 
                # We are trying to generate a path that intersects with the control, we keep generating linestrings or polygons till one is found that does intersect
                if coin_flip:
                    flight_geometry = self._generate_random_flight_polygon()
                else:
                    flight_geometry = self._generate_random_flight_path()
                    
                raw_geom = asShape(flight_geometry) # Generate a shape from the geometry
                
                geometry_intersects = self.first_flight_geometry.intersects(raw_geom) # Check this intersects with the control     
            
        return flight_geometry

    def convert_geometry_to_volume(self, flight_geometry:LineString, altitude_of_ground_level_wgs_84:int) -> Volume3D:
        ''' A method to convert a GeoJSON LineString or Polygon to a ASTM outline_polygon object by buffering 15m spatially '''
        
        flight_geometry_shp = asShape(flight_geometry)
        flight_geometry_utm = self.utm_converter(flight_geometry_shp)
        buffer_shape_utm = flight_geometry_utm.buffer(15)        

        alt_upper = altitude_of_ground_level_wgs_84 + self.altitude_agl +self.altitude_envelope  
        alt_lower = altitude_of_ground_level_wgs_84 + self.altitude_agl - self.altitude_envelope

        buffered_shape_geo = self.utm_converter(buffer_shape_utm, inverse=True)
        
        all_vertices = []

        altitude_upper = Altitude(value= alt_upper, reference = 'W84', units='M')
        altitude_lower = Altitude(value=alt_lower, reference = 'W84', units='M')
        for vertex in list(buffered_shape_geo.exterior.coords):
            coord = LatLngPoint(lat = vertex[0] , lng = vertex[1])
            all_vertices.append(coord)
        
        p = Polygon(vertices=all_vertices)
        
        volume3D = Volume3D(outline_polygon = p, altitude_lower = altitude_lower, altitude_upper = altitude_upper, outline_circle = {})
        
        return volume3D

    def transform_3d_volume_to_astm_4d(self, volume_3d : Volume3D) -> Volume4D:
        ''' This method converts a 3D Volume to 4D Volume, the flight start time is 3 mins from now  '''
    
        three_mins_from_now = self.now.shift(minutes = 3)
        eight_mins_from_now = self.now.shift(minutes = 8)
        start_time = Time(value = three_mins_from_now.isoformat(), format = 'RFC3339')
        end_time = Time(value = eight_mins_from_now.isoformat(), format = 'RFC3339')    
        volume_4D = Volume4D(volume=volume_3d, time_start= start_time, time_end=end_time)
        
        return volume_4D
    
    def generate_nominal_test_geometry(self, geometry_generation_rule: GeometryGenerationRule, injection_number: int) -> GeneratedGeometry:
        ''' A method to generate two Volume 4D payloads to submit to the system to be tested.  '''                
        
        flight_path_geometry = self._generate_single_flight_geometry(geometry_generation_rule = geometry_generation_rule, injection_number= injection_number)

        raw_geometry = GeneratedGeometry(geometry = flight_path_geometry, geometry_generation_rule = geometry_generation_rule)
        
        return raw_geometry


    def generate_astm_4d_volumes(self,raw_geometry:GeneratedGeometry, altitude_of_ground_level_wgs_84 :int) -> Volume4D:
        ''' A method to generate ASTM specified Volume 4D payloads to submit to the system to be tested.  '''
        
        flight_volume_3d = self.convert_geometry_to_volume(flight_geometry = raw_geometry.geometry, altitude_of_ground_level_wgs_84 = altitude_of_ground_level_wgs_84)
        flight_volume_4d = self.transform_3d_volume_to_astm_4d(volume_3d = flight_volume_3d)
        
        return flight_volume_4d
    
    def generate_injection_operational_intents(self, astm_4d_volume:Volume4D) -> OperationalIntentTestInjection:
        ''' A method to generate Operational Intent references given a list of Volume 4Ds '''

        
        current_operational_intent_reference = OperationalIntentTestInjection(volumes = [astm_4d_volume], key = [], state = 'Accepted', off_nominal_volumes = [], priority =0)            
        return current_operational_intent_reference

class SerialNumberGenerator():
    ''' A class to generate a UAS Serial number as is expressed in the ANSI/CTA-2063-A Physical Serial Number format. Required by ANNEX IV of COMMISSION IMPLEMENTING REGULATION (EU) 2021/664, paragraph 1. Reference: https://eur-lex.europa.eu/legal-content/EN/TXT/HTML/?uri=CELEX:32021R0664&from=EN#d1e32-178-1 
    ''' 

    def __init__(self):

        self.serial_number_length_code_points = {'1':1,'2':2,'3':3,'4':4,'5':5,'6':6,'7':7,'8':8,'9':9,'A':10,'B':11,'C':12,'D':13,'E':14,'F':15}
        self.serial_number_code_points = '0123456789ABCDEFGHJKLMNPQRSTUVWXYZ'


    def generate_incorrect_serial_number(self, valid_serial_number:str) ->str:
        ''' 
        A method to modify a valid UAV serial number to one that does not conform to the standard / is invalid.         
        '''
        _serial_number_length_code_points = self.serial_number_length_code_points # make a copy of the the code points
        manufacturer_code = valid_serial_number[0:4] # take out the manufacturer serial code out of the valid one
        length_code = valid_serial_number[4:5] # take out the length code out of the valid serial number         
        _serial_number_length_code_points.pop(length_code, None) # take out the length code so that we dont pick that one again (and make the serial number valid)
        dict_key, new_length_code = random.choice(list(_serial_number_length_code_points.items())) # pick a new length code
        random_serial_number = ''.join(random.choices(self.serial_number_code_points, k = new_length_code)) # generate anew 

        incorrect_serial_number =  manufacturer_code + length_code + random_serial_number

        return incorrect_serial_number

    def generate_serial_number(self) -> str:
        ''' 
        A method to generate a valid and random UAV serial number per the standard        
        '''
        
        random.shuffle(self.serial_number_code_points.split())
        manufacturer_code = ''.join(self.serial_number_code_points[:4])
        dict_key, length_code = random.choice(list(self.serial_number_length_code_points.items()))
        random_serial_number = ''.join(random.choices(self.serial_number_code_points, k=length_code))
        serial_number = manufacturer_code + dict_key + random_serial_number
        return serial_number


class OperatorRegistrationDataGenerator():
    ''' A class to generate data for operator registration per EN4709-02 standard. 
    ''' 

    def __init__(self):        
        
        self.registration_number_code_points = '0123456789abcdefghijklmnopqrstuvwxyz'

    def generate_incorrect_operator_registration_number(self, valid_operator_id:str) -> str:
        ''' Take a valid Operator Registration number per the standard and modify it to make it incorrect / invalid '''

        new_registration_number = valid_operator_id.split('-')[0]
        final_random_string = ''.join(random.choice(string.ascii_lowercase) for _ in range(3))
        new_registration_number = new_registration_number +'-'+ final_random_string
        return new_registration_number

    def generate_operator_registration_number(self, prefix='CHE') -> str:
        ''' A method to generate the Operator Registration number '''
        def gen_checksum(raw_id):
            assert raw_id.isalnum()
            assert len(raw_id) == 15
            
            d = {v: k for k, v in enumerate(list(self.registration_number_code_points))}
            numeric_base_id = list(map(d.__getitem__, list(raw_id)))
            # Multiplication factors for each digit depending on its position
            mult_factors = cycle([2, 1])
            def partial_sum(number, mult_factor):
                '''Calculate partial sum ofr a single digit.'''
                quotient, remainder = divmod(number * mult_factor, 36)
                return quotient + remainder
            final_sum = sum(                
                partial_sum(int(character), mult_factor)
                for character, mult_factor in zip(numeric_base_id, mult_factors))

            # Calculate control number based on partial sums
            control_number = -final_sum % 36
            
            return list(self.registration_number_code_points)[control_number]

        final_random_string = ''.join(random.choice(string.ascii_lowercase) for _ in range(3))
        base_id = ''.join(random.choice(string.ascii_lowercase + string.digits) for _ in range(12))
        checksum = gen_checksum(base_id + final_random_string)
        reg_num = prefix + base_id + str(checksum) +'-'+ final_random_string
        return reg_num        


def generate_flight_injection_attempts() -> List[FlightInjectionAttempt]:
    flight_injection_attempts = []

    my_operational_intent_generator = ProximateOperationalIntentGenerator(minx=7.4735784530639648, miny=46.9746744128218410, maxx=7.4786210060119620, maxy=46.9776318195799121, utm_zone='32T')
    altitude_of_ground_level_wgs_84 = 570 # height of the geoid above the WGS84 ellipsoid (using EGM 96) for Bern, rom https://geographiclib.sourceforge.io/cgi-bin/GeoidEval?input=46%B056%26%238242%3B53%26%238243%3BN+7%B026%26%238242%3B51%26%238243%3BE&option=Submit
    altitude_of_ground_level_wgs_84 = 570 # height of the geoid above the WGS84 ellipsoid (using EGM 96) for Bern, rom https://geographiclib.sourceforge.io/cgi-bin/GeoidEval?input=46%B056%26%238242%3B53%26%238243%3BN+7%B026%26%238242%3B51%26%238243%3BE&option=Submit
            
    num_injections = 2
    for injection_number in range(0,num_injections):
        
        my_serial_number_generator = SerialNumberGenerator()
        my_operator_id_generator = OperatorRegistrationDataGenerator()
        serial_number = my_serial_number_generator.generate_serial_number()
        operator_id = my_operator_id_generator.generate_operator_registration_number()
        # TODO: Code to generate additional fields 
        
        generate_incorrect_data = random.choice([0,1]) # a flag specify if one of the parameters of the flight_authorisation should be incorrect
        if generate_incorrect_data: # if the flag is on, make the serial number incorrect        
            incorrect_field = random.choice(['uas_serial_number','operator_registration_number']) # Pick a field to make incorrect, TODO: Additional fields to be added
            if incorrect_field == 'uas_serial_number':
                serial_number = my_serial_number_generator.generate_incorrect_serial_number(valid_serial_number = serial_number)
            elif incorrect_field == 'operator_registration_number':
                operator_id = my_operator_id_generator.generate_incorrect_operator_registration_number(valid_operator_id= operator_id)
        
        flight_authorisation_data = FlightAuthorisationData(uas_serial_number = serial_number, operation_category='Open', operation_mode = 'Vlos',uas_class='C0', identification_technologies = ['ASTMNetRID'], connectivity_methods = ['cellular'], endurance_minutes = 30, emergency_procedure_url = 'https://uav.com/emergency', operator_id = operator_id, uas_id= '', uas_type_certificate = '')
    
        should_intersect = False
        if injection_number != 0:
            coin_flip = random.choice([0,0,1]) # Geometry may or may not intersect
            should_intersect = coin_flip

        geometry_generation_rule = GeometryGenerationRule(intersect_space = should_intersect)

        flight_geometry = my_operational_intent_generator.generate_nominal_test_geometry(geometry_generation_rule= geometry_generation_rule, injection_number = injection_number)            
    
        flight_volume = my_operational_intent_generator.generate_astm_4d_volumes(raw_geometry = flight_geometry, altitude_of_ground_level_wgs_84 = altitude_of_ground_level_wgs_84)
        
        operational_intent_test_injection = my_operational_intent_generator.generate_injection_operational_intents(astm_4d_volume = [flight_volume])
    
        inject_flight_request = InjectFlightRequest(operational_intent= operational_intent_test_injection, flight_authorisation= flight_authorisation_data)
        
        all_incorrect_result_details = []
        flight_authorisation_processing_result_details = {}

        if generate_incorrect_data:
            expected_flight_authorisation_processing_result = 'Rejected'   

            if incorrect_field == 'uas_serial_number':                 
                if_planned_explanation = KnownIssueFields(test_code = 'flight_authorisation_test', relevant_requirements = ['A correct UAS Serial number is equired by ANNEX IV of COMMISSION IMPLEMENTING REGULATION (EU) 2021/664, paragraph 1'], severity= 1, subject='UAS Serial Number provided is incorrect', summary ="The UAS serial number provided in the injection attempt was incorrect", details = "The UAS serial number is not as expressed in the ANSI/CTA-2063 Physical Serial Number format and should be rejected.")                
                flight_authorisation_processing_result_details['Planned'] = if_planned_explanation
           
            elif incorrect_field == 'operator_registration_number':                
                if_planned_explanation = KnownIssueFields(test_code = 'flight_authorisation_test', relevant_requirements = ['A correct Operational Registration number is equired by ANNEX IV of COMMISSION IMPLEMENTING REGULATION (EU) 2021/664, paragraph 1'], severity= 1, subject='Operator Registration Number provided is incorrect', summary ="The Operator Registration number provided in the injection attempt was incorrect", details = "The UAS serial number is not as expressed as described in the EN4709-02 standard should be rejected.")

                flight_authorisation_processing_result_details['Planned'] = if_planned_explanation

        else:

            expected_flight_authorisation_processing_result = 'Planned'
            
            common_error_notification = KnownIssueFields(test_code = 'flight_authorisation_test', relevant_requirements = ['A correct UAS Serial number is equired by ANNEX IV of COMMISSION IMPLEMENTING REGULATION (EU) 2021/664, paragraph 1'], severity= 1, subject='All data provided is correct and conforms to the appropriate standards', summary ="The flight authorisation data provided was full and correct", details = "All data provided was complete and correct, conforming to the relevant standardized formats and the data should have been processed successfully and flight Planned.")
                        
            flight_authorisation_processing_result_details['Rejected']= common_error_notification
            flight_authorisation_processing_result_details['Failed']= common_error_notification
            
            
        all_incorrect_result_details.append(flight_authorisation_processing_result_details)
        operational_intent_processing_result_details = {}

        if should_intersect: 
            expected_operational_intent_processing_result = 'ConflictWithFlight'

            if_planned_explanation = KnownIssueFields(test_code = 'nominal_test', relevant_requirements = ['A operational intent that has time or space conflict should be planned by the USS'], severity= 1, subject='Operational Intent provided should not be planned', summary ="The operational intent details provided were generated in such a way that they should not have been planned.", details = "The co-ordinates of the 4D Opeational intent does conflicts with any existing operational intent in the area and the processing result should not be a successful planning of the intent.")
            
            operational_intent_processing_result_details['Planned'] = if_planned_explanation
        else: 
            expected_operational_intent_processing_result= 'Planned'

            if_conflict_with_flight_explanation = KnownIssueFields(test_code = 'nominal_test', relevant_requirements = ['A operational intent that has no time or space conflict should be planned by the USS'], severity= 1, subject='Operational Intent provide should be planned', summary ="The operational intent details provided were generated in such a way that they should have been planned.", details = "The co-ordinates of the 4D Opeational intent does not conflict with any existing operational intent in the area and the processing result should be a successful planning of the intent.")
            
            operational_intent_processing_result_details['ConflictWithFlight'] = if_conflict_with_flight_explanation

        injection_target = InjectionTarget(uss_role = 'Submitting USS')

        known_responses = [KnownResponses(acceptable_results=[expected_flight_authorisation_processing_result, expected_operational_intent_processing_result], incorrect_result_details= all_incorrect_result_details)]
        
        flight_injection_attempt = FlightInjectionAttempt(test_injection = inject_flight_request, known_responses = known_responses,injection_target = injection_target)
        
        flight_injection_attempts.append(flight_injection_attempt)
    
    return flight_injection_attempts
        
class AutomatedTestsWriter():
    ''' A class to write raw Flight injection attempt and volumes to disk so that they can be examined / used in other software '''

    def write_automated_test_to_disk(self,output_path:os.path, flight_injection_attempts: List[FlightInjectionAttempt], country_code='che') -> None:
        ''' A method to automated test to disk '''
    
        
        output_directory = Path(output_path, country_code) 
        # Create test_definition directory if it does not exist        
        output_directory.mkdir(parents=True, exist_ok=True)
        # The generator creates two sub-directories to write the files, the 4D Volumes are written in the astm_4d_volumes directory and the rules regarding the generation and the expected output from processing the Volume 4D sequentially. Since the DSS is a First In First Out system, we expect the first volume processing to be accepted.
        output_subdirectories = OutputSubDirectories(autmoated_test_base_path = Path(output_directory, 'autmated_test'))        
        output_subdirectories.autmoated_test_base_path.mkdir(parents=True, exist_ok=True)       

        automated_test_data = AutomatedTest(injection_attempts = flight_injection_attempts)
         
        automated_test_file_name = 'automated_test_%s.json' % str(1)  # Avoid Zero based numbering           
        automated_test_file = Path(output_subdirectories.autmoated_test_base_path, automated_test_file_name)
        with open(automated_test_file, 'w') as f:
            f.write(json.dumps(automated_test_data))


if __name__ == '__main__':    
    flight_injection_attempts = generate_flight_injection_attempts()    
    output_path = os.path.join(Path(__file__).parent.absolute(), '../test_definitions')
    my_injection_attempt_writer = AutomatedTestsWriter()
    my_injection_attempt_writer.write_automated_test_to_disk(output_path=output_path,flight_injection_attempts = flight_injection_attempts)
