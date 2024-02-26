'''
this is how we send post requests to Nishant uncle's database through his webhook
'''

import logger_setup
from requests import Session
from requests.adapters import HTTPAdapter
from requests.exceptions import ConnectionError


# Set up logger for this file
nk_db_logger = logger_setup.setup_logger(__name__, logger_setup.logging.DEBUG)

class Post:
  def __init__(self, max_retries=3):
    self.url = 'https://pointcapitalis.com/meta/addTradeViewData'
    self.adapter = HTTPAdapter(max_retries=max_retries)
    self.session = Session()
    self.session.mount(self.url, self.adapter)

  def post_to_url(self, payload: dict):
    try:
      response = self.session.post(self.url, data=payload)
    except ConnectionError as e:
      nk_db_logger.exception(f'ConnectionError occurred while sending post request to Nishant uncle\'s webhook ')
      return False
    else:
      nk_db_logger.info(f'Post request to Nishant uncle\'s webhook sent successfully! Response: {response}')
      return response
    
