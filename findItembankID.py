# findItemBankID.py
# Input: question_bank_name (naam van itembank)
# Output: id of the question_bank
# Description:
# The Woots webinterface doesn't show the id of an itembank
# this script finds the id based on the name
# the question_bank_id is needed in other scripts
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
question_bank_name = "Frans GL6 1-3HV" # can be found in Woots webpage 
question_bank_id = -1 # our code will look this up through the API based in question_bank_name

# system parameters, these should not be changed
api_server = "https://app.woots.nl/api/v2"
api_endpoint = "" # something like "/question_banks", value will be provided before each api call
api_header = "" # value will be assigned after token has been read

# find token to use for Woots API calls
argv_token = None
if len(sys.argv) > 1 :
    argv_token = sys.argv[1] 
env_token = os.environ.get("WOOTS_API_TOKEN")
token = argv_token or env_token  # token can be created here: https://app.woots.nl/users/tokens
if token == None :
    print("Usage: python3 "+sys.argv[0]+" token")
    print("or create environment variable WOOTS_API_TOKEN containing token using")
    print('export WOOTS_API_TOKEN="token_like_23f79ds798abd"')
    print("A token can be created here:")
    print("https://app.woots.nl/users/tokens")
    exit(1)
api_header = {"accept": "application/json", "Authorization": "Bearer "+token}

# GET itembank_id from question_bank with question_bank_name
api_endpoint = f"/question_banks"
#print("request api_endpoint:", api_endpoint)
response = requests.get(api_server+api_endpoint, headers=api_header)
assert response.status_code == 200, f"unexpected response {response.status_code}"
data = response.json()
#print(json.dumps(data, indent=4)) 
question_bank_id = -1
for question_bank in data:
    assert not (question_bank["name"] == question_bank_name and question_bank_id >= 0), f"Multiple question_banks with the same name {question_bank_name}"
    if question_bank["name"] == question_bank_name:
        question_bank_id = question_bank["id"]
assert question_bank_id >= 0, f"No question_bank with name {question_bank_name}"

print(f"question_bank_id: {question_bank_id}")