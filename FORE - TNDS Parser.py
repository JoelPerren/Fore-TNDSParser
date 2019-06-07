#------------------------------------------------------------------------------
# A tool to parse TNDS and return the bus route and timetabling data
# (c) Joel Perren (Fore Consulting Limited) 2019
#------------------------------------------------------------------------------

#------------------------------------------------------------------------------
# Imports and Parameters
#------------------------------------------------------------------------------

import os
import xml.etree.ElementTree as et
import time
from operator import itemgetter

XML_PATH = "C:\\Users\\Joel.Perren\\Documents\\Traveline Data\\TransXChange\\XML\\Yorkshire\\SVRYWAO034.xml"
NS = {"tnds": "http://www.transxchange.org.uk/"}

#------------------------------------------------------------------------------
# Main Script
#------------------------------------------------------------------------------

tree = et.parse(XML_PATH)
root = tree.getroot()

def get_service_information():
	service = root.find('tnds:Services/tnds:Service', NS)
	
	if service == None:
		return None

	service_info = {
		"Mode" : service.find('tnds:Mode', NS).text,
		"Service Code" : service.find('tnds:ServiceCode', NS).text,
		"Line Name" : service.find('tnds:Lines/tnds:Line/tnds:LineName', NS).text,
		"Operator": root.find('tnds:Operators/tnds:Operator/tnds:OperatorShortName', NS).text,
		"Descirption": service.find('tnds:Description', NS).text
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
			"time": departure_time,
			"operating_profile" : operating_profile,
			"journey_pattern" : journey_pattern,
			"direction": direction,
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
			"weekday": [],
			"saturday": [],
			"sunday": [],
		}

	for journey in sorted_journeys:
		results[journey['direction']][journey['operating_profile']].append((journey['time'], journey['journey_pattern']))

	return results

