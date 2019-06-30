import xml.etree.ElementTree as et
import os
from difflib import SequenceMatcher
from datetime import time

#-
# Classes 
#-

class TNDSTimetable:
    name_space = {"tnds": "http://www.transxchange.org.uk/"}

    def __init__(self, tnds_file):
        self.file_name = os.path.basename(tnds_file)
        self.root = et.parse(tnds_file).getroot()
        self.service_info = self.find_service_info()
        self.stops = self.find_stops()
        self.jpref_prefix = self.find_jpref_prefix()
        self.jps_prefix = self.find_jps_prefix()
        self.vehicle_journeys = self.find_vehicle_journeys()
        self.unique_directions = self.find_unique_directions()

    def find_service_info(self):
        service = self.root.find("tnds:Services/tnds:Service", self.name_space)
        service_info = {
            "Mode"          : "n/a",
            "Service Code"  : "n/a",
            "Line Name"     : "n/a",
            "Description"   : "n/a",
        }

        try:
            service_info["Mode"] = service.find("tnds:Mode", self.name_space).text
        except:
            pass
        try:
            service_info["Service Code"] = service.find("tnds:ServiceCode", self.name_space).text
        except:
            pass
        try:
            service_info["Line Name"] = service.find("tnds:Lines/tnds:Line/tnds:LineName", self.name_space).text
        except:
            pass
        try:
            service_info["Desciption"] = service.find("tnds:Description", self.name_space).text
        except:
            pass

        return service_info
    
    def find_vehicle_journeys(self):
        journeys = self.root.find("tnds:VehicleJourneys", self.name_space)
        results = []

        for journey in journeys:
            results.append(TNDSJourney(journey, self))

        return results

    def find_stops(self):
        stop_points = self.root.find("tnds:StopPoints", self.name_space)
        results = {}

        for stop in stop_points:
            stop_ref = stop.find("tnds:StopPointRef", self.name_space).text
            stop_name = stop.find("tnds:CommonName", self.name_space).text

            results[stop_ref] = stop_name

        return results

    def find_unique_directions(self):
        all_directions = []

        for journey in self.vehicle_journeys:
            all_directions.append(journey.direction)
        
        directions = list(set(all_directions))

        return directions

    def longest_common_substring(self, s1, s2):
        seq_match = SequenceMatcher(None, s1, s2)
        match = seq_match.find_longest_match(0, len(s1), 0, len(s2))

        if (match.size > 0):
            return (s1[match.a: match.a + match.size])
        else:
            return None

    def find_jpref_prefix(self):
        journeys = self.root.find("tnds:VehicleJourneys", self.name_space)
        jprefs = []

        for journey in journeys:
            try:
                jpref = journey.find("tnds:JourneyPatternRef", self.name_space).text
            except:
                pass

            jprefs.append(jpref)
        
        return self.longest_common_substring(jprefs[0], jprefs[-1])

    def find_jps_prefix(self):
        journey_patterns = self.root.find("tnds:JourneyPatternSections", self.name_space)
        jp_ids = []

        for jp in journey_patterns:
            try:
                jp_id = jp.attrib["id"]
            except:
                pass

            jp_ids.append(jp_id)
        
        return self.longest_common_substring(jp_ids[0], jp_ids[-1])


class TNDSJourney:
    def __init__(self, vehicle_journey, TNDSTimetable):
        self.vehicle_journey = vehicle_journey
        self.timetable = TNDSTimetable
        self.initial_time = self.find_initial_time()
        self.operating_profile = self.find_operating_profile()
        self.journey_pattern = self.find_route()
        self.direction = self.find_direction(self.find_journey_pattern())

    def find_initial_time(self):
        initial_time = self.vehicle_journey.find("tnds:DepartureTime", self.timetable.name_space).text
        return initial_time

    def find_operating_profile(self):
        days_of_week = self.vehicle_journey.find('tnds:OperatingProfile/tnds:RegularDayType/tnds:DaysOfWeek', self.timetable.name_space)
        results = [0,0,0,0,0,0,0]

        for day in days_of_week:
            tag = day.tag.strip("{http://www.transxchange.org.uk/}")
            if (tag == "Monday"):
                results[0] = 1
            elif (tag == "Tuesday"):
                results[1] = 1
            elif (tag == "Wednesday"):
                results[2] = 1
            elif (tag == "Thursday"):
                results[3] = 1
            elif (tag == "Friday"):
                results[4] = 1
            elif (tag == "Saturday"):
                results[5] = 1
            elif (tag == "Sunday"):
                results[6] = 1
            elif (tag == "MondayToFriday"):
                results = [1,1,1,1,1,0,0]
            elif (tag == "MondayToSaturday"):
                results = [1,1,1,1,1,1,0]
            elif (tag == "MondayToSunday"):
                results = [1,1,1,1,1,1,1]
            else:
                print("Unhandled Operating Profile: {}".format(tag))
        
        return results

    def find_journey_pattern(self):
        jpref_prefix = self.timetable.jpref_prefix
        jps_prefix = self.timetable.jps_prefix
        jpref = self.vehicle_journey.find("tnds:JourneyPatternRef", self.timetable.name_space).text[len(jpref_prefix):]
        journey_pattern = self.timetable.root.find("tnds:JourneyPatternSections/*[@id='{}{}']".format(jps_prefix, jpref), self.timetable.name_space)
        return journey_pattern

    def find_route(self):
        jp = self.find_journey_pattern()
        route = []
        for link in jp:
            route.append(TNDSLink(link, self))
        return route

    def find_direction(self, jp):
        rl_ref = jp.find("tnds:JourneyPatternTimingLink/tnds:RouteLinkRef", self.timetable.name_space).text
        route = self.timetable.root.find("tnds:RouteSections/*/*[@id='{}']".format(rl_ref), self.timetable.name_space)
        direction = route.find("tnds:Direction", self.timetable.name_space).text
        return direction



class TNDSLink:
    def __init__(self, timing_link, TNDSJourney):
        self.timing_link = timing_link
        self.journey = TNDSJourney
        self.start_point = self.find_start()
        self.end_point = self.find_end()
        self.duration = self.find_duration()

    def find_start(self):
        stop_id = self.timing_link.find("tnds:From/tnds:StopPointRef", self.journey.timetable.name_space).text
        stop_name = self.journey.timetable.stops[stop_id]
        return (stop_id, stop_name)

    def find_end(self):
        stop_id = self.timing_link.find("tnds:To/tnds:StopPointRef", self.journey.timetable.name_space).text
        stop_name = self.journey.timetable.stops[stop_id]
        return (stop_id, stop_name)

    def find_duration(self):
        run_time = self.timing_link.find("tnds:RunTime", self.journey.timetable.name_space).text
        number = int(run_time[2:-1])
        unit = run_time[-1]
        duration = None

        if (unit == "M"):
            duration = time(0, number, 0)
        else:
            if (number % 60) == 0:
                duration = time(0, int(number/60), 0)
            else:
                mins = number // 60
                secs = number % 60
                duration = time(0, int(mins), int(secs))
        
        return duration.isoformat()

#-
# Utilities
#-

def add_time(cur_time, hours, minutes, seconds):
    pass

def journey_to_csv_line(journey_obj):
    pass

#-
# Main Script
#- 

# XML = "C:\\Users\\joelp\\Google Drive\\Coding\\Fore-TNDSParser\\NW_05_ROS_464_1.xml"
XML = "C:\\Users\\joelp\\Google Drive\\Coding\\Fore-TNDSParser\\SVRYWAO049.xml"
tt = TNDSTimetable(XML)

for journey in tt.vehicle_journeys:
    if (journey["Operating Profile"][:5] != [1,1,1,1,1]):
        continue
    
