# convertQuestionTitlesToLeerdoelen.py
# Input: leerdoelen in the title of an assignment in Woots
# Output: leerdoelen in appropriate meta data of a question in Woots
# assumption: one question per exercise
# Workflow:
# 1. Find a token to access the API from Woots
# 2. For all questions in all excercises in a question_bank:
# 3.      extract objectives from question_content
# 4.      update question to set objectives
# 5.      remove objectives from question_content
# Example of objectives present in question_content: 'What is Python?{"objective_ids":[1,3]}' 
# where 1 and 3 are id's of the objectives that have to be tied to the question
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
api_header_get = "" # value will be assigned after token has been read
api_header_patch = "" # value will be assigned after token has been read

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

# create headers
api_header_get = {"accept": "application/json", "Authorization": "Bearer "+token}
api_header_patch = {"accept": "application/json", "Authorization": "Bearer "+token, "Content-Type": "application/json"}

# GET list of excercises in question_bank
page = 1
last_page = 1
exercises =[]
while page <= last_page :
    api_params = {"items": 100, "page": page}
    api_endpoint = f"/question_banks/{question_bank_id}/question_bank_exercises"
    print("request api_endpoint?api_params: ", f"{api_endpoint}?{api_params}")
    response = requests.get(api_server+api_endpoint, params=api_params, headers=api_header_get)
    assert response.status_code == 200, f"unexpected response {response.status_code}"
    exercises.extend(response.json())
    last_page = int(response.headers["Total-Pages"])
    page = page + 1

for exercise in exercises:

    # GET questions in exercise
    api_endpoint = f'/exercises/{exercise["id"]}/questions'
    response = requests.get(api_server+api_endpoint, headers=api_header_get)
    assert response.status_code == 200, f"unexpected response {response.status_code}"
    questions = response.json()

    #
    # REFACTORED CODE, NOT TESTED
    #
    counter = 0
    for question in questions:
        key = ""
        if question["content"] != None and question["content"].find("{") != -1 : 
            key = "content"
        elif question["fill_content"] != None and question["fill_content"].find("{") != -1 : 
            key= "fill_content"

        if key != "" : # meta data present
            # extract meta data from question_content
            title = question[key]
            meta_string = title[title.find("{"):title.find("}")+1]
            assert json.loads(meta_string) != None, "wrong format of meta data" # this line is a good check, but you will never see the assert message, as json.loads will abort at an error

            # add meta data to question
            api_endpoint = f'/questions/{question["id"]}'
            response = requests.patch(api_server+api_endpoint, data=meta_string, headers=api_header_patch)
            assert response.status_code == 200, f"unexpected response {response.status_code}"

            # create title without meta data
            title_no_meta = title[0:title.find("{")] + title[title.find("}")+1:len(title)]
            patch = {key: title_no_meta }
            api_endpoint = f'/questions/{question["id"]}'
            # save title without meta data to woots, comment out the next to lines while testing
            response = requests.patch(api_server+api_endpoint, json=patch, headers=api_header_patch)
            assert response.status_code == 200, f"unexpected response {response.status_code}{response.text}"
            counter = counter + 1
            print(f'{counter} meta data found, "exercise_id:" {exercise["id"]}, {meta_string}')