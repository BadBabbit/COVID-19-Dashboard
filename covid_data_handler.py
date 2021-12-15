import csv, json
from typing import Tuple
from uk_covid19 import Cov19API  # pip install uk-covid19
from datetime import datetime
import logging

logging.basicConfig(filename='log_file.log', encoding='utf-8')


def parse_csv_data(csv_filename) -> list:  # Function to parse csv data into a list.
    """extracts CSV data and formats it as a list.

    :param csv_filename: the name of the CSV file you wish to parse.
    :return: the lines of the CSV as a list of lists.
    """
    file_lines = []  # initialises list to append to
    with open(csv_filename) as file:
        csv_reader = csv.reader(file, delimiter=",")  # .reader method helps organising file into a 2D array
        for line in csv_reader:  # each line is read and appended to the list
            file_lines.append(line)
    return file_lines


def process_national_covid_csv_data(covid_csv_data) -> Tuple[int, int, int]:
    """Processes CSV data to find cases over the past seven days, hospitalisations, and cumulative deaths.

    :param covid_csv_data: the extracted data of a CSV file, in the form of a list of lists.
    :return: multivariable return of three integer values.
    """
    national7days_cases = 0
    cases_counter = 0  # Counts number of days that have been counted
    first_data_hit = False  # Flag to represent if data has been passed, so the first item can be skipped.
    for row in covid_csv_data:
        if row[2] != "" and row[2] != "hospitalCases":
            hospital_cases = int(row[2])
            break
    for row in covid_csv_data:
        if row[1] != "" and row[1] != "cumDeaths28DaysByDeathDate":  # Skips empty elements and title element
            cum_deaths = int(row[1])  # Takes the first element with data.
            break
    for row in covid_csv_data:  # For-loop to avoid errors where data items are not present.
        if row[3] != "" and row[3] != "newCasesByPublishDate":  # Skips empty elements and title element
            if first_data_hit:
                cases_counter += 1
                national7days_cases += int(row[3])
                if cases_counter == 7:  # If a week's worth of data has been accumulated, closes loop.
                    break
            else:  # Flips the flag and moves on to next data item
                first_data_hit = True
                continue
    logging.info("national covid data successfully processed at %s", datetime.now())
    return national7days_cases, hospital_cases, cum_deaths


def process_local_covid_csv_data(covid_csv_data) -> int:
    """Processes CSV data to find cases over the past seven days (in a lower-tier local authority).

    :param covid_csv_data: the extracted data of a CSV file, in the form of a list of lists
    :return: Integer value representing cases of COVID-19 over the past 7 days.
    """
    local7days_cases = 0
    cases_counter = 0  # Counts number of days that have been counted
    first_data_hit = False  # Flag to represent if data has been passed, so the first item can be skipped.

    for row in covid_csv_data:  # For-loop to avoid errors where data items are not present.
        if row[3] != "" and row[3] != "newCasesBySpecimenDate":  # Skips empty elements and title element
            if first_data_hit:
                cases_counter += 1
                local7days_cases += int(row[3])
                if cases_counter == 7:  # If a week's worth of data has been accumulated, closes loop.
                    break
            else:  # Flips the flag and moves on to next data item
                first_data_hit = True
                continue
    logging.info("local covid data successfully processed at %s", datetime.now())
    return local7days_cases


def covid_API_request(
        location=json.loads(open("config.json").read())["location"],
        location_type=json.loads(open("config.json").read())["location_type"]
) -> list:
    """Function makes an API request to get data for a specified location.

    :param location: String representing the name of the location, i.e. "Exeter".
    :param location_type: String representing the type of the location, i.e. "ltla".
    :return: List containing CSV formatted data pulled from the COVID API.
    """
    filters = [
        'areaType=' + location_type,
        'areaName=' + location
    ]
    structure = {
        "date": "date",
        "cumDeaths28DaysByDeathDate": "cumDeaths28DaysByDeathDate",
        "hospitalCases": "hospitalCases",
        "newCasesByPublishDate": "newCasesByPublishDate"
    }
    # NOTE: hospitalCases and cumDailyNsoDeathsByDeathDate do not return values for local authorities.
    try:
        api = Cov19API(filters=filters, structure=structure)
        data = api.get_csv()
        data = data.split("\n")
        for i in range(len(data)):
            data[i] = data[i].split(",")
        logging.info("Covid API call successfully made at %s", datetime.now())
    except ConnectionError:
        logging.error("ERROR: Could not make Covid API call due to a connection error; check your internet and try again.")
        data = []
    return data


def create_csv(data, local=True) -> None:
    """Stores pulled CSV-formatted data from Covid-19 API into a CSV.

    :param data: CSV-formatted data, as a list.
    :param local: Boolean value dictating whether the function should update the local or national data.
    :return: None-type.
    """
    if local:
        file_name = "local_data.csv"
    else:
        file_name = "national_data.csv"
    with open(file_name, "w", newline="") as csv_file:
        file = csv.writer(csv_file, delimiter=",")
        for line in data:
            file.writerow(line)
    return None
