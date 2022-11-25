"""
Copyright (c) 2022 Cisco and/or its affiliates.
This software is licensed to you under the terms of the Cisco Sample
Code License, Version 1.1 (the "License"). You may obtain a copy of the
License at
               https://developer.cisco.com/docs/licenses
All use of the material herein must be in accordance with the terms of
the License. All rights not expressly granted by the License are
reserved. Unless required by applicable law or agreed to separately in
writing, software distributed under the License is distributed on an "AS
IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express
or implied.
"""

# code pulls cmx observation data from the CMXData.csv file and creates a summary of store visits
# in visitsSummary.csv based on observations of clients moving from APs specified in the 
# entranceAPs array of AP Names to those in the internalAPs array of AP Names

# Libraries
from datetime import datetime
from pytz import timezone
import csv
import sys
from config import ORG_IDS, MERAKI_API_KEY
import meraki
from config import initialRSSIThreshold, \
                    minMinutesVisit, \
                    theTimeZone, \
                    entranceAPs, \
                    internalAPs

csvinputfile = None
csvoutputfile = None

dashboard = meraki.DashboardAPI(api_key=MERAKI_API_KEY)

def retrieveClientData(first_time_seen):
    # Get list of organizations to which API key has access
    organizations = dashboard.organizations.getOrganizations()
    client_ips={}
    # Iterate through list of orgs
    for org in organizations:
        print(f'\nAnalyzing organization {org["name"]}:')
        org_id = org['id']
        #skip org if not speficied in list
        if org_id not in ORG_IDS:
            print(f'Skipping org id: {org_id}')
            continue
        # Get list of networks in organization
        try:
            networks = dashboard.organizations.getOrganizationNetworks(org_id)
        except meraki.APIError as e:
            print(f'Meraki API error: {e}')
            print(f'status code = {e.status}')
            print(f'reason = {e.reason}')
            print(f'error = {e.message}')
            continue
        except Exception as e:
            print(f'some other error: {e}')
            continue

        # Iterate through networks
        total = len(networks)
        counter = 1
        print(f'  - iterating through {total} networks in organization {org_id}')
        for net in networks:
            print(f'Finding clients in network {net["name"]} ({counter} of {total})')
            try:
                # Get list of clients on network, filtering on timespan of last 14 days
                clients = dashboard.networks.getNetworkClients(net['id'], t0=first_time_seen, perPage=1000, total_pages='all') #TODO: set timespan to match data in readings
            except meraki.APIError as e:
                print(f'Meraki API error: {e}')
                print(f'status code = {e.status}')
                print(f'reason = {e.reason}')
                print(f'error = {e.message}')
            except Exception as e:
                print(f'some other error: {e}')
            else:
                if clients:
                    #print(clients)
                    print(f'  - found {len(clients)}')
                    for client in clients:
                        client_ips[client['mac']]=client['ip']
            counter += 1
    return client_ips



def timestamp_converter(time) :
    date,time = time.split('T')
    time = time.replace('Z','')
    # print(date)
    # print(time)
    return date,time

def datetime_handler(date, time) :
      time_components= [int(x) for x in time.split(':') ]
      date_components = [int(x) for x in date.split('-') ]
    #   print(date_components)
      datetime_obj = datetime(date_components[0], date_components[1],date_components[2],time_components[0],time_components[1],time_components[2])
      return datetime_obj


if __name__ == '__main__':
    fieldnamesin = ['NETNAME', 'APNAME', 'APMAC', 'CLIENT_MAC', 'time', 'rssi']
    externalObservations={}
    internalVisits={}
    fieldnamesout = ['NETNAME', 'CLIENT_MAC','client_ip', 'external_ap_name','internal_ap_name','start_inside_date', 'start_inside_time','length_mins']

    

    first_time_seen=''

    # capture all strong (95+rssi>15) readings from Entrance APs with timestamp into externalObservations
    # (using client mac as key)  
    # for each strong (95+rssi>15) reading from internal IPs, check if client MAC is in externalObservations. 
    #  If so, create a record in internalVisits (also indexed by MAC) 
    # with both timestamps 
    # (from latest external AP reading and internal AP reading that triggered the entry) .
    #  Also record the AP name from which they entered and the 
    # one from the internal list with the readings we are recording

    with open('cmxdata.csv', newline='') as csvinputfile:
        datareader = csv.DictReader(csvinputfile, fieldnames=fieldnamesin)
        next(datareader, None) #skip the header row
        for row in datareader:
            #print(row['NETNAME'], row['APNAME'],row['APMAC'], row['MAC'], row['time'], row['rssi'])
            #assigning client MAC address from the row from the input file to a separate variable for better
            #readability of the code
            clientMAC=row['CLIENT_MAC']
            if (96+int(row['rssi']))>=initialRSSIThreshold:
                if (row['APNAME'] in entranceAPs):
                    # reading from entrance APIs, record in in-memory array indexed in dict for that client MAC
                    # keep all strong external observations 
                    if clientMAC not in externalObservations:
                        externalObservations[clientMAC]=[]
                    aStrongReading= {}
                    aStrongReading['time_ts']= row['time']
                    aStrongReading['rssi'] = int(row['rssi'])
                    aStrongReading['NETNAME'] = row['NETNAME']
                    aStrongReading['APNAME'] = row['APNAME']
                    externalObservations[clientMAC].append(aStrongReading)
                    if first_time_seen=='':
                        first_time_seen=row['time']
                if (row['APNAME'] in internalAPs):
                    #This reading is for an internal AP, but we are only interested in those we saw earlier
                    #also on entranceAPs
                    if clientMAC in externalObservations:
                        # Keep the most recent reading for the client that was also seen at entrance
                        if not clientMAC in internalVisits:
                            internalVisits[clientMAC]={}
                        internalVisits[clientMAC]['latest']={'time_ts': row['time'],'rssi' : int(row['rssi']), \
                                                            'NETNAME': row['NETNAME'] , 'APNAME': row['APNAME'] }
                        for aReading in externalObservations[clientMAC]:
                            # Also keep the reading with same client mac seen inside that was also seen outside with the smallest delta
                            # between time seen in the entrance and first seen inside
                            ext_ts=aReading['time_ts']
                            [ext_date, ext_time] = timestamp_converter(ext_ts)
                            extDT= datetime_handler(ext_date, ext_time)

                            int_ts=row['time']
                            [int_date, int_time] = timestamp_converter(int_ts)
                            intDT= datetime_handler(int_date, int_time)

                            deltaSecs=intDT.timestamp()-extDT.timestamp()
                            
                            if (not 'first_entered' in internalVisits[clientMAC]) or \
                                (deltaSecs < internalVisits[clientMAC]['first_entered']['delta']): 
                                    internalVisits[clientMAC]['first_entered']= {'time_ts': row['time'],'rssi' : int(row['rssi']), \
                                                                'NETNAME': row['NETNAME'] , 'EXTAPNAME': aReading['APNAME'],'APNAME': row['APNAME'], \
                                                                    'delta': deltaSecs } 


    print("Done reading and mapping, starting to generate summary file...")
    print("dict of internal Visits:\n", internalVisits)

    # First, we retrieve enough client data to map IP addresses to MAC addresses of clients, if they associated
    clients_ips=retrieveClientData(first_time_seen)
    
    #fieldnamesout = ['NETNAME', 'CLIENT_MAC', 'external_ap_name','internal_ap_name','start_inside_date', 'start_inside_time','length_mins']
    with open('visitsSummary.csv', 'w', newline='') as csvoutputfile:
        localTZ = timezone(theTimeZone)
        writer = csv.DictWriter(csvoutputfile, fieldnames=fieldnamesout)
        writer.writeheader()
        for theKey in internalVisits:
            if 'first_entered' in internalVisits[theKey]:
                [start_inside_date, start_inside_time] = timestamp_converter(internalVisits[theKey]['first_entered']['time_ts'])
                theTime= datetime_handler(start_inside_date, start_inside_time)
                theLocalTime=theTime.astimezone(localTZ)
                [last_inside_date, last_inside_time] = timestamp_converter(internalVisits[theKey]['latest']['time_ts'])
                theDeltaSeconds = datetime_handler(last_inside_date, last_inside_time).timestamp() - theTime.timestamp()
                theVisitLength=round(theDeltaSeconds / 60,2)

                if theVisitLength>=minMinutesVisit:
                    print("Network which meets visit length:", internalVisits[theKey]['first_entered']['NETNAME'],'\n')
                    #TODO: use variable "theKey" to query meraki dashboard API to find out if there is a client IP
                    # associated to it and, if so, write out new column indicating it was "connected"
                    # use GET /networks/{networkId}/clients to obtain the list of clients for a time period (the time period
                    # in the capture data) and try to determine an association
                    writer.writerow({'NETNAME': internalVisits[theKey]['first_entered']['NETNAME'],
                                        'CLIENT_MAC': theKey,
                                        'client_ip': clients_ips[theKey] if theKey in clients_ips else '',
                                        'external_ap_name': internalVisits[theKey]['first_entered']['EXTAPNAME'],
                                        'internal_ap_name': internalVisits[theKey]['latest']['APNAME'],
                                        'start_inside_date': theLocalTime.strftime('%m/%d/%Y'),
                                        'start_inside_time': theLocalTime.strftime('%H:%M'),
                                        'length_mins': theVisitLength})

    print("Summary File generated.")



