# -
# Imports and Parameters
# -

import os
import xml.etree.ElementTree as et
import csv
from datetime import datetime
from datetime import timedelta
from datetime import time

XML = "C:\\Users\\joelp\\Google Drive\\Coding\\Fore-TNDSParser"
NS = {"tnds" : "http://www.transxchange.org.uk/"}
OUTPUT = "C:\\Users\\joelp\\Google Drive\\Coding\\Fore-TNDSParser\\outputs"

# -
# Classes
# -

class TNDSJourney:
    def __init__(self, init_time, direction, operating_profile, route):
        self.init_time = init_time
        self.direction = direction
        self.operating_profile = operating_profile
        self.route = route

    def output_journey(self):
        time = self.init_time
        first = True
        output = []

        for leg in self.route:
            if (first):
                output.append("{} ({})".format(leg[0], time))
                first = False

            time = add_time(time, leg[2])
            output.append("{} ({})".format(leg[1], time))
        
        return output

# -
# Function Defintions
# -

def find_directions():
    route_sections = root.find("tnds:RouteSections", NS)
    directions = []
    for direction in route_sections.iter("{http://www.transxchange.org.uk/}Direction"):
        directions.append(direction.text)
    unique_directions = list(set(directions))
    return unique_directions

def find_journey_direction(journey_pattern):
    rl_ref = journey_pattern.find("tnds:JourneyPatternTimingLink/tnds:RouteLinkRef", NS).text
    rl = root.find("tnds:RouteSections/*/*[@id='{}']".format(rl_ref), NS)
    direction = rl.find("tnds:Direction", NS).text
    return direction

def find_operating_profile(veh_journey):
    days_of_week = veh_journey.find('tnds:OperatingProfile/tnds:RegularDayType/tnds:DaysOfWeek', NS)
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

def find_route(jp):
    def process_link(link):
        start = link.find("tnds:From/tnds:StopPointRef", NS).text
        end = link.find("tnds:To/tnds:StopPointRef", NS).text

        run_time = link.find("tnds:RunTime", NS).text
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
        duration = duration.isoformat()
        return (start, end, duration)
        
    route = []
    for link in jp:
        route.append(process_link(link))
    return route

def find_related_jp(veh_journey):
    jpref = veh_journey.find("tnds:JourneyPatternRef", NS).text[len(jpref_prefix):]
    journey_pattern = root.find("tnds:JourneyPatternSections/*[@id='{}{}']".format(jps_prefix, jpref), NS)
    return journey_pattern

def find_jpref_prefix():
    journeys = root.find("tnds:VehicleJourneys", NS)
    jprefs = []

    for journey in journeys:
        jprefs.append(journey.find("tnds:JourneyPatternRef", NS).text)
    
    prefix = longest_substring(list(set(jprefs)))
    return prefix

def find_jps_prefix():
    jps = root.find("tnds:JourneyPatternSections", NS)
    jp_ids = []

    for jp in jps:
        jp_ids.append(jp.attrib["id"])
    
    prefix = longest_substring(list(set(jp_ids)))
    return prefix

def longest_substring(strings):
    substr = ""
    if len(strings) > 1 and len(strings[0]) > 0:
        for i in range(len(strings[0])):
            for j in range(len(strings[0])-i+1):
                if j > len(substr) and all(strings[0][i:i+j] in x for x in strings):
                    substr = strings[0][i:i+j]
    return substr

def add_time(cur_time, plus_time):
    time = datetime.strptime(cur_time, "%H:%M:%S")
    to_add = datetime.strptime(plus_time, "%H:%M:%S")
    fulldate = datetime(100, 1, 1, time.hour, time.minute, time.second)
    fulldate = fulldate + timedelta(hours=to_add.hour, minutes=to_add.minute, seconds=to_add.second)
    return fulldate.time().strftime('%H:%M:%S')

# -
# Main Script
# -

xml_files = []
for file in os.listdir(XML):
	if file.endswith(".xml"):
		xml_files.append(file)

for file in xml_files:
    try:
        tree = et.parse("{}\\{}".format(XML, file))
        root = tree.getroot()
        line = root.find("tnds:Services/tnds:Service/tnds:Lines/tnds:Line/tnds:LineName", NS).text
        directions = find_directions()
        jpref_prefix = find_jpref_prefix()
        jps_prefix = find_jps_prefix()

        timetable_journeys = []
        for veh_journey in root.iter("{http://www.transxchange.org.uk/}VehicleJourney"):
            init_time = veh_journey.find("tnds:DepartureTime", NS).text
            operating_profile = find_operating_profile(veh_journey)
            journey_pattern = find_related_jp(veh_journey)
            direction = find_journey_direction(journey_pattern)
            route = find_route(journey_pattern)
            timetable_journeys.append(TNDSJourney(init_time, direction, operating_profile, route))
        timetable_journeys.sort(key=lambda x: x.init_time)
            
        for direction in directions:
            csvfile = open("{}\\{} ({}).csv".format(OUTPUT, line, direction), "w", newline="")
            csvwriter = csv.writer(csvfile, delimiter = ',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
            for journey in timetable_journeys:
                if (journey.operating_profile[:5] == [1,1,1,1,1] and journey.direction == direction):
                    csvwriter.writerow(journey.output_journey())
            csvfile.close()
        print("{} parsed succesfully".format(file))
    except Exception as e:
        print("ERROR: Could not parse {}. [{}]".format(file, e))

print("TNDS files parsed!")