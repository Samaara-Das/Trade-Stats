# Trade Stats

1. the Get Exits indicator should be on the Exits layout on TradingView

2. the Get Exits indicator should be favourited

3. In Pine Script, the Get Exits indicator must have its first 7 inputs in this order: `entryTime`, `entryPrice`, `entryType`, `sl`, `tp1`, `tp2`, `tp3`

4. On TradingView, "Alerts Log" cannot be minimized

5. There are going to be a few different types of messages that the alert on Pine Script will give. As of now, they are: "Tp1 hit", "Tp2 hit", "Tp3 hit", "Sl hit", "Trade is still running". Python is going to take the message of the alert and check which one of these messages came. So, make sure that Python also has the same types of messages in main.py.