import logger_setup
import open_tv
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
        entries = db.get_docs('entries', db.get_unix_time(0))

        # initiate Browser
        browser = open_tv.Browser(True, INDICATOR_SHORT, INDICATOR_NAME)

        # setup the indicators, alerts etc.
        setup_check = browser.setup_tv()

        # set up alerts for all the symbols
        browser.set_bulk_alerts()

        if setup_check and browser.init_succeeded:
            last_run = time()
            while True:
                # restart all the inactive alerts every INTERVAL_MINUTES minutes (this is also done in get_alert_data.py in the method get_alert_box_and_msg()) and refresh browser
                if time() - last_run > interval_seconds:
                    # clear_cache()
                    browser.alerts.restart_inactive_alerts()
                    last_run = time()

                # get entries from the alerts which come and post them
                alert = browser.alerts.get_alert()
                browser.alerts.post(alert, browser.indicator_visibility)
    except Exception as e:
        main_logger.exception(f'Error in main.py:')
 