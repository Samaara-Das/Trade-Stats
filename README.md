# Trade Stats

1. the Get Exits indicator should be on the Exits layout on TradingView

2. the Get Exits indicator should be favourited

3. In Pine Script, the Get Exits indicator must have its first 7 inputs in this order: `entryTime`, `entryPrice`, `entryType`, `sl`, `tp1`, `tp2`, `tp3`

4. On TradingView, "Alerts Log" cannot be minimized

5. There are going to be a few different types of messages that the alert on Pine Script will give. As of now, they are: "Tp1 hit", "Tp2 hit", "Tp3 hit", "Sl hit", "Trade is still running". Python is going to take the message of the alert and check which one of these messages came. So, make sure that Python also has the same types of messages in main.py.

6. in the `collections` list in main.py, add all the names of the collections under the "tradingview-to-everywhere" database in MongoDb

7. `START_FRESH` is like an on/off switch for starting fresh, deleting all alerts and setting up new alerts OR just opening TradingView, keeping the pre-existing alerts and waiting for alerts to come. If it's `True`, the application will open TradingView, delete all the alerts and start setting up all 260 alerts again. If it's `False`, the application will open TradingView, NOT delete the alerts but instead keep all the alerts that were made when the application was previously run. This variable was created so that I could do 2 things:
    - When I leave the application running, come back in the morning to find it frozen and find alerts in the Alerts log that are unread by the application, I would like to re-start the application and keep the alerts that were made when it ran previously without deleting all the alerts and therefore, keeping the alerts in the Alerts log. So, when I run the application with `START_FRESH` set to `False`, the application won't delete all the alerts, read the unread alerts that came when it was previously running and wait for new alerts.
    - Sometimes, when I think I need to start fresh, delete all the alerts and make new ones, I can set `START_FRESH` set to `True`.