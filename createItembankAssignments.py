import requests, os, json, random

# --- GLOBAL VARIABLES user may need to change these
school_id = "1680"
question_bank_id = 70902
random.seed(1974) # change the number to create a different set of excercises in the assignments, keep de number the same when you want to rebuild the same assigments again
# more params can be found in collect_desired_question_bank_exercises_for_one_assignment

# --- GLOBAL VARIABLES these should not be changed
token = os.environ.get("WOOTS_API_TOKEN")
get_header = {"accept": "application/json", "Authorization": "Bearer "+token}
post_header = {"accept": "application/json", "Authorization": "Bearer "+token, "Content-Type": "application/json"}

question_bank_exercises = []

exercises_info = [] 
exercises_cache_path = f"__repo{question_bank_id}_exercises__"

desired_exercises = []

# --- FUNCTION DEFINITIONS
from utils import print_rule, print_header, print_fail

def print_question_banks():
    print_header('Print question banks')
    api_url = "https://app.woots.nl/api/v2/question_banks"
    response = requests.get(api_url, headers=get_header)
    if response.status_code == 200:
        for bank in response.json():
            print(bank['id'], bank['name'])
    else:
        print(response.status_code, response.reason)

def write_json_to_file_in_path(obj, filename, path):
    assert os.path.exists(path), f"Path `{path}` does not exist."
    with open(os.path.join(path, f"{filename}.json"), "w") as file:
        file.write(json.dumps(obj))

def store_question_bank_exercises_and_objectives(question_bank_id):
    if os.path.exists(exercises_cache_path): 
        print_fail(f"WARNING: Cache already exists. Delete {exercises_cache_path} to rebuild.")
        return
    
    os.mkdir(exercises_cache_path)
    print_header(f"Collect all exercises from bank {question_bank_id}")
    page = 1
    last_page = 1
    api_url = f"https://app.woots.nl/api/v2/question_banks/{question_bank_id}/question_bank_exercises"
    while page <= last_page :
        api_params = {"items": 100, "page": page} 
        response = requests.get(api_url, params=api_params, headers=get_header)
        assert response.status_code == 200, f"{response.status_code} {response.reason}"
        question_bank_exercises.extend(response.json())
        print(f"Page {page}, total exercise count: {len(question_bank_exercises)}")
        last_page = int(response.headers["Total-Pages"])
        page = page + 1
    print_header("# Store info for all exercises in cache, counting")
    counter = 0
    # TODO: this takes long, but we are allowed 500 requests per minute (8+ per second)
    # However, natural speed (without parallellisation) is 3+ per second already.
    # So at most, a speedup of 3x is feasible. Not worth it, I guess.
    for exercise in question_bank_exercises:
        api_url = f"https://app.woots.nl/api/v2/exercises/{exercise['id']}/questions"
        response = requests.get(api_url, headers=get_header)
        assert response.status_code == 200, f"{response.status_code} {response.reason}"
        questions = response.json()
        if len(questions) > 0 : # not all excercises contain a question
            api_url = f"https://app.woots.nl/api/v2/questions/{questions[0]['id']}"
            response = requests.get(api_url, headers=get_header)
            assert response.status_code == 200, f"{response.status_code} {response.reason}"
            question = response.json()
            question_info = {"id": exercise['id'], "name": exercise['name'], \
                             "question0_id": question['id'], "question0_objectives": question['objectives']}
            write_json_to_file_in_path(question_info, exercise['id'], exercises_cache_path)
            exercises_info.append(question_info)
            counter = counter + 1
            print(counter)

def read_question_bank_exercises_and_objectives():
    print_header(f"Read all exercises and objectives in {exercises_cache_path}")
    global exercises_info
    assert os.path.exists(exercises_cache_path), f"Cannot read exercises and objectives. Path {exercises_cache_path} does not exist."
    files = os.listdir(exercises_cache_path)
    for filename in files:
        exercise_info = json.loads(open(os.path.join(exercises_cache_path, filename), "r").read())
        exercises_info.append(exercise_info)
    print(f"Read {len(exercises_info)} exercises from cache.")

def collect_desired_question_bank_exercises_for_one_assignment(jaar, hoofdstuk, deel):
    global desired_exercises
    # RIP: This is where an expensive bug / typo was. Wrong ID led to non-creation of assignments
    # API error was a confusing 404 Not Found on the POST request
    part1_intro_excercise_id = "23001415" # vertaal FA-NL
    part2_intro_excercise_id = "23001416" # vertaal NL-FA
    part3_intro_excercise_id = "23001417" # grammatica
    part1_max_exercises = 10
    part2_max_exercises = 10
    part3_max_exercises = 10

    # this must be possible in a shorter and readable way in python, but it works
    print_header(f"Collect desired question bank exercises from {question_bank_id}")

    # MAYBE TODO: doesn't work when different objectives have samen name, currently that is not the case, but it depends on choosen objectives
    # part 1 , vertaal FA-NL
    max_exercises = part1_max_exercises
    desired_exercises.append(part1_intro_excercise_id)
    part_desired_exercises = []
    for exercise_info in exercises_info:
            vrgtaal = "<div>FA-NL</div>"
            vrgtype = "<div>mpc</div>"   
            if deel == "<div>ABCD</div>" :
                paragraaf1 = "<div>A</div>"   
                paragraaf2 = "<div>B</div>"   
            elif deel == "<div>EFGH</div>" :
                paragraaf1 = "<div>E</div>"   
                paragraaf2 = "<div>F</div>"   
            jaar_found = False
            hoofdstuk_found = False
            deel_found = False
            paragraaf_found = False
            vrgtaal_found = False
            vrgtype_found = False
            for objective in exercise_info['question0_objectives'] :
                if objective['name'] == jaar :
                    jaar_found = True
                if objective['name'] == hoofdstuk :
                    hoofdstuk_found = True
                elif objective['name'] == deel :
                    deel_found = True
                elif objective['name'] == paragraaf1 or objective['name'] == paragraaf2:
                    paragraaf_found = True
                elif objective['name'] == vrgtaal :
                    vrgtaal_found = True
                elif objective['name'] == vrgtype :
                    vrgtype_found = True
            if jaar_found and hoofdstuk_found and deel_found and paragraaf_found and vrgtaal_found and vrgtype_found:
                    part_desired_exercises.append(exercise_info['id'])
    print(f"Collected {len(part_desired_exercises)} exercises, need {max_exercises}, removing surplus")
    while len(part_desired_exercises) > max_exercises:
        part_desired_exercises.pop(random.randint(0, len(part_desired_exercises) - 1))
    print(f"Now {len(part_desired_exercises)} exercises left")
    desired_exercises.extend(part_desired_exercises)
    print(desired_exercises)

    # part 2 , vertaal NL-FA
    max_exercises = part2_max_exercises
    desired_exercises.append(part2_intro_excercise_id)
    part_desired_exercises = []
    for exercise_info in exercises_info:
            vrgtaal = "<div>NL-FA</div>"
            vrgtype = "<div>fill</div>"   
            if deel == "<div>ABCD</div>" :
                paragraaf1 = "<div>A</div>"   
                paragraaf2 = "<div>B</div>"   
            elif deel == "<div>EFGH</div>" :
                paragraaf1 = "<div>E</div>"   
                paragraaf2 = "<div>F</div>"   
            jaar_found = False
            hoofdstuk_found = False
            deel_found = False
            paragraaf_found = False
            vrgtaal_found = False
            vrgtype_found = False
            for objective in exercise_info['question0_objectives'] :
                if objective['name'] == jaar :
                    jaar_found = True
                if objective['name'] == hoofdstuk :
                    hoofdstuk_found = True
                elif objective['name'] == deel :
                    deel_found = True
                elif objective['name'] == paragraaf1 or objective['name'] == paragraaf2:
                    paragraaf_found = True
                elif objective['name'] == vrgtaal :
                    vrgtaal_found = True
                elif objective['name'] == vrgtype :
                    vrgtype_found = True
            if jaar_found and hoofdstuk_found and deel_found and paragraaf_found and vrgtaal_found and vrgtype_found:
                    part_desired_exercises.append(exercise_info['id'])
    print(f"Collected {len(part_desired_exercises)} exercises, need {max_exercises}, removing surplus")
    while len(part_desired_exercises) > max_exercises:
        part_desired_exercises.pop(random.randint(0, len(part_desired_exercises) - 1))
    print(f"Now {len(part_desired_exercises)} exercises left")
    desired_exercises.extend(part_desired_exercises)

    # part 3 , grammatica
    max_exercises = part3_max_exercises
    desired_exercises.append(part3_intro_excercise_id)
    part_desired_exercises = []
    for exercise_info in exercises_info:
            vrgtaal = "<div>FA-FA</div>"
            vrgtype1 = "<div>fill</div>"   
            vrgtype2 = "<div>mpc</div>"   
            if deel == "<div>ABCD</div>" :
                paragraaf1 = "<div>D</div>"   
                paragraaf2 = "<div>D</div>"   
            elif deel == "<div>EFGH</div>" :
                paragraaf1 = "<div>H</div>"   
                paragraaf2 = "<div>H</div>"   
            jaar_found = False
            hoofdstuk_found = False
            deel_found = False
            paragraaf_found = False
            vrgtaal_found = False
            vrgtype_found = False
            for objective in exercise_info['question0_objectives'] :
                if objective['name'] == jaar :
                    jaar_found = True
                if objective['name'] == hoofdstuk :
                    hoofdstuk_found = True
                elif objective['name'] == deel :
                    deel_found = True
                elif objective['name'] == paragraaf1 or objective['name'] == paragraaf2:
                    paragraaf_found = True
                elif objective['name'] == vrgtaal :
                    vrgtaal_found = True
                elif objective['name'] == vrgtype1 or objective['name'] == vrgtype2:
                    vrgtype_found = True
            if jaar_found and hoofdstuk_found and deel_found and paragraaf_found and vrgtaal_found and vrgtype_found:
                    part_desired_exercises.append(exercise_info['id'])
    print(f"Collected {len(part_desired_exercises)} exercises, need {max_exercises}, removing surplus")
    while len(part_desired_exercises) > max_exercises:
        part_desired_exercises.pop(random.randint(0, len(part_desired_exercises) - 1))
    print(f"Now {len(part_desired_exercises)} exercises left")
    desired_exercises.extend(part_desired_exercises)
    
def create_repo_assignment(question_bank_id, name, exercise_ids, dry_run=False, full_log=False):
    print_header(f"Creating repo assignment based on desired_exercises {'(dry run)' if dry_run else ''}")
    api_url = f"https://app.woots.nl/api/v2/question_banks/{question_bank_id}/question_bank_assignments"
    data = {
  "name": name,
  "digital": True,
  "exercise_ids": exercise_ids,
  "label_id": 1,
  "external_id": "Ext1",
  "trashed": False,
  "grades_settings": {
    "grade_calculation": "formula",
    "rounding": "decimal",
    "grade_formula": "10 - ((10 - 6.0) / (1.00 - 0.75)) * (total - points) / total", # 100% goed = cijfer 10; 75% goed = cijfer 6,0; 50% goed = cijfer 2,0
    "grade_lower_bound": True,
    "grade_lower_limit": 1,
    "grade_upper_bound": True,
    "grade_upper_limit": 10,
    "passed_grade": 5.5,
    "guess_correction": False,
    "guess_correction_lower_bound": False
  }
}
    if full_log:
        print(f"[POST] {api_url} requested with headers:")
        print(post_header)
        print("and data:")
        print(data)
        print("Chosen exercises:")
        print(desired_exercises)

    if not dry_run:
        response = requests.post(api_url, headers=post_header, json=data)
        if response.status_code == 200:
            for exercise in response.json():
                desired_exercises.append(exercise['id'])
        else:
            print_fail(f"{response.status_code}: {response.reason}")
    

# --- WORKFLOW: read all questions 
# read from woots and store in cache (unless cache already exists)
store_question_bank_exercises_and_objectives(question_bank_id) 
# read back from cache
read_question_bank_exercises_and_objectives()

# --- POLYFLOW: create all assignments
jaarlagen = ["1HV", "2H", "3H", "2V", "3V"] # future versions: ["1HV", "2H", "2V", "3H", "3V"]
hoofdstukken = ["H01", "H02", "H03", "H05", "H06", "H07"] # H04 and H08 contain no exam-questions
delen = ["ABCD", "EFGH"]
versies = ["A", "B", "C", "D"]

# Nog geen input voor collect_desired_question_bank_exercises_for_one_assignment:
paragrafen = [[*"ABCD"], [*"EFGH"]]
vraagtaal = ["FA-FA", "FA-NL", "NL-FA"]
vraagomvang = ["woord", "zin"]
vraagtype = ["mpc", "fill", "open"]

def div_of(text):
    return f"<div>{text}</div>"

toetsen = []
for jaarlaag in jaarlagen:
    for hoofdstuk in hoofdstukken:
        for deel in delen:
            for versie in versies:
                combinatie = (jaarlaag, hoofdstuk, deel, versie)
                toetsen.append(combinatie)
print_header(f"POLYFLOW bouwt {len(toetsen)} toetsen.")
print("De eerste is", toetsen[0])
print("De laatste is", toetsen[-1])

titles = []
for i, (jaar, hoofdstuk, deel, versie) in enumerate(toetsen):
    collect_desired_question_bank_exercises_for_one_assignment(*map(div_of, (jaar, hoofdstuk, deel)))
    title = f"Frans {jaar} SO {hoofdstuk} {deel} versie {versie}"
    create_repo_assignment(question_bank_id, title, desired_exercises, False)
    desired_exercises = []
    titles.append([i, title])

[print(f"({i+1}): {title}") for i, title in titles]
