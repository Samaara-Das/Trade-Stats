import logger_setup
import open_tv
import open_entry_chart
import get_alert_data
import local_db
from time import time
from time import sleep

main_logger = logger_setup.setup_logger(__name__, logger_setup.logging.DEBUG) # Set up logger for this file
REMOVE_LOG = True # remove the content of the log file (to clean it up)
INDICATOR_SHORT = 'Get exits'
INDICATOR_NAME = 'Get exits'

# Clean up the log
if REMOVE_LOG:
    with open('app_log.log', 'w') as file:
        pass

# Run main code
if __name__ == '__main__':
    try:
        # Just a seperator to make the log look readable
        main_logger.info('***********************************************************************************')

        # Retrieve entries
        db = local_db.Database()
        entries = db.get_docs('entries', db.get_unix_time(30)*1000) # multiply by 1000 to convert to milliseconds because the date field in the mongodb documents is in milliseconds. 

        # initiate Browser
        browser = open_tv.Browser(True, INDICATOR_SHORT, INDICATOR_NAME)

        # setup the indicators, alerts etc.
        setup_check = browser.setup_tv()

        # Send each retrieved entry’s info into the indicator’s inputs
        open_chart = open_entry_chart.OpenChart(browser.driver)
        for entry in entries:
            # open and change the indicator's settings
            open_chart.change_settings(int(entry['date']), float(entry['entry']), entry['type'], float(entry['sl']), float(entry['tp1']), float(entry['tp2']), float(entry['tp3']))
            
            # set an alert
            browser.set_alerts(int(entry['date']), float(entry['entry']), entry['type'], float(entry['sl']), float(entry['tp1']), float(entry['tp2']), float(entry['tp3']))

            # wait for an alert to come
            alert = get_alert_data.Alerts(browser.driver, browser.get_exits_indicator).get_alert()
            



    except Exception as e:
        main_logger.exception(f'Error in main.py:')
 