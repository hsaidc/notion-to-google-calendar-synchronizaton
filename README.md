# Notion to Google Calendar Task Synchronization

## Introduction

Efficient project management relies on keeping your tasks organized and readily accessible. However, managing tasks across different platforms can be inconvenient and time-consuming. This guide explains how to synchronize tasks from your **Notion** to Google Calendar. 

**Please duplicate the [example Notion database](https://hsaidcankurtaran.notion.site/9f8f881760014fe5ada0f2c9fe7c0906?v=819c5588e6df4f70baae8177bd10f6f4&pvs=4) to create your own. Changing column names will cause the script to fail.**

*This repository is a derivative of [Tapir Lab.'s Task Synchronization Repository](https://github.com/TapirLab/calendar-task-synchronization)*. Licenses are included.

## Benefits

- **Improved task visibility:** Centralize your tasks in one location for easier tracking.
- **Enhanced collaboration:** Share tasks and updates seamlessly with your team.
- **Streamlined workflow:** Reduce time spent switching between platforms.

## Required Services and Information to Execute Script

1. **Google Service Account:**

   - **Create a Google Cloud project:** https://developers.google.com/workspace/guides/create-project
   - **Enable Google Calendar API:** https://support.google.com/googleapi/answer/6158841?hl=en
   - **Create a service account:** https://cloud.google.com/iam/docs/service-accounts-create to access the Google Calendar API.
   - **Create a key and download the authentication file (secret file).**

2. **Google Calendar:**

   - **Create a new calendar** in your Google Calendar settings. **Important:** Do not use your main calendar! Create a new one **as all entries in the chosen calendar can be removed by this script.**

      <img src="https://github.com/hsaidc/notion-to-google-calendar-synchronizaton/blob/main/examples/create-google-calendar.png?raw=true" alt="Create Google Calendar" width="500"/>

   - **Add your service account to the calendar with "Make changes to events" permission.**

      <img src="https://github.com/hsaidc/notion-to-google-calendar-synchronizaton/blob/main/examples/adding-service-account-to-calendar.png?raw=true" alt="Create Google Calendar" width="500"/>


3. **Google Calendar ID:** Obtain the ID of your Google Calendar in Calendar settings. You can find the Calendar ID in the "Integrate Calendar" section of your Google Calendar settings.
    
    <img src="https://github.com/hsaidc/notion-to-google-calendar-synchronizaton/blob/main/examples/google-calendar-id.png?raw=true" alt="Google Calendar ID" width="500"/>

4. **Notion API key:** Generate an API key for Notion to access your data programmatically. Please read https://developers.notion.com/docs/create-a-notion-integration to learn how to create an API key. **Remember to add your integration to your database, as shown in the guide.**

5. **Notion database ID:**

   - Click the **Share** button located on the top right of the Notion window.

      <img src="https://github.com/hsaidc/notion-to-google-calendar-synchronizaton/blob/main/examples/notion-db-id.png?raw=true" alt="Google Calendar ID" width="500"/>
      
   - Copy the URL displayed in the dropdown menu. The URL will be in the format:

     ```
     [https://www.notion.so/](https://www.notion.so/)<your-notion-workspace>/<db-id>?v=...
     ```

   - Copy the text between `<your-notion-workspace>/` and `?v=`. This is the ID of your tasks database!

6. **Script uses Notion API version 2022-06-28.** This version is specified in the request headers. If you encounter a Notion API version error, please check https://developers.notion.com/reference/versioning.

## Requirements

1. Obtain the necessary credentials mentioned in the `Required Services and Information to Execute Script` section.
2. Copy the `.env.example` file as `.env` and fill in the missing values.
3. Install required packages: `pip install -r requirements.txt`
4. Execute the script: `python notion2gcalendar.py`
5. You can create a cron job to execute the script periodically.

## Resources

- **Notion API Documentation:** https://developers.notion.com/
- **Google Calendar API Documentation:** https://developers.google.com/calendar/api/v3/reference

## Additional Considerations

- **Implement robust error handling** to gracefully handle potential issues during synchronization.
- **Consider adding logging mechanisms** to track the script's execution and identify errors.
- **Ensure proper security measures** are in place when handling API keys and other sensitive information.
- **Future improvements:** Add options like "periodic" or "do not synchronize" to tasks.

## License

**Disclaimer:** This guide provides a general framework for task synchronization. Specific implementation details may vary depending on your database structure. **Do not change the titles of your database columns.** You can modify the code to personalize it for your own task database.

**License:** The software is licensed under the MIT License.