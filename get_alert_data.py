'''
This handles getting the alert and the alert message, removing it from the log, restarting inactive alerts and posting entry snapshots everywhere.
'''

# import modules
import logger_setup
import open_entry_chart
from datetime import datetime
from traceback import print_exc
from resources.symbol_settings import symbol_category
import send_to_socials.send_to_discord as send_to_discord
import database.nk_db as nk_db
import database.local_db as local_db
from time import sleep, time
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.common.exceptions import TimeoutException, StaleElementReferenceException
from json import loads

# Set up logger for this file
alert_data_logger = logger_setup.setup_logger(__name__, logger_setup.logging.DEBUG)

# class
class Alerts:

  def __init__(self, driver, get_exits_indicator) -> None:
    self.driver = driver
    self.local_db = local_db.Database('')
    self.nk_db = nk_db.Post()
    self.discord = send_to_discord.Discord()
    self.get_exits_indicator = get_exits_indicator
    self.last_run = time()
    self.get_alert_log()
    
  def post(self, msg, screener_visibility):
    '''This goes through every entry in `msg` and takes a snapshot of those entries and posts them to Nk uncle's database, our remote database & Discord'''
    try:
      if not screener_visibility(False, self.screener_shortitle): # hide the screener indicator with the passed in function
        alert_data_logger.warning('Failed to hide the screener indicator but still continuing to post about entries')
    
      for key, value in msg.items(): # go over every json field in this specific alert message
        try:
          # get all the data from the message
          timeframe = value['timeframe']
          entry_time = datetime.fromtimestamp(float(value['entryTime'])).strftime('%Y-%m-%d %H:%M')
          entry_price = value['entryPrice']
          sl_price = value['slPrice']
          tp1_price = value['tp1Price']
          tp2_price = value['tp2Price']
          tp3_price = value['tp3Price']
          direction = value['direction']

          # go to that specific entry's symbol and its timeframe. Then it inputs all the entry info into the Trade Drawer indicator
          if not self.chart.change_symbol(key):
            alert_data_logger.error(f'Error in changing the symbol to {key}. Going to next symbol.')
            continue
          if not self.chart.change_tframe(self.chart_timeframe):
            alert_data_logger.error(f'Error in changing the timeframe to {timeframe}. Going to next symbol.')
            continue
          if not self.chart.change_indicator_settings(self.drawer_indicator, entry_time, entry_price, sl_price, tp1_price, tp2_price, tp3_price):
            alert_data_logger.error(f'Error in changing the Trade Drawer indicator\'s settings. Going to next symbol.')
            continue

          # take a snapshot of the entry's chart, create a discord message and send it to Discord. Then, send all the entry's info to my database and Nishant uncle's database
          chart_link = self.chart.save_chart_img() 
          category = symbol_category(key)
          content = f"{direction} in {key} at {entry_price}. TP1: {tp1_price} TP2: {tp2_price} TP3: {tp3_price} SL: {sl_price} Link: {chart_link if chart_link != False else ''}"
          self.discord.create_msg(category, content) 
          self.send_to_db(value['type'], direction, key, timeframe, entry_price, tp1_price, tp2_price, tp3_price, sl_price, chart_link, content, entry_time, category, '')
        except Exception as e:
          alert_data_logger.exception(f'Error in posting an entry. Continuing to next entry. Error:')
          continue
    except Exception as e:
      alert_data_logger.exception('Error in posting an entry. Continuing to next entry. Error:')

  def restart_inactive_alerts(self):
    '''Restarts all the inactive alerts by going to the settings and clicking on "Restart all inactive". Then it will click "Yes" on the popup which comes to confirm the restarting of the alerts.'''
    try:
      # click the 3 dots
      WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[data-name="alerts-settings-button"]'))).click()
      
      # wait for the dropdown to show up
      dropdown = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-name="menu-inner"]')))
      
      # check if the "Show Alerts" section is minimised. if it is, maximise it
      show_all_section = dropdown.find_element(By.CSS_SELECTOR, 'div[class="section-xZRtm41u summary-ynHBVe1n"]')
      maximized = True if show_all_section.get_attribute('data-open') == 'true' else False
      if not maximized:
        show_all_section.click()
        alert_data_logger.info('Maximized the "Show Alerts" section')

      # then check if the "All" option is selected. if it is not, select it
      all_option = dropdown.find_element(By.CSS_SELECTOR, 'div[class="item-xZRtm41u item-jFqVJoPk"]')
      if not all_option.find_element(By.TAG_NAME, 'input').is_selected():
        all_option.click()
        alert_data_logger.info('Selected the "All" option')

      # then click on "Restart all inactive"
      dropdown_button = dropdown.find_element(By.CSS_SELECTOR, 'div[class="item-jFqVJoPk item-xZRtm41u withIcon-jFqVJoPk withIcon-xZRtm41u"]')

      if dropdown_button.text == 'Restart all inactive':
        # click Yes when the popup comes
        popup = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[class="dialog-qyCw0PaN popupDialog-B02UUUN3 dialog-aRAWUDhF rounded-aRAWUDhF shadowed-aRAWUDhF"]')))
        popup.find_element(By.CSS_SELECTOR, 'button[name="yes"]').click()
        alert_data_logger.info('Restarting all inactive alerts!')
        
      sleep(1)
      return True
    except Exception as e:
      alert_data_logger.exception('Error occurred when restarting the inactive alerts. Error:')
      return False
    
  def send_to_db(self, _type, direction, symbol, tframe, entry_price, tp1, tp2, tp3, sl, chart_link, content, date_time, symbol_type, exit_msg):
    '''This converts all arguments into a dictionary and sends that to Nk uncle's database and a local database'''
    data = {
      "type": _type,
      "direction": direction,
      "symbol": symbol,
      "tframe": tframe,
      "entry": entry_price,
      "tp1": tp1,
      "tp2": tp2,
      "tp3": tp3,
      "sl": sl,
      "chart_link": chart_link,
      "content": content,
      "date": date_time,
      "symbol_type": symbol_type,
      "exit_msg": exit_msg
    }

    self.local_db.add_doc(data, symbol_type)
    self.nk_db.post_to_url(data)

  def get_alert(self):
    '''As soon as an alert comes in the Alert log or whenever it sees an alert, the alert gets deleted from the log and its message gets returned'''
    start_time = time()
    while True:
      try:
        # Exit the loop if more than 10 seconds have passed
        current_time = time()  
        if current_time - start_time > 10: 
          return ''  

        # get the alert box and its message. 
        alert_msg = self.get_alert_box_and_msg()
        return alert_msg
      except Exception as e:
        alert_data_logger.exception('Error in reading the alert. Error:')

  def get_alert_msg(self):
    '''Returns the alert's message if there is an alert. If there is no alert, it waits for one. Also, it restarts all the inactive alerts periodically. If something goes wrong, `None` gets returned'''
    try:
      # restart all the inactive alerts every INTERVAL_MINUTES minutes (this is also done in get_alert_data.py in the method get_alert_box_and_msg())
      if time() - self.last_run > self.interval_seconds:
        self.restart_inactive_alerts()
        self.last_run = time()

      alert_boxes = WebDriverWait(self.driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[data-name="alert-log-item"]')))
      if alert_boxes:
        alert_msg = alert_boxes[-1].find_element(By.CSS_SELECTOR, 'div[class="message-PQUvhamm"]').text 
        return alert_msg
      return None
    except TimeoutException:
      alert_data_logger.error('TimeoutException occurred while waiting for an alert.')
      return None
    except Exception as e:
      alert_data_logger.exception('Error in getting the alert box and message. Error:')
      return None
  
  def remove_alert(self, alert_box):
    '''Removes the alert from the Alert log'''
    try:
      ActionChains(self.driver).move_to_element(alert_box).perform()
      remove_button = alert_box.find_element(By.CSS_SELECTOR, 'div[data-name="event-delete-button"]')
      remove_button.click()
      return True
    except Exception as e:
      alert_data_logger.exception('Error in removing the alert from the Alert log. Error:')
      return False
  
  def get_alert_log(self):
    '''makes an attribute called `self.alert_log` which has the alert log as a web element'''
    try:
      self.alert_log = self.driver.find_element(By.CSS_SELECTOR, 'div[class="widget-X9EuSe_t widgetbar-widget widgetbar-widget-alerts_log"]')
      return True
    except Exception as e:
      alert_data_logger.exception('Error in getting the alert log. Error:')
      return False
    
  def scroll_to_alert(self, alert):
    '''This scrolls to the given alert'''
    try:
      self.driver.execute_script("arguments[0].scrollIntoView();", alert)
      return True
    except Exception as e:
      alert_data_logger.exception('Error in scrolling to the alert. Error:')
      return False