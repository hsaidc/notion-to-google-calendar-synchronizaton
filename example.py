import os
from datetime import datetime
from dotenv import load_dotenv

from src.notion2gcalendar import load_credentials, google_calendar_service, read_database, parse_tasks_in_database, read_events, parse_events, synchronize_tasks

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