'''
Sends messages to discord webhooks.

To create a webhook url, do this:
go to a discord channel -> Edit channel -> Integrations -> Webhooks -> New Webhook
'''
import logger_setup 
from discord_webhook import DiscordWebhook
from resources.categories import *

# Set up logger for this file
discord_logger = logger_setup.setup_logger(__name__, logger_setup.logging.DEBUG)

class Discord:
    def __init__(self):
        self.webhook_urls = {
            CURRENCIES_WEBHOOK_NAME: CURRENCIES_WEBHOOK_LINK,
            US_STOCKS_WEBHOOK_NAME: US_STOCKS_WEBHOOK_LINK,
            INDIAN_STOCKS_WEBHOOK_NAME: INDIAN_STOCKS_WEBHOOK_LINK,
            CRYPTO_WEBHOOK_NAME: CRYPTO_WEBHOOK_LINK,
            INDICES_WEBHOOK_NAME: INDICES_WEBHOOK_LINK
        }

    def create_msg(self, category, content):
        try:
            webhook = DiscordWebhook(url=self.webhook_urls[category], content=content)
            response = webhook.execute()
        except Exception as e:
            discord_logger.exception(f'Error sending "{content}" to {category} webhook. Error:')
