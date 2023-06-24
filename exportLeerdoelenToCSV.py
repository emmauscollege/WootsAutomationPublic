# exportLeerdoelenToCSV.py
# Input: question_bank_name (naam van itembank)
# Output: csv formatted list of domains and objectives 
# Description:
# leerdoelen (objectives) zijn gegroepeerd in domeinen (domains) 
# domeinen maken onderdeel uit van één itembank (questionbank)
# de domains en objectives in een itembank kun je snel toevoegen via Woots webinterface, 
# dat scripten we dus niet, het moet in Woots ingevoerd zijn voor je dit script draait
# Documentation:
# - Woots API reference (requires login to woots) <br>
# https://app.woots.nl/api/docs/index.html
# - How to create a token for Woots API <br>
# https://support.woots.nl/hc/nl/articles/8422631132689-Genereer-een-API-token

import requests
import sys
import os
import json

# user parameters, you may need to change these
school_id = 1680 # school_id can be found on same webpage as where you create a token
question_bank_id = 70902 # use script to find question_bank_id by name

# system parameters, these should not be changed
api_server = "https://app.woots.nl/api/v2"
api_endpoint = "" # something like "/question_banks", value will be provided before each api call
api_header = "" # value will be assigned after token has been read

# find token to use for Woots API calls
argv_token = None
if len(sys.argv) > 1 :
    argv_token = sys.argv[1] 
env_token = os.environ.get("WOOTS_API_TOKEN")
token = argv_token or env_token  # token can be created her: https://app.woots.nl/users/tokens
if token == None :
    print("Usage: python3 "+sys.argv[0]+"token")
    print("or create environment variable WOOTS_API_TOKEN containing token using")
    print('export WOOTS_API_TOKEN="token_like_23f79ds798abd"')
    print("A token can be created here:")
    print("https://app.woots.nl/users/tokens")
    exit(1)
api_header = {"accept": "application/json", "Authorization": "Bearer "+token}

#
# GET objectives from itembank
# prints table for copy-paste in .csv file
#

# GET all objectives in all domains domains from itembank
api_endpoint = f"/question_banks/{question_bank_id}/domains"
# print("request api_endpoint:", api_endpoint)
response = requests.get(api_server+api_endpoint, headers=api_header)
assert response.status_code == 200, f"unexpected response {response.status_code}"
domains = response.json()
#print(json.dumps(domains, indent=4)) 
print('domain_name,domain_position,domain_id,objective_name,objective_position,objective_id')
for domain in domains:
    api_endpoint = f'/domains/{domain["id"]}/objectives'
    #print("request api_endpoint:", api_endpoint)
    response = requests.get(api_server+api_endpoint, headers=api_header)
    assert response.status_code == 200, f"unexpected response {response.status_code}"
    objectives = response.json()
    for objective in objectives:
         print(f'{domain["name"]},{domain["position"]},{domain["id"]},{objective["name"].replace("<div>","").replace("</div>","")},{objective["position"]},{objective["id"]}') # remove div's added by Woots, TODO: support , in name
