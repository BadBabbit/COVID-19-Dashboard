import covid_news_handling
from covid_data_handler import *
from covid_news_handling import *
from sched import scheduler
from time import *
from datetime import datetime
from main import cancel_stored_update, update_covid_data

logging.basicConfig(filename='log_file.log', encoding='utf-8')

def test_parse_csv_data():
    data = parse_csv_data('nation_2021-10-28.csv')
    print("Length: " + str(len(data)))
    print(data)
    try:
        assert len(data) == 639
    except AssertionError:
        print("Failed to assert.")


def test_process_covid_csv_data():
    last7days, current_hospital_cases, total_deaths = process_local_covid_csv_data(parse_csv_data('nation_2021-10-28.csv'))
    try:
        assert last7days == 240_299
        assert current_hospital_cases == 7_019
        assert total_deaths == 141_544
    except AssertionError:
        print("Failed to assert.")


def test_news_API_request():
    headlines = news_API_request()
    print(headlines)
    assert headlines['totalResults'] > 0


def foo():
    print("hello world")


def datetime_test():
    current_time = datetime.now()
    time = "13:45"
    alarm_time = current_time.replace(
        hour=int(time.split(":")[0]),
        minute=int(time.split(":")[1])
    )
    if current_time > alarm_time:
        alarm_time = alarm_time.replace(day=alarm_time.day + 1)
    alarm_time = alarm_time.replace(second=0, microsecond=0)
    delay = abs(current_time.hour - alarm_time.hour)*3600 + abs(current_time.minute - alarm_time.minute)*60
    print(delay)
    s = scheduler()
    s.enter(delay, 1, foo)
    s.run()

    return alarm_time

def news_test():
    articles = news_API_request()
    print(articles)
    print(limit_articles(articles))
    assert len(articles) > 1


def logging_test():
    logging.warning("watch yo jet bro. watch yo jet bro. watCH YO J-")
    # https://www.youtube.com/watch?v=nQN2ytZzic8
    try:
        lmao = 0/0
    except ZeroDivisionError:
        logging.error("bruh. error occured at %s", datetime.now())

def str_datetime_to_time_test():
    str_datetime = "2021-12-10 16:00:00"
    datetime_obj = datetime.strptime(str_datetime, "%Y-%m-%d %H:%M:%S")
    return datetime_obj.time()

def read_csv_lines_test():
    updates = []
    with open("updates.csv") as file:
        csv_reader = csv.reader(file, delimiter=",")  # .reader method helps organising file into a 2D array
        for line in csv_reader:  # each line is read and appended to the list
            updates.append(line)
    return updates

def test_remove_update(name):
    with open("updates.csv", "r") as f:
        original_len_file = len(f.readlines())
    cancel_stored_update(name)
    with open("updates.csv", "r") as f:
        new_len_file = len(f.readlines())
    assert new_len_file == original_len_file-1

def test_remove_non_existent_event():
    event_scheduler = scheduler(time.time, time.sleep)
    try:
        event_scheduler.cancel("hehehehe")
    except ValueError:
        logging.error("ERROR: event cancelled does not exist.")

def test_delay():
    current_time = datetime.now().time()
    alarm_time = current_time.replace(minute=current_time.minute+1)
    delay = abs(current_time.hour - alarm_time.hour) * 3600 + abs(current_time.minute - alarm_time.minute) * 60 - current_time.second
    assert delay < 60

def test_str_to_datetime():
    temp = "14:30"
    current_time = datetime.now()
    alarm_time = current_time.replace(
        hour=int(temp.split(":")[0]),
        minute=int(temp.split(":")[1])
    )
    assert current_time != alarm_time

def update_test(event_scheduler):
    delay = 10
    repeat = False
    event_id = event_scheduler.enter(delay, 1, update_covid_data, argument=("name", repeat,))
    assert event_scheduler.queue != []
    event_scheduler.cancel(event_id)

def main():
    event_scheduler = scheduler(time, sleep)
    update_test(event_scheduler)



if __name__ == "__main__":
    main()
