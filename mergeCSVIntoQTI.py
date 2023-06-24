# --- Import dependencies, define global variables
import zipfile, os, io, csv, re
import xml.etree.ElementTree as ET
from utils import print_rule, print_header, print_fail
from datetime import datetime, timezone

export_zip_path = 'export.zip' # export from Woots, used as input for this script
export_folder_path = 'export' 
export_files = {}

# TODO: recognise the question type by file contents
# could make use of the unique identifiers "questionOpen", "questionFill", "questionMC"
# or similarly, the identifiers "titleOpen", "titleFill", "titleMC"
export_open_filename = 'QUE_23001418_1.xml'
export_fill_filename = 'QUE_23001420_1.xml'
export_mc_filename = 'QUE_23001419_1.xml'
export_filenames = { 
    'open': export_open_filename,
    'fill': export_fill_filename,
    'mc': export_mc_filename
}

csv_path = 'questions.csv'
csv_data = []
import_files = {}
import_zip_path = 'import.zip'  # output of this script, for import to Woots
import_folder_path = 'import'

export_manifest = None
resource_strings = {}
import_manifest = None

# TODO: make this work independent on number of lines in qti file
# BUG: size and position of resource lines in manifest did not change, but order did!
# This makes the above todo very important if we want to make new question templates!
first_in_manifest = [18, 35]
second_in_manifest = [36, 53]
third_in_manifest = [54, 71]
export_manifest_resource_open_lines = first_in_manifest
export_manifest_resource_mc_lines = second_in_manifest
export_manifest_resource_fill_lines = third_in_manifest

# --- Unzip the export
def unzip_to_folder():
    assert not os.path.exists(export_folder_path), print(f"{export_folder_path} already exists, please delete is to get rid of odl files")
    if not os.path.exists(export_folder_path):
        os.makedirs(export_folder_path)
    with zipfile.ZipFile(export_zip_path, 'r') as export_zip:
        export_zip.extractall(export_folder_path)

# Read the template QTI files and manifest
def read_files_from_folder():
    for filename in os.listdir(export_folder_path):
        file_path = os.path.join(export_folder_path, filename)

        if os.path.isfile(file_path):
            with io.open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
                export_files[filename] = content

def print_export_files():
    for filename, content in export_files.items():
        print(f"Filename: {filename}")
        print(f"Content:")
        print(content)
        print('---------------------------------------------')

# Read the CSV of types and values
def read_csv_data():
    with open(csv_path, 'r', encoding='utf-8-sig') as csv_file:
        csv_reader = csv.reader(csv_file, delimiter=';')
        header = next(csv_reader)
        for row in csv_reader:
            row_dict = {}
            for i, value in enumerate(row):
                row_dict[header[i]] = value
            csv_data.append(row_dict)

def print_csv_data():
    for question in csv_data:
        print(question)

# --- Generate the new QTI files by find and replace
def generate_qti_content(max=None):
    qti_id_prefix =  datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S') # assure unique qti id 
    for i, question in enumerate(csv_data[:max], start=1):
        print_header(f"Generating QTI for question {i} of type {question['__template__']}")
        filename = f"Q_{qti_id_prefix}{i}.xml"
        identifier = f"Q_{qti_id_prefix}{i}"
        # print(question)
        if(question['__template__'] == 'fill'): 
            import_files[filename] = export_files[export_fill_filename]
            import_files[filename] = import_files[filename].replace('__vraag__', '__vraag__'+question['__meta__'])
            for key in question:
                import_files[filename] = import_files[filename].replace(key, question[key])
            import_files[filename] = import_files[filename].replace(export_filenames['fill'][0:-4], identifier)
            print(import_files[filename])
        
        elif(question['__template__'] == 'open'): 
            import_files[filename] = export_files[export_open_filename]
            import_files[filename] = import_files[filename].replace('__vraag__', '__vraag__'+question['__meta__'])
            for key in question:
                import_files[filename] = import_files[filename].replace(key, question[key])
            import_files[filename] = import_files[filename].replace(export_filenames['open'][0:-4], identifier)
        
        elif(question['__template__'] == 'mc'):
            import_files[filename] = export_files[export_mc_filename]
            import_files[filename] = import_files[filename].replace('__vraag__', '__vraag__'+question['__meta__'])
            for key in question:
                import_files[filename] = import_files[filename].replace(key, question[key])
            import_files[filename] = import_files[filename].replace(export_filenames['mc'][0:-4], identifier)

def print_import_files():
    for filename, content in import_files.items():
        print(f"Filename: {filename}")
        print(f"Content:")
        print(content)
        print('---------------------------------------------')

# --- Generate new manifest
def generate_manifest_building_blocks():
    global export_manifest
    export_manifest = export_files['imsmanifest.xml']
    export_manifest_lines = export_manifest.split('\n')

    # fixed bug: even though arrays are zero-indexed, they are also right exclusive
    # thus, I need b instead of b-1
    a, b = export_manifest_resource_open_lines # line numbers are one-indexed, arrays are zero-indexed
    resource_manifest_open = ''.join(export_manifest_lines[(a-1):(b)])
    
    c, d = export_manifest_resource_fill_lines # line numbers are one-indexed, arrays are zero-indexed
    resource_manifest_fill = ''.join(export_manifest_lines[(c-1):(d)])

    e, f = export_manifest_resource_mc_lines # line numbers are one-indexed, arrays are zero-indexed
    resource_manifest_mc = ''.join(export_manifest_lines[(e-1):(f)])
    
    # print(resource_manifest_open)
    # print(resource_manifest_fill)
    # print(resource_manifest_mc)

    resource_strings['open'] = resource_manifest_open
    resource_strings['fill'] = resource_manifest_fill
    resource_strings['mc'] = resource_manifest_mc

def generate_manifest():
    head, tail = export_manifest.split('<resources>')

    global import_manifest
    import_manifest = head + '<resources>'

    for row, (filename, content) in zip(csv_data, import_files.items()):
        old_identifier = export_filenames[row['__template__']][0:-4]
        new_identifier = filename[0:-4]
        # print(old_identifier, new_identifier)
        
        resource = resource_strings[row['__template__']]
        resource = resource.replace(old_identifier, new_identifier)
        resource = resource.replace('__title__', row['__title__'])
        # print(resource)

        import_manifest = import_manifest + resource

        # print(row)
        # print(filename)
        # print(resource)
        # print('-------------------------------------------------')
    
    import_manifest = import_manifest + '</resources></manifest>'

# Save the questions and manifest to file
def save_files_to_folder():
    assert not os.path.exists(import_folder_path), print(f"{import_folder_path} already exists, please delete is to get rid of odl files") 
    if not os.path.exists(import_folder_path):
        os.makedirs(import_folder_path)

    for filename, content in import_files.items():
        import_filename = os.path.join(import_folder_path, filename)

        with open(import_filename, 'w') as file:
            file.write(content)
    
    global import_manifest
    import_manifest_filename = os.path.join(import_folder_path, "imsmanifest.xml")
    with open(import_manifest_filename, 'w') as file:
        file.write(import_manifest)

# Zip everything, ready to import
def pack_files_into_zip():
    with zipfile.ZipFile(import_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _, files in os.walk(import_folder_path):
            for file in files:
                file_path = os.path.join(root, file)
                zipf.write(file_path, os.path.relpath(file_path, import_folder_path))

# --- Decide which steps to execute
unzip_to_folder()
read_files_from_folder()
# print_export_files()
read_csv_data()
# [print(key, '\t', value) for key, value in csv_data[0].items()]
# print_csv_data()
generate_qti_content()
# print_import_files()
generate_manifest_building_blocks()
generate_manifest()
# print(import_manifest)
save_files_to_folder()
pack_files_into_zip()
