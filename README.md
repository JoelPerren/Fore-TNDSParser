# Fore-TNDSParser
A tool to parse TNDS .xml files and return the associated route and timetabling data into CSV format.

## Traveline National Dataset (TNDS)
The Traveline National Dataset contains public transport timetables for bus services in Great Britain.

See https://data.gov.uk/dataset/0447f8d9-8f1b-4a68-bbc8-246981d02256/traveline-national-dataset for more information.

## Inputs
The script, through the 'XML' global variable, searches a given directory for .xml files which it then attempts to parse.

## Outputs
In the directory specified by the 'OUTPUT' global variable the script writes a .csv file for each *journey direction* in each .xml file. In practicality, this often means that there is more than one .csv file output for each .xml file input.

Each row of a given .csv file represents one vehicle journey in the timetable. Each cell of the row contains the ATCO Code of a bus stop and the time at which the bus is scheduled to arrive at the bus stop in parenthesis.

## Usage
Run the script using Python 3.

*Python "Fore - TNDS Parser.py"*