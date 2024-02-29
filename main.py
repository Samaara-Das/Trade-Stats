import logger_setup
import open_tv
import open_entry_chart
import get_alert_data
import local_db
from datetime import timedelta, datetime
import pytz
from time import time
from time import sleep

main_logger = logger_setup.setup_logger(__name__, logger_setup.logging.DEBUG) # Set up logger for this file
REMOVE_LOG = True # remove the content of the log file (to clean it up)
INDICATOR_SHORT = 'Get Exits'
INDICATOR_NAME = 'Get Exits'
START_FRESH = False

# Clean up the log
if REMOVE_LOG:
    with open('app_log.log', 'w') as file:
        pass

# All the collections
collections = ['Currencies', 'US Stocks', 'Indian Stocks', 'Crypto', 'Indices']

# Run main code
if __name__ == '__main__':
    try:
        # Just a seperator to make the log look readable
        main_logger.info('***********************************************************************************')
        # db = local_db.Database()

        # to set up the entries in mongodb to use them for testing
        # result = db.db['entries'].update_many({}, {'$set': {'tframe': '1 hour'}})

        # Query to add a field and rename a field in all documents in a collection
        # for col_ in collections:
        #     col = db.db[col_]
        #     docs = col.find({})
        #     for doc in docs:
        #         update_query = {
        #             '$set': {'exit_snapshot': ''},  # Assuming you want to initialize it with None
        #             '$rename': {'chart_link': 'entry_snapshot'}
        #         }

        #         # Apply the update to all documents in the collection
        #         result = col.update_many({}, update_query)

        # initiate Browser
        browser = open_tv.Browser(True, INDICATOR_SHORT, INDICATOR_NAME)

        # setup the indicators, alerts etc.
        setup_check = browser.setup_tv()

        for col in collections: #Do this for all the collections
            # Retrieve entries
            db = local_db.Database()
            entries = db.get_entries_in_timespan(col, db.get_unix_time(3)*1000) # multiply by 1000 to convert to milliseconds because the date field in the mongodb documents is in milliseconds. 

            # Send each retrieved entry’s info into the indicator’s inputs
            open_chart = open_entry_chart.OpenChart(browser.driver)
            for entry in entries:
                # open the symbol and the timeframe
                if open_chart.change_symbol(entry['symbol']) and open_chart.change_tframe(entry['tframe']):
                    sleep(1)

                    # open and change the indicator's settings
                    if open_chart.change_indicator_settings(browser.get_exits_indicator, int(entry['date']), float(entry['entry']), entry['direction'], float(entry['sl']), float(entry['tp1']), float(entry['tp2']), float(entry['tp3'])):
                    
                        # set an alert
                        if browser.set_alerts(int(entry['date']), float(entry['entry']), entry['direction'], float(entry['sl']), float(entry['tp1']), float(entry['tp2']), float(entry['tp3'])):

                            # wait for an alert to come
                            alert = get_alert_data.Alerts(browser.driver, browser.get_exits_indicator).get_alert()

                            # read it
                            # if alert == 'TP1 hit' or alert == 'TP2 hit' or alert == 'TP3 hit':
                            #     entry['tp_hit'] = True
                            
                            # if alert == 'SL hit':
                            #     entry['sl_hit'] = True

            # Get the total wins and losses
            wins = len([d for d in db.find_docs(col, 'tp_hit', True)])
            losses = len([d for d in db.find_docs(col, 'sl_hit', True)])

    except Exception as e:
        main_logger.exception(f'Error in main.py:')
 