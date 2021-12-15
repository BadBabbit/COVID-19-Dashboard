from flask import Flask, render_template, request
from covid_news_handling import *
from covid_data_handler import *
from datetime import datetime
from sched import scheduler
import time
import logging
from csv import writer
from webbrowser import open as open_webpage

# noinspection PyArgumentList
logging.basicConfig(filename='log_file.log', encoding='utf-8')

app = Flask(__name__)
event_scheduler = scheduler(time.time, time.sleep)

first_itr = True  # Flag is necessary so index() doesn't attempt to load data from stored_updates.csv each iteration.

def update_news(name="News update", repeat=False, is_both=False) -> None:
    """Updates the articles variable (defined in the global namespace) by
    calling the api request function.

    :param is_both: Boolean variable that dictates whether the news update is part of a 'both' update. If
    True, function will not schedule repeat upon repeat as this will be handled in the 'update_all' function.
    :param name: User-selected identifier of the update; string.
    :param repeat: Boolean variable that dictates whether the function will run again in 24 hours.
    :return: None-type.
    """
    current_articles = news_API_request()
    for i in current_articles:
        for j in removed_articles:
            if i == j:
                current_articles.remove(i)
    if repeat and not is_both:  # Will not repeat if the repeat has already been scheduled in update_all()
        event_id = news_scheduler.enter(24 * 60 * 60, 1, update_news, argument=(True,))
        store_update(
            event_id,
            datetime.now().replace(day=datetime.now().day + 1),
            "news",
            name,
            str(repeat)
        )
    return None


def update_covid_data(name="covid update", repeat=False, is_both=False) -> None:
    """Updates all relevant data for the index template and stores it in CSV files.

    :param name: User-defined name of the update. defaults to 'covid update'.
    :param repeat: Boolean variable that dictates whether the function will run again in 24 hours.
    :param is_both:Boolean variable that dictates whether the covid update is part of a 'both' update. If
    True, function will not schedule repeat upon repeat as this will be handled in the 'update_all' function.
    :return: None-type.
    """
    local_data = covid_API_request()
    national_data = covid_API_request(json.loads(open("config.json").read())["country"], "nation")
    create_csv(local_data)
    create_csv(national_data, False)
    if repeat and not is_both:
        event_id = event_scheduler.enter(24 * 60 * 60, 1, update_covid_data, argument=(True,))
        store_update(
            event_id,
            datetime.now().replace(day=datetime.now().day + 1),
            "covid-data",
            name,
            str(repeat)
        )
    return None


def update_all(name="Data and News update", repeat=False) -> None:
    """Updates both news and covid data by calling the respective update functions, and schedules a repeat if necessary.

    :param name: User-defined name of the update. defaults to 'data and news update'.
    :param repeat: Dictates whether the update will repeat 24 hours later.
    :return: None type.
    """
    update_news(name, repeat, is_both=True)
    update_covid_data(name, repeat, is_both=True)
    if repeat:
        event_id = event_scheduler.enter(24 * 60 * 60, 1, update_all, argument=(name, True,))
        store_update(
            event_id,
            str(datetime.now().replace(day=datetime.now().day + 1)),
            "both",
            name,
            str(repeat)
        )
        logging.info("Repeating update scheduled for %s", str(datetime.now().replace(day=datetime.now().day + 1)))
    return None


def store_update(event_id, abs_time, update_type, update_name, repeat) -> None:
    """Stores a row of elements describing a scheduled event to a CSV file, which is read from at the
    beginning of each execution of the code. These events are either deleted or rescheduled, depending on
    whether they've happened already.

    :param event_id: Event identification, needed for cancelling event if necessary.
    :param abs_time: The absolute datetime of the update, in 'YYYY-mm-dd HH:MM:SS' format.
    :param update_type: String specifies whether the update will effect covid data, news articles, or both.
    :param update_name: User-defined name of the update
    :param repeat: Boolean variable to represent whether the update will repeat or not.
    :return: None.
    """
    row = [event_id, str(abs_time), update_type, update_name, repeat]
    with open("updates.csv", "a+", newline="") as f:
        writer(f).writerow(row)
    return None


def cancel_stored_update(event_id) -> None:
    """Calls the event scheduler to cancel an event with a given ID, and removes it from storage. Will search

    :param event_id: The unique event ID.
    :return: None.
    """
    updates = []
    with open("updates.csv") as f:
        csv_reader = csv.reader(f, delimiter=",")
        for line in csv_reader:
            updates.append(line)
    for update in updates:
        if update[0] == event_id:
            try:
                event_scheduler.cancel(event_id)
            except ValueError:
                logging.warning("WARNING: event %s could not be cancelled at %s because it does not exist.", event_id, datetime.now())
            finally:
                updates.remove(update)
                break
    with open("updates.csv", "w", newline="") as f:
        csv_writer = csv.writer(f, delimiter=",")
        for update in updates:
            csv_writer.writerow(update)


@app.route("/")
@app.route("/index")
def index():
    """Handles requests from index.html and the scheduling of updates.

    :return: The template for the HTML page, containing data to be displayed there.
    """
    event_scheduler.run(blocking=False)
    global first_itr
    logging.info("INFO: request.view args at %s: %s", datetime.now(), request.args)
    stored_updates = []
    updates = []
    update_types = {  # dictionary makes scheduling different types of data
        # easier, and removes the need for consecutive if-statements.
        "covid-data": [update_covid_data, "Covid update at "],
        "news": [update_news, "News update at "],
        "both": [update_all, "Covid and news update at"]
    }
    try:
        with open("updates.csv") as file:
            csv_reader = csv.reader(file, delimiter=",")  # .reader method helps organising file into a 2D array
            for line in csv_reader:  # each line is read and appended to the list
                stored_updates.append(line)
    except FileNotFoundError:  # Creates the file if it doesn't exist
        with open("updates.csv", "w") as f:
            pass
    try:
        local7days_cases = process_local_covid_csv_data(parse_csv_data("local_data.csv"))
        nat7days_cases, hospital_cases, cum_deaths = process_national_covid_csv_data(parse_csv_data("national_data.csv"))
    except FileNotFoundError:
        update_covid_data()
        local7days_cases = process_local_covid_csv_data(parse_csv_data("local_data.csv"))
        nat7days_cases, hospital_cases, cum_deaths = process_national_covid_csv_data(
            parse_csv_data("national_data.csv")
        )
        logging.warning("WARNING: No covid data was present. API call automatically made at %s", datetime.now())

    articles = news_API_request()
    repeat = False
    if "notif" in request.args:
        remove_article(request.args["notif"])
    articles_to_display = limit_articles(articles)
    if "two" in request.args and "update" in request.args:
        current_time = datetime.now()
        alarm_time = current_time.replace(
            hour=int(request.args["update"].split(":")[0]),
            minute=int(request.args["update"].split(":")[1])
        )
        if current_time > alarm_time:
            alarm_time = alarm_time.replace(day=alarm_time.day + 1)
        alarm_time = alarm_time.replace(microsecond=0)
        delay = abs(current_time.hour - alarm_time.hour) * 3600 + abs(current_time.minute - alarm_time.minute) * 60 - current_time.second
        content = ""
        if "repeat" in request.args:
            repeat = True
            content = "Repeating "
        if ("news" in request.args) and ("covid-data" in request.args):
            content += "News and covid update at " + str(alarm_time.replace(second=0))
            event_id = event_scheduler.enter(delay, 1, update_all, argument=(request.args["two"], repeat,))
            store_update(
                event_id,
                alarm_time.replace(second=0),
                "both",
                request.args["two"],
                str(repeat)
            )
        elif "news" in request.args:
            content += "News update at " + str(alarm_time.replace(second=0))
            event_id = event_scheduler.enter(delay, 1, update_news, argument=(request.args["two"], repeat,))
            store_update(
                event_id,
                alarm_time.replace(second=0),
                "news",
                request.args["two"],
                str(repeat)
            )
        elif "covid-data" in request.args:
            logging.warning("INFO: covid-data branch statement has been executed. FIX THE SCHEDULER EEEEE")
            content += "Covid update at " + str(alarm_time.replace(second=0))
            event_id = event_scheduler.enter(
                delay,
                1,
                update_covid_data,
                argument=(request.args["two"], repeat,)
            )
            store_update(
                event_id,
                alarm_time.replace(second=0),
                "covid-data",
                request.args["two"],
                str(repeat)
            )
        updates.append({
            'title': request.args["two"],
            'content': content
        })

    if stored_updates and first_itr:  # if stored_updates has contents and if they haven't been loaded already
        first_itr = False
        for update in stored_updates:  # extracts each update from the file and schedules it.
            event_id = update[0]
            update_name = update[3]
            if event_id in event_scheduler.queue:
                continue
            if update_name in request.args:
                cancel_stored_update(event_id)
            alarm_datetime = update[1]
            alarm_datetime = datetime.strptime(alarm_datetime, "%Y-%m-%d %H:%M:%S")
            if alarm_datetime < datetime.now():  # if the update is scheduled for the past, removes the update from storage.
                stored_updates.remove(update)
                cancel_stored_update(event_id)
                continue
            current_time = datetime.now()
            update_type = update_types[update[2]][0]
            content = update_types[update[2]][1]
            repeat = update[4]
            if repeat == "True":
                content = "Repeating " + content
            content += str(alarm_datetime)
            update_name = update[3]
            delay = abs(current_time.hour - alarm_datetime.hour) * 3600 + abs(
                current_time.minute - alarm_datetime.minute) * 60 + (60 - current_time.second)
            event_scheduler.enter(delay, 1, update_type, argument=(repeat,))
            updates.append({
                "title": update_name,
                "content": content
            })
            pass

    if articles_to_display:
        for article in articles_to_display:
            article["content"] = article["description"]
        embed_hyperlinks(articles_to_display)

    return render_template(
        "index.html",
        updates=updates,
        local_7day_infections=local7days_cases,
        national_7day_infections=nat7days_cases,
        deaths_total="Total deaths: " + str(cum_deaths),
        nation_location=json.loads(open("config.json").read())["country"],
        hospital_cases="National Hospital Cases: " + str(hospital_cases),
        location=json.loads(open("config.json").read())["location"],
        title="COVID-19 Dashboard",
        news_articles=articles_to_display,
        image="covid_info.jpg"
    )


if __name__ == "__main__":
    open_webpage("http://127.0.0.1:5000/")
    app.run()
