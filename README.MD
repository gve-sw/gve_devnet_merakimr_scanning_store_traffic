# Meraki MR Analytics Store Traffic sample

## Contacts

* Gerardo Chaves 
* Ozair Saiyad (based on similar script for V3 of Scanning API: https://github.com/gve-sw/gve_merakimr_locationanalytics)

## Introduction
These python scripts recieve telemetry from the Meraki Scanning API and stores it in plain text
using CSV format in the **cmxData.csv** file. It also generates a list of "visits" into a store based on WiFi enabled devices detected entering and leaving the area covered by the MR access points specified as "External" (Entrance) and "Internal" acccess points in the config.py file and stores them in a file named **visitsSummary.csv**

<br/>
<br/>
To be able to calculates visits, the application stores the following for each "observation" it receives (one row per observation)
in a file named **cmxData.csv**:
<br/>
<br/>
``` Network Name, Access Point Name, Access Point MAC, Client MAC, Timestamp, RSSI ```
<br/>
<br/>
The **Network Name** and **Access Point Name** are retrieved when when script first runs since it creates a map of all MR devices from all networks
in the organization defined in the ORG_ID variable in the config.py file.
<br/>
<br/>
More details on the Access Point MAC, Client MAC, Timestamp and RSSI fields can be found here:
https://developer.cisco.com/meraki/scanning-api/#!3-0/observation-payloads 
<br/>
<br/>
The **visitsSummary.csv** file, which gets generated after running the visitsSummary.py script (if in Manual mode, or periodically by the main cmxreceiver.py script if not), contains the following for each row:
<br/>
<br/>
```Network Name, Client MAC, External AP Name, Internal AP Name, Visit Date (timezone adjusted), Visit Time (timezone adjusted), Visit Length (minutes)```
<br/>
<br/>

What constitutes a "visit" is determined by an algorithm described in the comments in the visitsSummary.py script.  
<br/>
<br/>



---
## Configuration

**Config.py** contains all of the global variables and configuration needed throughout the code, including keys and thresholds such as initialRSSIThreshold, minMinutesVisit , theTimeZone, entranceAPs and internalAPs.
<br/><br/>
In that file, you must fill in the values for the following variables:
<br/><br/>
**MERAKI_API_KEY**: This should contain your Meraki API key (details at https://developer.cisco.com/meraki/scanning-api/#!enable-scanning-api/enable-scanning-api)<br/>
**ORG_IDS**: An array with the Organization IDs you wish to use from which to consider all encompassing networks to search for access points.<br/>
**validators**: An array with the validator keys that can be found in the Meraki dashboard by navigating to Network-wide > General. Scroll down to “Location and Analytics” to copy and paste the validator key for each organization you are configuring into code (ensure analytics and scanning API are enabled)<br/>
**secrets**: An array with the secrets that can be found in the Meraki dashboard by navigating to Network-wide > General. Scroll down to “Location and Analytics” to copy and paste the secret key for each organization you are configuring into code (ensure analytics and scanning API are enabled)<br/>
**entranceAPs**: This is an array of access point names that are considered "External" to the store or right at the entrance.  
**internalAPs**: This is an array of access point names that are considered "Internal" to the store to be able to determine that a visitor actually entered the store if detected by them.  

More details on validators and secrets for the scanning-api can be found here: https://developer.cisco.com/meraki/scanning-api/#!enable-scanning-api/enable-location-api  
 

---
## Local machine configuration and Meraki Location analytics Access point Setup

This Meraki CMX receiver sample is a simple example demonstrating how to interact with the Scanning API.<br/>
This is how it works:
- Meraki access points will listen for WiFi clients that are searching for a network to join and log the events.
- The "observations" are then collected temporarily in the cloud where additional information can be added to
the event, such as GPS, X Y coordinates and additional client details.
- Meraki will first send a GET request to this CMX receiver, which expects to receive a "validator" key that matches
the Meraki network's validator.
- Meraki will then send a JSON message to this application's POST URL (i.e. http://yourserver/ method=[POST])
- The JSON is checked to ensure it matches the expected secret, version and observation device type.

Cisco Meraki Location Scanning Documentation
https://documentation.meraki.com/MR/Monitoring_and_Reporting/Scanning_API_for_Location_Analytics_Solutions
https://documentation.meraki.com/MR/Monitoring_and_Reporting/Location_Analytics 

More details on configuring the Meraki Dashboard for the Scanning API can be found here:
https://developer.cisco.com/meraki/scanning-api/#!enable-scanning-api/enable-scanning-api

Specifically for this example, **cmxreceiver.py** python script implements a web server that needs to have a publicly addressable address so that it can
be configured as a webhook on the Meraki Dashboard API. If you wish to run it on a machine behind a corporate firewall such as a
PC or laptop connected to a corporate network you need to use a utility such as Ngrok to open a "pinhole" on the firewall to be able
to redirect traffic to the script. Not all organizations support the use of ngrok or other similar utilities and it is definitely not
recommended to use in a production environment. But for quick testing it can be quite useful. Here is how you use it:
<br/><br/>

1. Download ngrok which is used to create public URLs for programs (more information here: https://ngrok.com)
2. Use ngrok to expose port 5500 by entering ‘./ngrok http 5500’ into terminal
3. You should see a url created that looks similar to this ‘https://2a6eed03.ngrok.io/'
4. Copy and paste this url into the “Post URL” section of “Location and Analytics” in the Meraki Dashboard
5. Note that the validate button should fail at this point as the the cmx receiver is not up and running



---
## Running the scripts

1. Make sure Python 3.10 or later is installed
2. Make sure pip is installed (https://pip.pypa.io/en/stable/installing/ for more information on pip)
3. Enter ```pip install -r requirements.txt``` into command line to download necessary libraries
4. Ensure all elements of the **config.py** file are completed
5. If behind a corporate firewall and using ngrok, make sure ngrok is running and that the url matches what is in the Meraki Dashboard (```./ngrok http 5500```)
6. In a new terminal window, enter ```python3 cmxreceiver.py``` (note at this point the validate button in the Meraki dashboard should be working, data will stream every minute or so)
7. Once you are done collecting observations with the **cmxreceiver.py** script or while collecting, you can run the **visitsSummary.py** script to generate
the list of unique visitors in **visitsSummary.csv**. To run it, enter ```python3 visitsSummary.py``` in the command line.
` 




## Additional info:

### LICENSE

Provided under Cisco Sample Code License, for details see [LICENSE](LICENSE.txt)

### CODE_OF_CONDUCT

Our code of conduct is available [here](Code_of_Conduct.md)

### CONTRIBUTING

See our contributing guidelines [here](Contributing.md)

#### DISCLAIMER:
<b>Please note:</b> This script is meant for demo purposes only. All tools/ scripts in this repo are released for use "AS IS" without any warranties of any kind, including, but not limited to their installation, use, or performance. Any use of these scripts and tools is at your own risk. There is no guarantee that they have been through thorough testing in a comparable environment and we are not responsible for any damage or data loss incurred with their use.
You are responsible for reviewing and testing any scripts you run thoroughly before use in any non-testing environment.

