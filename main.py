import logger_setup
import open_tv
import open_entry_chart
import get_alert_data
import local_db
import resources.symbol_settings as symbol_settings
from datetime import timedelta, datetime
import send_to_socials.send_to_discord as send_to_discord
from time import time
from time import sleep

main_logger = logger_setup.setup_logger(__name__, logger_setup.logging.DEBUG) # Set up logger for this file
REMOVE_LOG = True # remove the content of the log file (to clean it up)
INDICATOR_SHORT = 'Get Exits'
INDICATOR_NAME = 'Get Exits'
INTERVAL_MINUTES = 2 # number of mins to wait until inactive alerts get reactivated
DAYS = 10 # all the entries within this timespan will be retrieved

# Clean up the log
if REMOVE_LOG:
    with open('app_log.log', 'w') as file:
        pass

# All the collections
collections = ['Indian Stocks', 'US Stocks', 'Crypto', 'Currencies', 'Indices']

# Code that i need just in case
# 
# result = db.db[col].update_many({}, {"$set": {"sl_hit": False, "tp1_hit": False, "tp2_hit": False, "tp3_hit": False}})

# # Output the result of the update operation
# print(f"Documents modified: {result.modified_count}")


# Run main code
if __name__ == '__main__':
    try:
        # Just a seperator to make the log look readable
        main_logger.info('***********************************************************************************')

        # initiate Browser
        browser = open_tv.Browser(True, INDICATOR_SHORT, INDICATOR_NAME)

        # setup the indicators, alerts etc.
        setup_check = browser.setup_tv()

        if setup_check:
            main_logger.info('Setup Successful')
            db = local_db.Database()
            for col in collections: #Do this for all the collections
                # Retrieve entries
                entries = db.get_entries_in_timespan(col, db.get_unix_time(DAYS)) # multiply by 1000 to convert to milliseconds because the date field in the mongodb documents is in milliseconds. 

                # get the entries that are still open and have yet to hit their SL or TP levels
                entries = [entry for entry in entries if not entry['sl_hit'] and not entry['tp1_hit'] and not entry['tp2_hit'] and not entry['tp3_hit']]

                # Send each retrieved entry’s info into the indicator’s inputs
                open_chart = open_entry_chart.OpenChart(browser.driver)
                wins = 0 # total number of entries in this collection that hit any of their TP levels
                losses = 0 # total number of entries in this collection that hit any their SL levels
                for entry in entries:
                    # open the symbol and the timeframe
                    if open_chart.change_symbol(entry['symbol']) and open_chart.change_tframe(entry['tframe']):
                        sleep(1)

                        # open and change the indicator's settings
                        if open_chart.change_indicator_settings(browser.get_exits_shorttitle, int(entry['date']), float(entry['entry']), entry['direction'], float(entry['sl']), float(entry['tp1']), float(entry['tp2']), float(entry['tp3'])):
                        
                            # set an alert
                            if browser.set_alerts(int(entry['date']), float(entry['entry']), entry['direction'], float(entry['sl']), float(entry['tp1']), float(entry['tp2']), float(entry['tp3'])):

                                # wait for an alert to come
                                alert = get_alert_data.Alerts(browser.driver, open_chart, browser.get_exits_indicator, INTERVAL_MINUTES)
                                stats = alert.get_alert()

                                if stats:
                                    # update the entry with the stats
                                    tp1_hit = True if stats['tp1_hit'] == 'true' else False
                                    tp2_hit = True if stats['tp2_hit'] == 'true' else False
                                    tp3_hit = True if stats['tp3_hit'] == 'true' else False
                                    sl_hit = True if stats['sl_hit'] == 'true' else False

                                    db.db[col].update_one({'_id': entry['_id']}, {'$set': {'tp1_hit': tp1_hit, 'tp2_hit': tp2_hit, 'tp3_hit': tp3_hit, 'sl_hit': sl_hit}})

                                    # update the number of wins and losses
                                    if sl_hit: 
                                        losses = losses + 1 

                                    if tp1_hit or tp2_hit or tp3_hit: 
                                        wins = wins + 1 

                                    # take a snapshot
                                    if tp1_hit or tp2_hit or tp3_hit or sl_hit:
                                        snapshot_link = alert.post()
                                        if snapshot_link:
                                            # add the link to the document
                                            db.db[col].update_one({'_id': entry['_id']}, {'$set': {'exit_snapshot': snapshot_link}})

                                            # send the message to Discord
                                            discord = send_to_discord.Discord()
                                            symbol = entry['symbol']
                                            category = symbol_settings.symbol_category(symbol)
                                            word = 'hit' if sl_hit else ('gained' if tp1_hit or tp2_hit or tp3_hit else 'none')
                                            exit_type = 'Stop Loss' if sl_hit else ('3%' if tp3_hit else '2%' if tp2_hit else '1%' if tp1_hit else 'none')
                                            content = f"{entry['direction']} trade in {symbol} {word} {exit_type}. Link: {snapshot_link}"
                                            discord.create_msg(category, content) 

                                # delete the alert
                                browser.delete_all_alerts()
                                

    except Exception as e:
        main_logger.exception(f'Error in main.py:')
 