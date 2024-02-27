import os
import requests 
import json
from datetime import datetime, timedelta, timezone

from google.oauth2 import service_account
from googleapiclient.discovery import build
from dotenv import load_dotenv

def load_credentials(secret_file_path, scopes):
    """Loads credentials if secret_file_path is correct.

    Args:
        secret_file_path: path to json credentials file of service account
        scopes: scopes to authorize credential. (calendar)

    Returns:
        credentials: google.oauth2.service_account.Credentials object

    Raises:
        Exception: Possibly a "FileNotFoundError", but might be connection err.
    """
    try:
        credentials = service_account.Credentials.from_service_account_file(secret_file_path, scopes=scopes)

        return credentials
    except Exception as error:
        raise error


def google_calendar_service(credentials):
    """Creates service for Google Calendar based on given credentials."""
    try:
        service = build('calendar', 'v3', credentials=credentials)
    except Exception as error:
        raise error

    return service

def read_events(service, calendar_id, since='2024-01-01T00:00:00Z'):
    """Reads and returns all events on the calendar since specified date."""
    try:
        response = service.events().list(calendarId=calendar_id, timeMin=since).execute()
        events = response.get('items', [])

        return events
    except Exception as error:
        print(error)

def read_database(notion_api_key, database_id):
    """Reads entries of specified database"""

    database_url = f"https://api.notion.com/v1/databases/{database_id}/query"
    api_headers = {"Authorization": "Bearer " + notion_api_key, "Notion-Version": "2022-06-28"}
    response = requests.request("POST", database_url, headers=api_headers)

    return response


def parse_events(events):
    """Parses events on Google Calendar.

    In order to check its content and status, each event must be parsed
    into a predefined structure.

    Args:
        events: all events returned from read_events() func.

    Returns:
        parsed_events: a dictionary of structured events. Key is task ID.
        err: a list of could not structured events with Exception info
    """
    parsed_events = {}
    err = []
    for elem in events:
        try:
            tmp = {}
            tmp['event_id'] = elem['id']  # ID required in deletion and update
            # Parse details of tasks into predefined structure
            tmp['subject'] = elem['summary']
            # Description includes rest of the data related to a task.
            # Description is parsed into relevant keys
            description = elem['description'].strip().split('\n')  # Split description
            tmp['description'] = description[0].split(":")[1].strip()
            tmp['notes'] = description[1].split(":")[1].strip()
            tmp['category'] = description[2].split(":")[1].strip()
            tmp['assignment_date'] = description[3].split(":")[1].strip()
            dueDate = elem['end']['dateTime'].split('T')  # Split dueDate to date, time
            tmp['due_date'] = dueDate[0]  # DueDate of created event
            tmp['due_hour'] = dueDate[1]  # DueHour of created event
            # Get task specific database information
            tmp['last_edited_time'] = description[-2].strip()
            tmp['task_id'] = description[-1].strip()
            parsed_events[tmp['task_id']] = tmp
        except Exception as error:
            err.append([elem, error])

    return parsed_events, err


def task_to_event(task):
    """Converts task to required event structure of Google Calendar

    Google API requires a body to create, update, and delete events.
    This function constructs the required body based on task information.

    Args:
        task: Parsed task

    Returns:
        event: An event body to use in API calls
    """
    try:
        event_start = str_to_date(task['due_date'], task['due_hour'], task['user_time_zone'])  # Start datetime
    except Exception as error:
        print(error)
        event_start = datetime.now()
    
    event_finish = event_start + timedelta(minutes=30)  # Finish datetime

    description = 'Description: ' + task['description'] + '\n' \
        + 'Notes: ' + task['notes'] + '\n' \
        + "Category: " + task['category'] + '\n' \
        + "Assignment Date: " + task['assignment_date'] +  ' - ' + task['assignment_hour'] + '\n' \
        + '----------' + '\n' \
        + 'Please do not edit following lines!' + '\n' \
        + task['last_edited_time'] + '\n' \
        + task['task_id'] + '\n'
    
    event = {'summary': task['name'],
             'description': description,
             'start': {'dateTime': event_start.astimezone().isoformat()},
             'end': {'dateTime': event_finish.astimezone().isoformat()},
             'reminders': {
                 'useDefault': False,
                 'overrides': [
                     {'method': 'popup', 'minutes': 24*60},
                     {'method': 'popup', 'minutes': 30},
                 ],
    },
    }

    return event


def str_to_date(date, hour, user_time_zone):
    """Converts str type date and hour to datetime object

    Datetime object provides operations. This package converts the datetime string
    into a datetime object to get the correct dueDate and dueHour. All dates should
    be in `isoformat`.

    Args:
        date: YYYY-MM-DD,  Y=Year, M=Month, D=Day, formatted date string
        hour: HH:MM:SS, H=Hour, M=Minute, S=Seconds, formatted hour string

    Returns:
        date_time_obj: a datetime.datetime object
    """
    due_date = [int(x) for x in date.split('-')]
    due_hour = [int(x) for x in hour.split(':')]
    user_time_zone_hours, user_time_zone_minutes = user_time_zone.split(":")
    user_time_zone = timezone((timedelta(hours=int(
        user_time_zone_hours)) + timedelta(minutes=int(user_time_zone_minutes))))
    # Year, month, day, hour, minute, seconds
    date_time_obj = datetime(due_date[0], due_date[1], due_date[2],
                             due_hour[0], due_hour[1], due_hour[2],
                             tzinfo=user_time_zone)

    return date_time_obj

def parse_tasks_in_database(db_response):
    results = db_response.json()['results']
    parsed_tasks = {}
    err = []
    # properties = ['Name', 'Description', 'Notes', 'Category', 'Assignment Date', 'Due Date']
    for elem in results:
        # check whether status is specified or not. If not specified print it and move to next package
        try:
            package_status = elem['properties']['Status']['select']['name']
        except Exception as error:
            print(error)
            print("Missconfigured Task: ", elem['url'])
            continue

        if package_status not in ['Completed', 'Closed', 'Failed']:
            try:
                tmp = {}
                # Get unique DB ID record in Notion
                tmp['task_id'] = elem['id']

                if elem['properties']['Name']['title']:
                    # Get title of the task
                    tmp['name'] = elem['properties']['Name']['title'][0]['plain_text']
                else:
                    tmp['name'] = "Title is not specified!"

                if elem['properties']['Description']['rich_text']:
                    #  Get description of the task
                    tmp['description'] = elem['properties']['Description']['rich_text'][0]['plain_text']
                else:
                    tmp['description'] = "Description is empty!"

                if elem['properties']['Notes']['rich_text']:
                    # Get notes if any
                    tmp["notes"] = elem['properties']['Notes']['rich_text'][0]['plain_text']
                else:
                    tmp['notes'] = "Notes are empty!"

                if len(elem['properties']['Category']['multi_select']) != 0:
                    tmp['category'] = ", ".join(
                        [a['name'] for a in elem['properties']['Category']['multi_select']])
                else:
                    tmp['category'] = ["Not categorized!"]

                if elem['properties']['Assignment Date']['date']['start'] != type(None):
                    assignment_date = elem['properties']['Assignment Date']['date']['start'].split('T')
                    if len(assignment_date) == 2:
                        tmp['assignment_date'] = assignment_date[0] # YYYY-MM-DD
                        tmp['assignment_hour'] = assignment_date[1].split('.')[0] # HH:MM:SS
                        tmp['user_time_zone'] = assignment_date[1].split('+')[1] #  HH:MM
                    else:
                        tmp['assignment_date'] = assignment_date[0] # YYYY-MM-DD
                        tmp['assignment_hour'] = "00:00"
                        tmp['user_time_zone'] = ""
                else:
                    tmp['assignment_date'] = "Assignment date is missing!"

                if type(elem['properties']['Due Date']['date']['start']) != type(None):
                    due_date = elem['properties']['Due Date']['date']['start'].split('T')
                    if len(due_date) == 2:
                        tmp['due_date'] = due_date[0] # YYYY-MM-DD
                        tmp['due_hour'] = due_date[1].split('.')[0] # HH:MM:SS
                        tmp['user_time_zone'] = due_date[1].split('+')[1] #  HH:MM
                    else:
                        tmp['due_date'] = due_date[0] # YYYY-MM-DD
                        tmp['due_hour'] = "12:00:00"
                        if tmp['user_time_zone'] == "":
                            tmp['user_time_zone'] = "00:00"

                else:  # dueHour has no effect on time even if it is specified
                    tmp['assignment_date'] = "DUE DATE IS NOT SPECIFIED. TASK IS CREATED ON CREATION TIME!"
                    tmp['due_date'] = elem['created_time'].split('T')[0]
                    tmp['due_hour'] = elem['created_time'].split('T')[1].split('.')[0]

                tmp['last_edited_time'] = elem['last_edited_time']
                parsed_tasks[tmp['task_id']] = tmp

            except Exception as error:
                print(elem['url'], error)
                err.append([elem, error])

    return parsed_tasks, err


def to_create(task, service, calendar_id):
    """Creates an event for task via service on specifiedcalendar_id

    Google API enables configuration of events via a service built with
    Google Calendar API ['https://www.googleapis.com/auth/calendar'] scope.
    This function creates an event on the calendar specified  with `calendar_id`;
    based on given task (task), by using previously built service which
    includes Google Calendar API scope.

    Args:
        task: One of the elements of parsed tasks
        service: Google API service built with Calendar scope
        calendar_id: Calendar ID of Google Calendar

    Returns:
        str(e): If an error occurs during the process, it will be returned.

    ToDo: Return a value for success insted of printing
    """
    task = task
    event = task_to_event(task)
    try:
        response = service.events().insert(calendarId=calendar_id, body=event).execute()
        print('Event %s created at: %s' % (event['summary'], response.get('htmlLink')))
    except Exception as error:
        return str(error)


def to_delete(parsed_event, service, calendar_id):
    """Deletes given parsed_event from calendar using previously built service.

    Google API enables configuration of events via a service built with
    Google Calendar API ['https://www.googleapis.com/auth/calendar'] scope.
    This function deletes an event on the calendar specified  with `event_id`;
    based on a given event (parsed_event), by using previously built service
    which includes Google Calendar API scope.

    Args:
        parsed_event: One of the elements of parsed_events
        service: Google API service built with Calendar scope
        calendar_id: Calendar ID of Google Calendar

    Returns:
        str(e): If an error occurs during the process, it will be returned.

    ToDo: Return a value for success insted of printing
    """
    event_id = parsed_event['event_id']
    subject = parsed_event['subject']
    try:
        service.events().delete(calendarId=calendar_id, eventId=event_id).execute()
        print('task: {} has been deleted'.format(subject))
    except Exception as error:
        return str(error)


def may_update(task, parsed_event, service, calendar_id):
    """Updates task on calendar if there is an update.

    Google API enables configuration of events via a service built with
    Google Calendar API ['https://www.googleapis.com/auth/calendar'] scope.
    This function updates an event on the calendar specified  with `event_id`;
    based on a given event (parsed_event), by using previously built service
    which includes Google Calendar API scope if there is any update.

    Args:
        task: One of the elements of parsed tasks
        parsed_event: One of the elements of parsed_events
        service: Google API service built with Calendar scope
        calendar_id: Calendar ID of Google Calendar

    Returns:
        str(e): If an error occurs during the process, it will be returned.

    ToDo: Return a value for success insted of printing
    """
    if task['last_edited_time'] != parsed_event['last_edited_time']:
        tmp = task_to_event(task)
        event_id = parsed_event['event_id']
        try:
            updated_event = service.events().update(calendarId=calendar_id, eventId=event_id, body=tmp).execute()
            print('Event %s has been updated' % updated_event['summary'])
        except Exception as error:
            return str(error)


def synchronize_tasks(parsed_tasks, parsed_events, service, calendar_id):
    """Synchronizes Notion tasks with Google Calendar events

    After loading and parsing all tasks and events, this function is
    called to synchronize events on Google Calendar. For each task
    there are three possible actions: (i) It should be created, (ii) It is
    already created but its content requires an update, and (iii) task is
    closed or deleted, so it should be removed from the calendar.

    Args:
        parsed_tasks: a dictionary of structured tasks. Key is task ID.
        parsed_events: a dictionary of structured events. Key is task ID.
        service: Authorized Google Calendar API service
        calendar_id: Id of the Calendar which tasks are synchronized.

    Returns:
        task_ids: classified task_ids as create, delete or update
        err: Faced errors during creation, deletion or update
    """
    tasks_on_notion = set(parsed_tasks.keys())
    tasks_on_calendar = set(parsed_events.keys())
    # Decide which packages to create, to delete and may update
    to_create_set = tasks_on_notion.difference(tasks_on_calendar)
    to_delete_set = tasks_on_calendar.difference(tasks_on_notion)
    may_update_set = tasks_on_calendar.intersection(tasks_on_notion)
    to_create_err, to_delete_err, may_update_err = [], [], []

    # Iterate over each task
    for task_id in to_create_set:
        err = to_create(parsed_tasks[task_id], service, calendar_id)
        to_create_err.append(err)

    for task_id in to_delete_set:
        err = to_delete(parsed_events[task_id], service, calendar_id)
        to_delete_err.append(err)

    for task_id in may_update_set:
        task, event = parsed_tasks[task_id], parsed_events[task_id]
        err = may_update(task, event, service, calendar_id)
        may_update_err.append(err)

    task_ids = [to_create_set, to_delete_set, may_update_set]
    error = [to_create_err, to_delete_err, may_update_err]

    return [task_ids, error]

if __name__ == "__main__":
    load_dotenv()

    # Notion API token and Database ID.
    NOTION_API_KEY = os.getenv("NOTION_API_KEY")
    NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

    # Google Calendar and Calendar API Configurations
    GOOGLE_SERVICE_ACCOUNT_SECRET_FILE = os.getenv("GOOGLE_SERVICE_ACCOUNT_SECRET_FILE")
    GOOGLE_API_SCOPE = os.getenv("GOOGLE_API_SCOPE")
    GOOGLE_CALENDAR_ID = os.getenv("GOOGLE_CALENDAR_ID")
    READ_CALENDAR_SINCE=os.getenv("READ_CALENDAR_SINCE")
    SCOPES = [GOOGLE_API_SCOPE]

    # Load Google API credentials
    credentials = load_credentials(GOOGLE_SERVICE_ACCOUNT_SECRET_FILE, SCOPES)
    
    # Start google calendar service
    calendar_service = google_calendar_service(credentials)

    # NOTION
    # Read tasks on Notion
    database_response = read_database(NOTION_API_KEY, NOTION_DATABASE_ID)
    # Parse tasks to start synchronization
    parsed_tasks, err = parse_tasks_in_database(database_response)
    
    # Google Calendar
    # Read events from calendar
    all_events = read_events(calendar_service, GOOGLE_CALENDAR_ID, since=READ_CALENDAR_SINCE)
    # Parse events
    parsed_events, gc_err = parse_events(all_events)
    
    # SYNCHRONIZE!
    tasks, errors = synchronize_tasks(parsed_tasks, parsed_events, calendar_service, GOOGLE_CALENDAR_ID)

    print('Synchronization has been completed at %s!' %datetime.today().isoformat())
