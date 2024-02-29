'''
this can change the Trade Drawer's settings, change the chart's symbol and timeframe and take a snapshot of the chart.
'''

# import modules
import logger_setup
from time import sleep, time
from traceback import print_exc
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains

# Set up logger for this file
entry_chart_logger = logger_setup.setup_logger(__name__, logger_setup.logging.DEBUG)

# class
class OpenChart:

  def __init__(self, driver) -> None:
    self.driver = driver
    
  def change_indicator_settings(self, get_exits_indicator, entry_time, entry_price, entry_type, sl_price, tp1_price, tp2_price, tp3_price):
    '''This double clicks on the Get Exits indicator to open its settings and changes its inputs'''
    try:
      # double click on the indicator so that the settings can open 
      i = 1
      while i <= 3:
        try:
          ActionChains(self.driver).move_to_element(get_exits_indicator).perform()
          ActionChains(self.driver).double_click(get_exits_indicator).perform()
          settings = WebDriverWait(self.driver, 5).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-name="indicator-properties-dialog"]')))
          break
        except Exception as e:
          entry_chart_logger.exception('Failed to open the Trade Drawer\'s settings. Error:')
          i += 1
          if i == 4:
            entry_chart_logger.error('Trade Drawer indicator\'s settings failed to open. Could not change the settings. Exiting function.')
            return False
        
      # when the settings come up, click on the Inputs tab (just in case we’re on some other tab)
      settings.find_element(By.CSS_SELECTOR, 'div[class="tabs-vwgPOHG8"] button[id="inputs"]').click()

      # fill up the settings
      inputs = settings.find_elements(By.CSS_SELECTOR, '.cell-tBgV1m0B input')
      for i in range(len(inputs)):
        val = 0
        if i == 0:
          val = entry_time
        elif i == 1:
          val = entry_price
        elif i == 2:
          val = entry_type
        elif i == 3:
          val = sl_price
        elif i == 4:
          val = tp1_price
        elif i == 5:
          val = tp2_price
        elif i == 6:
          val = tp3_price

        ActionChains(self.driver).key_down(Keys.CONTROL, inputs[i]).send_keys('a').perform()
        inputs[i].send_keys(Keys.DELETE)
        inputs[i].send_keys(val)

      entry_chart_logger.info(f'Trade Drawer\'s settings changed. Inputs: entry_time - {entry_time}, entry_price - {entry_price}, entry_type - {entry_type}, sl_price - {sl_price}, tp1_price - {tp1_price}, tp2_price - {tp2_price}, tp3_price - {tp3_price}')

      # click on submit
      self.driver.find_element(By.CSS_SELECTOR, 'button[name="submit"]').click()
      return True
    except Exception as e:
      entry_chart_logger.exception('Failed to change the Trade Drawer\'s settings. Error:')
      return False

  def change_symbol(self, symbol):
    '''This changes the chart's symbol to `symbol` if it is any other symbol. Then it waits for 1.5 secs for the chart to load'''
    try:
      symbol_search = WebDriverWait(self.driver, 15).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[id="header-toolbar-symbol-search"]')))
      if not symbol_search.find_element(By.CSS_SELECTOR, 'div').text == symbol: # only search for a specific symbol if the current symbol is different from that symbol
        # click on Symbol Search and search for a specific symbol and hit ENTER
        symbol_search.click()
        search_input = self.driver.find_element(By.XPATH, '//*[@id="overlap-manager-root"]/div/div/div[2]/div/div[2]/div[1]/input')
        search_input.send_keys(symbol)
        search_input.send_keys(Keys.ENTER)
        entry_chart_logger.info(f'Entered symbol {symbol}') 
        WebDriverWait(self.driver, 5).until(EC.text_to_be_present_in_element((By.CSS_SELECTOR, 'button[id="header-toolbar-symbol-search"] div'), symbol))
        sleep(1.5) # wait for the chart to load
        return True
      else:
        entry_chart_logger.info(f'The current symbol is the same as {symbol}. There is no need to change the symbol!')
        return True
    except Exception as e:
      entry_chart_logger.exception(f'Failed to change the symbol of the chart. Error: ')
      return False

  def change_tframe(self, timeframe):
    '''Changes the timeframe of the chart to `timeframe`'''
    try:
      # click on the timeframe dropdown and choose from the dropdown options and click on the one which matches the timeframe
      tf_button = WebDriverWait(self.driver, 15).until(EC.element_to_be_clickable((By.XPATH, '//*[@id="header-toolbar-intervals"]/button')))

      if tf_button.get_attribute('aria-label') != timeframe: # if the chart's timeframe is different, change it to the desired timeframe
        tf_button.click()
        options = WebDriverWait(self.driver, 15).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[class="dropdown-S_1OCXUK"]')))
        options = options.find_elements(By.CSS_SELECTOR, 'div[class="accessible-NQERJsv9 menuItem-RmqZNwwp item-jFqVJoPk"]')

        for option in options:
          if option.find_element(By.CSS_SELECTOR, 'span[class="label-jFqVJoPk"]').text == timeframe:
            option.click()
            entry_chart_logger.info(f'Successfully changed the timeframe to {timeframe}!')
            return True
      
      elif tf_button.get_attribute('aria-label') == timeframe: # if the chart's timeframe is already the desired timeframe
        entry_chart_logger.info('No need to change the timeframe as the current chart is already on that timeframe!')
        return True
      
      return False
    except Exception as e:
      entry_chart_logger.exception(f'Failed to change the timeframe of the chart to {timeframe}. Error:')
      return False
                                               
  def save_chart_img(self):
    '''Clicks on the camera icon to take a snapshot of the chart and opens it in a new tab. Then it gets the link of the tab and closes it. The link gets returned. If an error happens, an empty string is returned.'''
    url = ''
    try:
      camera = WebDriverWait(self.driver, 20).until(EC.element_to_be_clickable((By.XPATH, "//button[@aria-label='Take a snapshot']/div[@id='header-toolbar-screenshot']")))

      # copy the link of the chart
      camera.click()
      open_in_new_tab = self.driver.find_element(By.XPATH, '//*[@id="overlap-manager-root"]/div/span/div[1]/div/div/div[5]')
      open_in_new_tab.click()
      entry_chart_logger.info(f'Took a snapshot and opened it in new tab.')

      # get the url of the newly opened tab after it has fully loaded
      self.driver.switch_to.window(self.driver.window_handles[-1])
      WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'img[class="tv-snapshot-image"]')))
      url = self.driver.current_url
      entry_chart_logger.info(f'Got url of the snapshot: {url}')

      # close the new tab 
      self.driver.close()

      # switch back to the original tab
      self.driver.switch_to.window(self.driver.window_handles[0])
    except Exception as e:
      entry_chart_logger.exception('Failed to save the chart image. Error:')
      return ''
    
    return url