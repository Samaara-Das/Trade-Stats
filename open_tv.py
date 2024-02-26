'''
the main things that this does is:
opens Tradingview, sets it up, sets alerts for all the symbols, changes the layout, changes the screener's settings, creates an alert for the screener, changes the visibility of the indicators, deletes all the alerts and re-uploads the screener on the chart.

There are a few other things this does that are related to all the things mentioned above.
'''

# import modules
import get_alert_data
import logger_setup
from traceback import print_exc
from time import sleep, time
from open_entry_chart import OpenChart
from resources.symbol_settings import *
from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.wait import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
from selenium.common.exceptions import WebDriverException, TimeoutException

# Set up logger for this file
open_tv_logger = logger_setup.setup_logger(__name__, logger_setup.logging.DEBUG)

# some constants
SYMBOL_INPUTS = 5 #number of symbol inputs in the screener
USED_SYMBOLS_INPUT = "Used Symbols" # Name of the Used Symbols input in the Screener
LAYOUT_NAME = 'Exits' # Name of the layout for the screener
SCREENER_REUPLOAD_TIMEOUT = 15 # seconds to wait for the screener to show up on the chart after re-uploading it

CHROME_PROFILE_PATH = 'C:\\Users\\Puja\\AppData\\Local\\Google\\Chrome\\User Data'
# CHROME_PROFILE_PATH = 'C:\\Users\\pripuja\\AppData\\Local\\Google\\Chrome\\User Data'

# generator functions
def main_list_gen():
  '''A generator which yields the main list of each category. Eg: [['AAPL', 'TSLA'], ['KO', 'SHOP']] and [['EURUSD', 'XAUUSD'], ['USDJPY', 'GBPUSD']]'''
  for _, main_list in symbol_set.items():
    yield main_list

def symbol_sublist_gen():
  '''A generator which yields each sublist of the main list. Eg: ['USDJPY', 'EURUSD', 'XAUUSD']'''
  main_lists = main_list_gen()
  for main_list in main_lists:
    for sublist in main_list:
      yield sublist


# class
class Browser:

  def __init__(self, keep_open: bool, ind_shorttitle: str, ind_name: str) -> None:
    chrome_options = Options() 
    chrome_options.add_experimental_option("detach", keep_open)
    chrome_options.add_argument('--profile-directory=Profile 2')
    chrome_options.add_argument(f"--user-data-dir={CHROME_PROFILE_PATH}")
    self.driver = webdriver.Chrome(service=ChromeService(ChromeDriverManager().install()), options=chrome_options)
    self.get_exits_name = ind_name
    self.get_exits_shorttitle = ind_shorttitle
    self.init_succeeded = True

  def open_page(self, url: str):
    '''This opens `url` and maximizes the window'''
    try:
      self.driver.get(url)
      self.driver.maximize_window()
      return True
    except WebDriverException:
      open_tv_logger.exception(f'Cannot open this url: {url}. Error: ')
      return False 

  def setup_tv(self):
    '''This opens tradigview, changes the layout of the chart, opens the alert sidebar, deletes all alerts, gets access to the screener & trade drawer indicators, makes them both visible and changes the timeframe of the screener'''
    # open tradingview
    if not self.open_page('https://www.tradingview.com/chart'):
      if not self.open_page('https://www.tradingview.com/chart'): # try once more
        open_tv_logger.error(f'Failed to open tradingview. Exiting function')
        return False

    # change to the screener layout (if another layout is displayed)
    if not self.change_layout():
      self.change_layout() # try once more
      if self.current_layout() != LAYOUT_NAME:
        open_tv_logger.error(f'Cannot change the layout to {LAYOUT_NAME}. Exiting function')
        return False

    # open the alerts sidebar
    if not self.open_alerts_sidebar():
      self.open_alerts_sidebar() # try once more
      if not self.alerts_sidebar_open():
        open_tv_logger.error(f'Cannot open the alerts sidebar. Exiting function')
        return False

    # delete all alerts
    if not self.delete_all_alerts():
      self.delete_all_alerts() # try once more
      if not self.no_alerts():
        open_tv_logger.error(f'Cannot delete all alerts. Exiting function')
        return False

    # make the Get exits indicator into attributes of this object
    self.get_exits_indicator = self.get_indicator(self.get_exits_shorttitle)

    if self.get_exits_indicator is None: # try once more to find the screener
      self.get_exits_indicator = self.get_indicator(self.get_exits_shorttitle)

    if self.get_exits_indicator is None:
      open_tv_logger.error(f'"Get exits" indicator is not found. Exiting function.')
      return False
    
    # make the Get exits indicator visible
    if not self.indicator_visibility(True, self.drawer_shorttitle):
      self.indicator_visibility(True, self.drawer_shorttitle)
      if self.is_visible(self.drawer_shorttitle) == False:
        open_tv_logger.warning('Failed to make the Get exits indicator visible. The function will still continue on without exiting as this is not crucial.')
    
    #give it some time to rest
    sleep(1) 

    return True
        
  def change_layout(self):
    '''This changes the layout of the chart to `LAYOUT_NAME` if we are a different one. If we are on the same layout, it does nothing.'''
    try:
      # switch the layout if we are on some other layout. if we are on the screener layout, we don't need to do anything
      curr_layout = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="header-toolbar-save-load"]')))
      if curr_layout.find_element(By.CSS_SELECTOR, '.text-yyMUOAN9').text == LAYOUT_NAME:
        return True

      # click on the dropdown arrow
      WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, '/html/body/div[2]/div[3]/div/div/div[3]/div[1]/div/div/div/div/div[14]/div/div/button[2]'))).click()
      
      # choose the screener layout
      layouts = WebDriverWait(self.driver, 10).until(EC.presence_of_all_elements_located((By.XPATH, '//*[@id="overlap-manager-root"]/div/span/div[1]/div/div/a')))

      for layout in layouts:
        if layout.find_element(By.CSS_SELECTOR, '.layoutTitle-yyMUOAN9').text == LAYOUT_NAME:
          layout.click()
          return True
    except Exception as e:
      open_tv_logger.exception(f'An error happened when changing the layout. Error: ')
      return False
    
  def current_layout(self):
    '''This returns the current layout of the chart.'''
    try:
      curr_layout = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="header-toolbar-save-load"]')))
      return curr_layout.find_element(By.CSS_SELECTOR, '.text-yyMUOAN9').text
    except Exception as e:
      open_tv_logger.exception(f'An error happened when getting the current layout. Error: ')
      return ''

  def change_settings(self, symbols_list):
    '''This changes the settings of the screener. It first fills in the "Used Symbols" input to tell the indicator how many symbols we're going to use. Then it fills in the symbols and clicks on Submit.'''
    try:
      # find the settings popup
      settings = None
      screener = self.get_indicator(self.screener_shorttitle)  # get the screener
      if not screener:
        open_tv_logger.error(f'Could not find screener indicator: {screener}. Exiting function.')
        return False
      
      # Open its settings
      self.screener_indicator = screener
      self.screener_indicator.click()
      WebDriverWait(self.screener_indicator, 15).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[data-name="legend-settings-action"]'))).click()
      settings = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, '.content-tBgV1m0B')))
      symbol_inputs = settings.find_elements(By.CSS_SELECTOR, '.inlineRow-tBgV1m0B div[data-name="edit-button"]') # symbol inputs

      # fill in the Used Symbols input
      input_names = settings.find_elements(By.CSS_SELECTOR, 'div[class="cell-tBgV1m0B first-tBgV1m0B"] div[class="inner-tBgV1m0B"]')
      inputs = settings.find_elements(By.CSS_SELECTOR, 'div[class="cell-tBgV1m0B"] div[class="inner-tBgV1m0B"] > span')
      symbols_used_input = None

      for index, element in enumerate(input_names):
        if element.text == USED_SYMBOLS_INPUT:
          symbols_used_input = inputs[index]
          break

      symbols_used_input.send_keys(len(symbols_list))
      symbols_used_input.send_keys(Keys.ENTER)

      # change the symbol inputs based on the total number of symbols
      for i, to_be_symbol in enumerate(symbols_list):
        symbol_inputs[i].click()
        search_input = self.driver.find_element(By.XPATH, '//*[@id="overlap-manager-root"]/div/div/div[2]/div/div/div[2]/div/div[2]/div/input')
        search_input.send_keys(to_be_symbol)
        search_input.send_keys(Keys.ENTER)

      # click on submit
      self.driver.find_element(By.CSS_SELECTOR, 'button[name="submit"]').click()
      open_tv_logger.info(f'Successfully changed the inputs of the screener: {symbols_list}')
      return True
    except Exception as e:
      open_tv_logger.exception('Error ocurred when filling in the inputs of the screener. Error:')
      return False

  def open_alerts_sidebar(self):
    '''opens the alerts sidebar if it is closed. If it is already open, it does nothing'''
    try:
      alert_button = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[data-name="right-toolbar"] button[aria-label="Alerts"]')))
      if alert_button.get_attribute('aria-pressed') == 'false':
        alert_button.click()
        open_tv_logger.info('Successfully opened the alerts sidebar!')
        return True
      else: # if the alerts sidebar is already open
        open_tv_logger.info('The alerts sidebar is already open!')
        return True
    except Exception as e:
      open_tv_logger.exception(f'An error happened when opening the alerts sidebar. Error: ')
      return False

  def set_alerts(self, symbols):
    '''This first checks if the screener has an error. If it does, it re-uploads it and fills in the symbols again. If an error is still there, `False` is returned. If there was no error in the first place, an alert gets created. If there was an error in creating the alert, it tries again.'''

    # check if the screener indicator has an error
    if not self.is_no_error(self.screener_shorttitle):
      open_tv_logger.error('Screener indicator had an error. Could not set an alert for this tab. Trying to reupload indicator')
      if not self.reupload_indicator():
        open_tv_logger.error('Could not re-upload screener. Cannot set an alert for the screener. Exiting function.')
        return False
      if not self.change_settings(symbols):
        open_tv_logger.error('Could not input the symbols into the screener. Cannot set an alert for the screener. Exiting function.')
        return False
      sleep(5) # wait for the screener indicator to fully load (we are avoiding to wait for the indicator to load because it will take too long)
      if not self.is_no_error(self.screener_shorttitle): # if an error is still there
        open_tv_logger.error('Error is still there in the screener. Cannot set an alert for the screener. Exiting function.')
        return False
   
    # set the alert for the screener
    try:
      if not self.click_create_alert():
        if self.reupload_indicator(): # Reuploading the screener
          if self.change_settings(symbols):
            return self.click_create_alert()
      else:
        return True
    except Exception as e:
      open_tv_logger.exception('Error occurred when setting up alert. Exiting function. Error:')
      return False
    
    return False
  
  def click_create_alert(self):
    '''This clicks the + button to create an alert for the screener and clicks on Create. This returns `True` if the alert was created otherwise `False`. If something goes wrong, the "Create Alert" popup will be closed (if it was open) and `False` will be returned.'''
    try:
      # click on the + button
      plus_button = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[data-name="set-alert-button"]')))
      plus_button.click()
        
      # wait for the create alert popup to show and click the dropdown 
      popup = None
      try:
        popup = WebDriverWait(self.driver, 5).until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'div[data-name="alerts-create-edit-dialog"]')))
      except TimeoutException:
        self.driver.get(self.driver.current_url) # If the popup doesn't show up within 5 seconds, refresh the page and try again. I can't use self.driver.refresh() because that might trigger a Google popup asking you if you want to refresh the page. I don't think PYthon can click control Google popups
        sleep(3) # wait for the page to load after refreshing
        open_tv_logger.error('Popup did not show up within 5 seconds. Page refreshed. Trying to create alert again.')
        plus_button = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[data-name="set-alert-button"]')))
        plus_button.click()
      
      WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'span[data-name="main-series-select"]'))).click()
    
      # choose the screener
      screener_found = False
      for el in self.driver.find_elements(By.CSS_SELECTOR, 'div[data-name="menu-inner"] div[role="option"]'):
        if self.screener_shorttitle in el.text:
          screener_found = True
          el.click()
          break    

      if not screener_found: # if the screener is not found, close the "Create Alert" popup and exit
        open_tv_logger.error('Failed to create alert. Screener is unavailable in the dropdown. Closing popup and exiting.')
        popup.find_element(By.CSS_SELECTOR, 'button[data-name="close"]').click()
        return False
      
      # click on submit if the screener was available in the dropdown and was selected
      if screener_found:
        self.driver.find_element(By.CSS_SELECTOR, 'button[data-name="submit"]').click()
        open_tv_logger.info('Clicked on "Create"!')

        # wait for the alert to be created
        try:
          WebDriverWait(self.driver, 2.5).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-name="alerts-create-edit-dialog"] div[data-name="error-hint"]')))
        except:
          open_tv_logger.info('No error occured while saving alert!')
          return True
        else:
          open_tv_logger.error('Alert failed to get saved. Clicking on "Cancel".')
          self.driver.find_element(By.CSS_SELECTOR, 'div[data-name="alerts-create-edit-dialog"] button[data-name="cancel"]').click()
          return False
        
    except Exception as e:
      # close the "Create Alert" popup if an alert fails to get created
      popup = WebDriverWait(self.driver, 3).until(EC.visibility_of_element_located((By.CSS_SELECTOR, 'div[data-name="alerts-create-edit-dialog"]')))
      if popup: 
        if popup.find_elements(By.CSS_SELECTOR, 'button[data-name="close"]'):
          popup.find_element(By.CSS_SELECTOR, 'button[data-name="close"]').click()
      open_tv_logger.exception('Error occurred when setting up alert. Exiting function. Error:')
      return False
    
    return False
  
  def indicator_visibility(self, make_visible: bool, shorttitle: str):
    '''Makes `shorttitle` indicator visible or hidden by clicking on the indicator's 👁️ button'''

    # get the indicator
    indicator = None
    if shorttitle == self.screener_shorttitle:
      indicator = self.screener_indicator
    elif shorttitle == self.drawer_shorttitle:
      indicator = self.drawer_indicator

    try:
      if indicator != None: # that means that we've found our indicator
        eye = indicator.find_element(By.CSS_SELECTOR, 'div[data-name="legend-show-hide-action"]')
        status = 'Hidden' if 'disabled' in indicator.get_attribute('class') else 'Shown'
        
        if make_visible == False: 
          if status == 'Shown': # if status is "Hidden", that means that it is already hidden
            indicator.click()
            eye.click()
            open_tv_logger.info(f'Successfully changed the visibility of {shorttitle} to make it invisible!')
            return True
          if status == 'Hidden': # if status is "Hidden", that means that it is already hidden
            open_tv_logger.info(f'{shorttitle} indicator is already hidden. No need to change its visibility!')
            return True

        if make_visible == True: 
          if status == 'Hidden': # if status is "Shown", that means that it is already shown
            indicator.click()
            eye.click()
            open_tv_logger.info(f'Successfully changed the visibility of {shorttitle} to make it visible!')
            return True
          if status == 'Shown': # if status is "Hidden", that means that it is already hidden
            open_tv_logger.info(f'{shorttitle} indicator is already visible. No need to change its visibility!')
            return True
    except Exception as e:
      open_tv_logger.exception(f'Error ocurred when changing the visibility of {shorttitle} to make it {"visible" if make_visible else "invisible"}. Error: ')
      return False
    
    return False

  def is_visible(self, shorttitle: str):
    '''This returns `True` if the visibility of `shorttitle` indicator is shown. Otherwise, this returns `False` if its visibility is hidden.'''
    # get the indicator
    indicator = None
    if shorttitle == self.screener_shorttitle:
      indicator = self.screener_indicator
    elif shorttitle == self.drawer_shorttitle:
      indicator = self.drawer_indicator
      
    # check its visibility
    try:
      if indicator != None: # that means that we've found our indicator
        status = 'Hidden' if 'disabled' in indicator.get_attribute('class') else 'Shown'
        open_tv_logger.info(f'{shorttitle} indicator is {status}.')
        return status == 'Shown'
    except Exception as e:
      open_tv_logger.exception(f'Error ocurred when checking the visibility of {shorttitle} indicator. Error:')
      return False
    
    return False

  def is_no_error(self, shorttitle:str):
    '''
    this checks if the indicator has successfully loaded without an error. Returns `True` if it has no error but `False` if there is an error.
    '''
    try:
      # find the indicator
      indicator = None
      if shorttitle == self.screener_shorttitle:
        indicator = self.screener_indicator
      elif shorttitle == self.drawer_shorttitle:
        indicator = self.drawer_indicator

      # if there is no error
      if indicator.find_elements(By.CSS_SELECTOR, '.statusItem-Lgtz1OtS.small-Lgtz1OtS.dataProblemLow-Lgtz1OtS') == []:
        open_tv_logger.info(f'There is no error in {shorttitle}!')
        return True
      
      open_tv_logger.error(f'There is an error in {shorttitle}.')
      return False
    except Exception as e:
      open_tv_logger.exception(f'Error ocurred when checking if {shorttitle} had an error. Error:')
      return False
    
  def delete_all_alerts(self):
    '''Waits for the alert sidebar to show up and deletes all the alerts if there are any. Then it waits a second.'''
    try:
      # wait for the alert sidebar to show up
      alert_sidebar1 = WebDriverWait(self.driver, 5).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, '.body-i8Od6xAB')))
      if not alert_sidebar1:
        open_tv_logger.error('Alert sidebar not found. Cannot delete all alerts.')
        return False

      # Check if there already are no alerts
      sleep(3) #wait for the alert sidebar to load fully
      if self.driver.find_elements(By.CSS_SELECTOR, 'div.list-G90Hl2iS div.itemBody-ucBqatk5') == []:
        open_tv_logger.info('There are no alerts. No need to delete any alerts!')
        return True

      # click the 3 dots
      settings = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-name="alerts-settings-button"]')))
      WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[data-name="alerts-settings-button"]'))).click()
         
      # delete all alerts
      WebDriverWait(self.driver, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[class="item-jFqVJoPk item-xZRtm41u withIcon-jFqVJoPk withIcon-xZRtm41u"]')))[-1].click() # in the dropdown which it opens, choose the "Remove all" option
      WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'button[name="yes"]'))).click() # click OK when the confirm dialog pops up

      sleep(1)
      if len(self.driver.find_elements(By.CSS_SELECTOR, 'div.list-G90Hl2iS div.itemBody-ucBqatk5')) == 0: # if there are no alerts visible (that means that the alerts have been deleted)
        open_tv_logger.info('All alerts have been sucessfully deleted!')
        return True
    except Exception as e:
      open_tv_logger.exception(f'Error happened somewhere when deleting all alerts. Failed to delete all alerts. Error:')
      return False
    
    return False

  def reupload_indicator(self):
    '''removes screener and reuploads it again to the chart by clicking on the screener in the Favorites dropdown. It then waits for the screener to show up on the chart and returns `True` if it does otherwise `False`.

    Don't remove the print statements. It seems like the code will only run with the print statements.'''
    val = False

    try:
      # click on screener indicator
      self.screener_indicator.click()

      # click on data-name="legend-delete-action" (a sub element under screener indicator)
      delete_action = WebDriverWait(self.screener_indicator, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[data-name="legend-delete-action"]')))
      print('Found remove button: ', delete_action)
      delete_action.click()

      # click on "Favorites" dropdowm
      WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[id="header-toolbar-indicators"] button[data-name="show-favorite-indicators"]'))).click()
      print('favorites dropdown was clicked')

      # Wait for the dropdown menu to appear
      menu = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-name="menu-inner"]')))
      print('dropdown menu appeared')

      # find Premium Screener in the dropdown menu and click on it
      dropdown_indicators = WebDriverWait(menu, 10).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[data-role="menuitem"]')))
      for el in dropdown_indicators:
        print('current indicator: ',el)
        text = el.find_element(By.CSS_SELECTOR, 'span[class="label-l0nf43ai apply-overflow-tooltip"]').text
        if self.screener_name == text:
          print('Found Premium Screener')
          if el.is_displayed():
            el.click()
            break
          else:
            # Scroll the element into view
            actions = ActionChains(menu).move_to_element(el)
            actions.perform()
            el.click()
            break
      
      # Wait for the indicator to show up on the chart
      start_time = time()
      timeout = SCREENER_REUPLOAD_TIMEOUT  # max seconds to wait
      while time() - start_time <= timeout:
        indicators = self.driver.find_elements(By.CSS_SELECTOR, 'div[data-name="legend-source-item"]')
        for ind in indicators:
          if ind.find_element(By.CSS_SELECTOR, 'div[class="title-l31H9iuA"]').text == self.screener_shorttitle:
            val = True
            break
        if val: # if the indicator is found on the chart, break the while loop
          open_tv_logger.info('The screener is on the chart after re-uploading it!')
          break
    except Exception as e:
      open_tv_logger.exception('An error occurred when re-uploading the screener. Could not reupload screener. Error: ')
      return False

    return val

  def get_indicator(self, ind_shorttitle: str):
    '''Returns the indicator which has the same shorttitle as `ind_shorttitle`. If an indicator with the same shorttitle can't be found or an error occurrs, `None` will be returned'''
    try:
      indicator = None
      wait = WebDriverWait(self.driver, 15)
      indicators = wait.until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, 'div[data-name="legend-source-item"]')))
      
      for ind in indicators: 
        indicator_name = ind.find_element(By.CSS_SELECTOR, 'div[class="title-l31H9iuA"]').text
        if indicator_name == ind_shorttitle: # finding the indicator
          open_tv_logger.info(f'Found indicator {ind_shorttitle}!')
          indicator = ind
          break
    except Exception as e:
      open_tv_logger.exception(f'Failed to find indicator {ind_shorttitle}. Error:')
      return None

    return indicator
    
    '''Checks if the Timeframe input of the Screener indicator is the same as `tf`. Returns `True` if it is the same, `False` otherwise.'''
    try:
      # open the settings of the screener
      self.screener_indicator.click()
      WebDriverWait(self.screener_indicator, 10).until(EC.element_to_be_clickable((By.CSS_SELECTOR, 'div[data-name="legend-settings-action"]'))).click()
      indicator_popup = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-dialog-name="Screener"]')))
      settings = indicator_popup.find_element(By.CSS_SELECTOR, '.content-tBgV1m0B')
       
      # Get the current value of the Timeframe input
      tf_val = settings.find_element(By.CSS_SELECTOR, 'div[class="cell-tBgV1m0B"] span[data-role="listbox"] span[class="button-children-tFul0OhX"] span').text
      open_tv_logger.info(f'Checked the screener\'s timeframe. Timeframe of the screener is {tf_val}.')
      return tf_val == tf
    except Exception as e:
      open_tv_logger.exception(f'Failed to check the timeframe of the screener. Error: ')
      return False
    
  def current_chart_tframe(self):
    '''Returns the current chart's timeframe'''
    try:
      tf_button = WebDriverWait(self.driver, 15).until(EC.presence_of_element_located((By.XPATH, '//*[@id="header-toolbar-intervals"]/button')))
      return tf_button.get_attribute('aria-label')
    except Exception as e:
      open_tv_logger.exception(f'Failed to get the current chart timeframe. Error:')
      return ''
    
  def alerts_sidebar_open(self):
    '''This checks if the Alerts sidebar is open. Returns `True` if it is and returns `False` if it is not.'''
    try:
      alert_button = WebDriverWait(self.driver, 10).until(EC.presence_of_element_located((By.CSS_SELECTOR, 'div[data-name="right-toolbar"] button[aria-label="Alerts"]')))
      if alert_button.get_attribute('aria-pressed') == 'true': # if the alerts sidebar is open
        open_tv_logger.info('The Alerts sidebar is open!')
        return True
      else:
        open_tv_logger.info('The Alerts sidebar is closed.')
        return False
    except Exception as e:
      open_tv_logger.exception(f'Failed to check if the Alerts sidebar is open. Error: ')
      return False
    
  def no_alerts(self):
    '''This checks if there no alerts. If there are no alerts, returns `True` and returns `False` if there are alerts'''
    try:
      alerts = self.driver.find_elements(By.CSS_SELECTOR, 'div.list-G90Hl2iS div.itemBody-ucBqatk5')
      if not alerts: # if there are no alerts
        open_tv_logger.info('There are no alerts!')
        return True
      else:
        open_tv_logger.info('There are alerts!')
        return False
    except Exception as e:
      open_tv_logger.exception(f'Failed to check if there are no alerts. Error: ')
      return False