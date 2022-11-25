# this config file contains multiple variables utilized throughout the functionality of this code
MERAKI_API_KEY = "ffxxx"
ORG_IDS = ["999999"] #Only need 1 if only 1 org
validators = ["bbdcssxx"] #Only need 1 if only 1 org
secrets = ["123456789"] #Only need 1 if only 1 org


#these are the parameters and thresholds used by the cmxsummary.py script, change as you desire
initialRSSIThreshold=15
visitorRSSIThreshold=10
maxSecondsAwayNewVisit=120
minMinutesVisit=0
theTimeZone='US/Central'


entranceAPs=["EntranceAP1", "EntranceAP2"]
internalAPs=["InsideAP1","InsideAP2", "InsideAP3"]
