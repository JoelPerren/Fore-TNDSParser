#------------------------------------------------------------------------------
# A tool to parse TNDS and return the bus route and timetabling data
# Requires Python 3 (e.g. py -3 "path_to_.py file")
# (c) Joel Perren (Fore Consulting Limited) 2019
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
# Imports and Parameters
#------------------------------------------------------------------------------

import os
import xml.etree.ElementTree as et
import time
import csv
import datetime
from operator import itemgetter

XML_PATH = "C:\\Users\\Joel.Perren\\Documents\\Traveline Data\\TransXChange\\Wakefield Aimsun Model\\XML"
NS = {"tnds": "http://www.transxchange.org.uk/"}
OUTPUT_DIR = "C:\\Users\\Joel.Perren\\Documents\\Traveline Data\\TransXChange\\Wakefield Aimsun Model\\CSV\\"

#------------------------------------------------------------------------------
# Function Definitions
#------------------------------------------------------------------------------

def get_service_information():
	service = root.find('tnds:Services/tnds:Service', NS)
	
	if service == None:
		return None

	service_info = {
		"Mode"         : service.find('tnds:Mode', NS).text,
		"Service Code" : service.find('tnds:ServiceCode', NS).text,
		"Line Name"    : service.find('tnds:Lines/tnds:Line/tnds:LineName', NS).text,
		"Operator"     : root.find('tnds:Operators/tnds:Operator/tnds:OperatorShortName', NS).text,
		"Description"  : service.find('tnds:Description', NS).text
	}

	return service_info

def get_all_journeys():

	vehicle_journeys = []

	for journey in root.find('tnds:VehicleJourneys', NS):
		departure_time = journey.find('tnds:DepartureTime', NS).text
		operating_profile = find_operating_profile(journey)
		journey_pattern = journey.find('tnds:JourneyPatternRef', NS).text
		direction = root.find("tnds:JourneyPatternSections/*[@id='{}']/tnds:JourneyPatternTimingLink/tnds:Direction".format(journey_pattern), NS).text

		journey_object = {
			"time"              : departure_time,
			"operating_profile" : operating_profile,
			"journey_pattern"   : journey_pattern,
			"direction"         : direction,
		}

		vehicle_journeys.append(journey_object)

	return vehicle_journeys


def find_operating_profile(vehicle_journey):
	days_of_week = vehicle_journey.find('tnds:OperatingProfile/tnds:RegularDayType/tnds:DaysOfWeek', NS)

	for day in days_of_week:
		if "Saturday" in day.tag:
			return "saturday"
		elif "Sunday" in day.tag:
			return "sunday"

	return "weekday"


def get_unique_directions(journeys):
	all_directions = []

	for journey in journeys:
		all_directions.append(journey['direction'])

	directions = list(set(all_directions))

	return directions

def organise_journeys(journeys):
	unique_directions = get_unique_directions(journeys)
	sorted_journeys = sorted(journeys, key=itemgetter('time'))
	results = {}

	for direction in unique_directions:
		results[direction] = {
			"weekday"  : [],
			"saturday" : [],
			"sunday"   : [],
		}

	for journey in sorted_journeys:
		results[journey['direction']][journey['operating_profile']].append((journey['time'], journey['journey_pattern']))

	return results

def get_stops_from_journey_pattern(journey_pattern_ref):
	journey_pattern = root.find("tnds:JourneyPatternSections/*[@id='{}']".format(journey_pattern_ref), NS)
	results = []

	for link in journey_pattern:
		journey_link = {
			"To"            : link.find('tnds:To/tnds:StopPointRef', NS).text,
			"From"          : link.find('tnds:From/tnds:StopPointRef', NS).text,
			"Duration"      : link.find('tnds:RunTime', NS).text.strip('PTS'),
			"Timing Status" : link.find('tnds:From/tnds:TimingStatus', NS).text,
		}

		results.append(journey_link)

	return results

def write_results(schedule):
	organised_journeys = organise_journeys(get_all_journeys())
	service_info = get_service_information()

	for direction in organised_journeys:
		csvfile = open("{}{} {} ({}).csv". format(OUTPUT_DIR, service_info['Line Name'], direction, schedule), 'w', newline='')
		csvwriter = csv.writer(csvfile, delimiter = ',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
		csvwriter.writerow(["{} {} ({})".format(service_info['Line Name'], service_info['Description'], direction)])

		for journey in organised_journeys[direction][schedule]:
			line = []
			start_time = journey[0]
			current_time = start_time
			# line.append(start_time)
			journey_pattern = get_stops_from_journey_pattern(journey[1])
			first = True

			for link in journey_pattern:
				if (first):
					line.append("{} ({})".format(link['From'], current_time))
					first = False
				
				current_time = add_seconds(current_time, link['Duration'])
				line.append("{} ({})".format(link['To'], current_time))

			csvwriter.writerow(line)

		csvfile.close()

def add_seconds(strtime, secs):
	time = datetime.datetime.strptime(strtime, '%H:%M:%S')
	fulldate = datetime.datetime(100, 1, 1, time.hour, time.minute, time.second)
	fulldate = fulldate + datetime.timedelta(seconds=int(secs))
	return fulldate.time().strftime('%H:%M:%S')

#------------------------------------------------------------------------------
# Main Script
#------------------------------------------------------------------------------

xml_files = []

for file in os.listdir(XML_PATH):
	if file.endswith(".xml"):
		xml_files.append(file)

user_input = input("Enter operating profile ('weekday', 'saturday', or 'sunday'): ").lower()

for file in xml_files:
	tree = et.parse("{}\\{}".format(XML_PATH, file))
	root = tree.getroot()
	write_results(user_input)

print("Success")