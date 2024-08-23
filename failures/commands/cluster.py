import argparse
import logging
import textwrap
import re
import pandas as pd
import copy
import json
import csv
import tiktoken
import math

from datetime import datetime

from failures.articles.models import Incident, Theme, SubTheme
from failures.commands.PROMPTS import CLUSTER_PROMPTS, CODING_PROMPTS
from failures.commands.MODEL_INPUTS import OPENAI_THEMES_INPUTS
from failures.networks.models import ChatGPT

CONTEXT_WINDOW = 16385

class ClusterCommand:
    POSTMORTEM_FIELDS = ["SEcauses", "NSEcauses", "impacts", "fixes"]
    THEMES_PATH = "failures/data/"

    def prepare_parser(self, parser: argparse.ArgumentParser):
        """
        Prepare the argument parser for the cluster command.

        Args:
            parser (argparse.ArgumentParser): The argument parser to configure.
        """

        parser.description = textwrap.dedent(
            """
            Cluster postmortem data into themes and subthemes. 
            """
        )
        parser.add_argument(
            "--fields",
            nargs='+',
            choices=self.POSTMORTEM_FIELDS,
            default=self.POSTMORTEM_FIELDS,
            help="A list of incident fields to perform clustering on.",
        )
        parser.add_argument(
            "--ids",
            nargs='+',
            type=int,
            help="List of incident ids.",
        )
        parser.add_argument( #TODO: Not used
            "--delete_themes",
            type=bool,
            help="Boolean to delete themes",
        )
        parser.add_argument(
            "--import_codes",
            type=bool,
            default=False,
            help="Determines whether codes should be imported or regenerated.",
        )
        parser.add_argument(
            "--hitl",
            type=bool,
            default=False,
            help="Human in the loop for whether the generated themes are acceptable.",
        )
        parser.add_argument(
            "--experiment",
            type=bool,
            default=False,
            help="To cluster incidents between 2010 and 2022 for experiment.",
        )

    def run(self, args: argparse.Namespace, parser: argparse.ArgumentParser, articles = None):
        """
        Run the article clustering process based on the provided arguments.

        Args:
            args (argparse.Namespace): The parsed command-line arguments.
            parser (argparse.ArgumentParser): The argument parser used for configuration.
        """

        #TODO: The way the factors, codes, and themes are stored within the script is confusing and inefficient. It should instead be stored in one dictionary. For example, cleaned_data should be: ["SEcauses"]["incident-ID"]["factors"] = list of SE causes and ["SEcauses"]["incident-ID"]["memos"] = memos and their descriptions; it is currently ["SEcauses"] = list of causes, and ["SEcauses_ids"] = incident ids of the causes, and the memos are not stored

        # Get fields to cluster
        postmortem_keys = args.fields
        logging.info(f"Conducting thematic analysis for fields: {postmortem_keys}")

        # Get incidents
        if args.ids:
            incidents = Incident.objects.filter(id__in=args.ids, complete_report=True)
        elif args.experiment:
            start_date = datetime(2010, 1, 1)
            end_date = datetime(2022, 12, 31, 23, 59, 59)

            incidents = Incident.objects.filter(published__range=(start_date, end_date))#, complete_report=True)
        else:
            #incidents = Incident.objects.filter(complete_report=True)
            incidents = Incident.objects.prefetch_related('articles').order_by('-published')[:50] # TODO: Update this to previous line when pipeline is finished
        logging.info(f"Conducting thematic analysis on {len(incidents)} incidents.")

        # Pre-process data to be clustered
        cleaned_data = pre_process_data(incidents, postmortem_keys)
        
        # Contains all information for coded data
        coded_data = {}

        # Store first pass
        themes_first_pass = True
        sub_themes_first_pass = True

        # Iterate through keys and get themes
        for postmortem_key in postmortem_keys:

            logging.info("Conducting thematic analysis for field: " + str(postmortem_key))

            # Specify the file path where you want to save the JSON file
            file_path = f"failures/data/initial_codes_{postmortem_key}.json"

            # Read initial codes in from file
            if args.import_codes == True:
                with open(file_path, 'r') as json_file:
                    initial_codes = json.load(json_file)

            else:
                # Generate initial codes
                initial_codes = get_initial_codes(cleaned_data[postmortem_key], postmortem_key)

                # Open the file in write mode and use `json.dump()` to save the list of dictionaries to the file
                with open(file_path, 'w') as json_file:
                    json.dump(initial_codes, json_file)

            # Remove duplicates
            initial_codes_trimmed = remove_duplicate_codes(initial_codes, postmortem_key)
            if not initial_codes_trimmed:
                logging.info(f"Unable to remove duplicate codes. Skipping coding for {postmortem_key}.")
                continue

            while True: #If human-in-the-loop, then check if the themes are acceptable and loop to generate themes until they are acceptable
                # Create themes
                major_themes = generate_themes(initial_codes_trimmed, postmortem_key)
                if not major_themes:
                    logging.info(f"Unable to get themes. Trying again for {postmortem_key}.")
                    major_themes = generate_themes(initial_codes_trimmed, postmortem_key)

                    if not major_themes:
                        logging.info(f"Unable to get themes (Second try). Skipping coding for {postmortem_key}.")
                        continue

                if args.hitl is True: #If human-in-the-loop, then check if the themes are acceptable
                    acceptable_themes = input("Are the generated themes acceptable? Only return bool True or False: ")
                    if acceptable_themes == "True":
                        acceptable_themes = True
                    else:
                        acceptable_themes = False

                    if acceptable_themes is True:
                        break
                    logging.info("Generated themes were not acceptable. Re-generating themes.")
                else:
                    break

            # Deductively code data based on generated codes
            new_codebook, coded_data[postmortem_key], coded_data[postmortem_key + "_themes"] = code_data(major_themes, cleaned_data[postmortem_key], postmortem_key, initial_codes)
            if not new_codebook or not coded_data[postmortem_key]:
                logging.info(f"Unable to code data. Skipping coding for {postmortem_key}.")
                continue

            # Get clustered data
            major_clusters = get_clustered_data(new_codebook, coded_data[postmortem_key + "_themes"], cleaned_data[postmortem_key + "_ids"])
            # write_dict_to_csv(major_clusters, self.THEMES_PATH + postmortem_key + "_themes.csv")

            # Update theme data
            update_db_themes(postmortem_key, new_codebook, coded_data[postmortem_key + "_themes"], cleaned_data[postmortem_key + "_ids"], themes_first_pass) # TODO: Implement update theme data
            themes_first_pass = False

            # Declare all sub data
            sub_initial_codes = {}
            sub_initial_codes_trimmed = {}
            sub_themes = {}
            sub_new_codebook = {}
            sub_new_coded_data = {}
            sub_clusters = {}

            # Perform run through for sub themes
            for major_theme, data in major_clusters.items():
                # Skip ids
                if major_theme[-4:] == "_ids":
                    continue

                if len(data) < 30:
                    logging.info(f"Skipping sub themes for {major_theme}. Not enough data points.")
                    continue

                logging.info(f"\n\nCreating Sub-Themes for MAJOR THEME: {major_theme}\n\n")
                sub_initial_codes[major_theme] = get_initial_codes(data, postmortem_key, f"In the following tasks, you will be tasked to identify a theme. The theme you identify should be a sub-theme under the larger theme: \"{major_theme}\". Thus, the theme identified in the following tasks should be more specific than the larger theme.\n") # Create sub theme codes
                sub_initial_codes_trimmed[major_theme] = remove_duplicate_codes(sub_initial_codes[major_theme], postmortem_key) # Remove duplicates in sub theme codes
                if not sub_initial_codes_trimmed[major_theme]:
                    logging.info(f"Unable to remove duplicate sub themes within theme {major_theme} for postmortem key {postmortem_key}. Skipping further coding.")
                    continue
                
                logging.info("Generating sub-themes for major theme: " + major_theme)
                
                while True: #If human-in-the-loop, then check if the themes are acceptable and loop to generate themes until they are acceptable   
                    sub_themes[major_theme] = generate_themes(sub_initial_codes_trimmed[major_theme], postmortem_key, f"In the following tasks, you will be tasked to group themes. The themes you identify should be sub-themes under the larger theme: \"{major_theme}\". Thus, the themes identified in the following tasks should be more specific than the larger theme.\n") # Generate sub themes
                    if not sub_themes[major_theme]:
                        logging.info(f"Unable to get sub themes within theme {major_theme} for postmortem key {postmortem_key}. Skipping further coding.")
                        continue
                    
                    if args.hitl is True: #If human-in-the-loop, then check if the themes are acceptable
                        acceptable_themes = input("Are the generated themes acceptable? Only return bool True or False: ")
                        if acceptable_themes == "True":
                            acceptable_themes = True
                        else:
                            acceptable_themes = False

                        if acceptable_themes is True:
                            break
                        logging.info("Generated themes were not acceptable. Re-generating themes.")
                    else:
                        break
                
                # TODO: Update how this is called
                sub_new_codebook[major_theme], sub_new_coded_data[major_theme], sub_new_coded_data[major_theme + "_themes"] = code_data(sub_themes[major_theme], data, postmortem_key, sub_initial_codes[major_theme]) # Code data for sub themes
                if not sub_new_codebook[major_theme] or not sub_new_coded_data[major_theme]:
                    logging.info(f"Unable to code sub themes within theme {major_theme} for postmortem key {postmortem_key}. Skipping further coding.")
                    continue

                # Update sub themes
                update_db_sub_themes(postmortem_key, major_theme, sub_new_codebook[major_theme], sub_new_coded_data[major_theme + "_themes"], major_clusters[major_theme + "_ids"], sub_themes_first_pass)
                sub_themes_first_pass = False

                logging.info("Finished conducting thematic analysis for field: " + str(postmortem_key))


def pre_process_data(incidents, postmortem_keys) -> dict:
    """
    Split up each incident entry into individual factors. Return as a dictionary.
    """
    logging.info("\nPreprocessing data.")
    # Convert incident data to a list of dictionaries
    if "fixes" in postmortem_keys:
        postmortem_keys.append("preventions")
    incidents_list = list(incidents.values('id', *postmortem_keys))
    if "fixes" in postmortem_keys:
        postmortem_keys.remove("preventions")

    # Create a DataFrame from the queryset data
    incidents_df = pd.DataFrame(incidents_list)

    # Dictionary to store cleaned data
    cleaned_data = {}

    # Clean data
    for postmortem_key in postmortem_keys:
        logging.info("\nPreprocessing data for " + postmortem_key +".")
        clean_key = []
        ids = []
        for (id, raw_data) in zip(incidents_df["id"], incidents_df[postmortem_key]):
            raw_data = re.split(r'\d+\.\s*', raw_data) # Split on numbered list
            raw_data = [re.sub(r'\s*\[(?:Article\s+)?\d+(?:,\s*\d+)*\]\s*[\r\n.]?$', '.', data) for data in raw_data]
            clean_key.extend(raw_data[1:])  # Skip the first empty item

            # Store id mappings
            ids.extend([id] * len(raw_data[1:]))

        if postmortem_key == "fixes":
            for (id, raw_data) in zip(incidents_df["id"], incidents_df["preventions"]):
                raw_data = re.split(r'\d+\.\s*', raw_data) # Split on numbered list
                raw_data = [re.sub(r'\s*\[(?:Article\s+)?\d+(?:,\s*\d+)*\]\s*[\r\n.]?$', '.', data) for data in raw_data]
                clean_key.extend(raw_data[1:])  # Skip the first empty item

                # Store id mappings
                ids.extend([id] * len(raw_data[1:]))

        # Store back to output dictionary
        cleaned_data[postmortem_key] = clean_key
        cleaned_data[postmortem_key + "_ids"] = ids

    logging.info("Data has been cleaned and processed for all postmortem keys.")


    return cleaned_data

# Prompt OpenAI LLM
def get_completion(prompt, model="gpt-3.5-turbo"):
    # Initializes ChatGPT 
    chatgpt = ChatGPT()
    inputs = OPENAI_THEMES_INPUTS
    messages = [{"role": "user", "content": prompt}]
    inputs["messages"] = messages
    inputs["response_format"] = {"type": "json_object"}
    logging.info("\nPrompt Inputs: \n")
    logging.info(prompt)
    logging.info("\n")
    response = chatgpt.run(inputs)
    logging.info("\nResponse: \n")
    logging.info(response)
    logging.info("\n")
    return response

def get_initial_codes(input_data: list, postmortem_key: str, pre_prompt: str="") -> list:

    logging.info("\nGetting initial codes for : " + str(postmortem_key))
  
    initial_code_information = [] # All theme information

    # Get themes
    for i, item in enumerate(input_data):

        # Format prompt
        prompt = pre_prompt + CLUSTER_PROMPTS[postmortem_key]['identify_themes'] + "'''" + str(item) + "'''"

        # Get response
        response = get_completion(prompt)

        # Convert response to JSON
        try:
            json_response = json.loads(response)
        except ValueError as e:
            logging.info(f"Couldnt convert GPT response to json for: {response}") # TODO: Convert to logging
            continue

        if not all(key in json_response for key in ["theme", "description"]):
            logging.info(f"Incorrect JSON formatting for response: {json_response}")
            continue

        # Add cause
        json_response["cause"] = item

        # Store information
        logging.info(f"{str(i + 1)} of {len(input_data)}. ({postmortem_key}) data: {item}")
        logging.info(f"{str(i + 1)} of {len(input_data)}. ({postmortem_key}) code: {json_response['theme']}")

        initial_code_information.append(json_response)

    logging.info("\nFinished getting initial codes for : " + str(postmortem_key))
    
    return initial_code_information

def remove_duplicate_codes(input_data: list, postmortem_key: str) -> dict:

    logging.info("\nRemoving duplicate codes for : " + str(postmortem_key))
    
    # Initialize token encoder to determine length
    encoding = tiktoken.encoding_for_model(OPENAI_THEMES_INPUTS["model"])

    # Chunking data to fit in context window
    chunks = []
    curr_chunk = []
    size = 0
    for t in input_data:
        if size + len(encoding.encode(json.dumps(t))) > CONTEXT_WINDOW - 1500:
            size = 0
            chunks.append(curr_chunk)
            curr_chunk = []
        curr_chunk.append(t)
        size += len(encoding.encode(json.dumps(t)))
    chunks.append(curr_chunk)

    # Iterate through chunks and reduce codes
    reduced_codes = {}
    for chunk in chunks:
        # Formate input string
        theme_information_str = ["{\"theme\": \"" + t["theme"] + "\", \"description\": \"" + t["description"] + "\"}" for t in chunk]

        # Format prompt
        prompt = CLUSTER_PROMPTS[postmortem_key]["reduce_themes"] + ",".join(theme_information_str) # TODO: Check if this is above context window

        # Get response
        response = get_completion(prompt)

        try:
            reduced_codes.update(json.loads(response))
        except json.decoder.JSONDecodeError as e:
            logging.info(f"Error decoding JSON (remove_duplicate_codes): {e}")
            # Handle the error here, such as logging it or returning an empty dictionary

    logging.info(f"Duplicate codes removed for postmortem key {postmortem_key}: \n{json.dumps(reduced_codes, indent=4)}")

    return reduced_codes

def generate_themes(input_data: dict, postmortem_key: str, pre_prompt: str="") -> dict:
    
    logging.info("\nGenerating themes for : " + str(postmortem_key))
    
    # Initialize token encoder to determine length
    encoding = tiktoken.encoding_for_model(OPENAI_THEMES_INPUTS["model"])

    # Get total size then partition
    total_size = len(encoding.encode(json.dumps(input_data)))
    num_chunks = math.ceil(total_size / (CONTEXT_WINDOW - 1500))
    chunk_size = math.floor(total_size / num_chunks)

    # Chunking data to fit in context window
    chunks = []
    curr_chunk = {}
    size = 0
    for theme, definition in input_data.items():
        if size + len(encoding.encode(theme + definition)) > chunk_size:
            size = 0
            chunks.append(curr_chunk)
            curr_chunk = {}
        curr_chunk[theme] = definition
        size += len(encoding.encode(theme + definition))
    chunks.append(curr_chunk)

    themes = {}
    for chunk in chunks:
        # Format prompt
        prompt = pre_prompt + CLUSTER_PROMPTS[postmortem_key]["group_themes"] + json.dumps(chunk) # TODO: Check if this is above context window

        # Get response
        response = get_completion(prompt)

        try:
            themes.update(json.loads(response)) ### TODO: the themes are writing over themselves
        except json.decoder.JSONDecodeError as e:
            logging.info(f"Error decoding JSON: {e}")
            # Handle the error here, such as logging it or returning an empty dictionaryx

    logging.info(f"Generated themes for postmortem key {postmortem_key}: \n{json.dumps(themes, indent=4)}")

    return themes

def code_data(codebook: dict, input_data: list, postmortem_key: str, initial_codes: list):
    
    logging.info("\nCoding data with codebook for : " + str(postmortem_key))
    
    # Make a deep copy of codebook to preserve original
    codebook_copy = copy.deepcopy(codebook)

    # Get ID to append new codes
    curr_id = len(codebook_copy) + 1

    # Keep track of coded data and inputs
    coded_data = {}
    added_codes = []
    themes = []

    logging.info("Codebook Before Coding:\n" + json.dumps(codebook_copy, indent=3) + "\n\n")

    prompt_temp = CODING_PROMPTS[postmortem_key]

    for i, data in enumerate(input_data):
        prompt = prompt_temp["str1"] +  prompt_temp["str2"] + json.dumps(codebook_copy) + prompt_temp["str3"] + str(data) + prompt_temp["str4"] + initial_codes[i]["theme"] + prompt_temp["str5"] + initial_codes[i]["description"] + prompt_temp["str6"]

        # Get response
        response = get_completion(prompt)

        # Store value
        coded_item = json.loads(response)

        logging.info(f"Coded item {str(i + 1)} of {str(len(input_data))} data: {data}")
        logging.info(f"Coded item {str(i + 1)} of {str(len(input_data))} code: {coded_item}")
  
        if "description" in coded_item: ### TODO: No longer part of prompt to create a new theme if existing themes aren't appropriate.
            # Store new theme
            codebook_copy[curr_id] = coded_item
            curr_id += 1

            # Code current cause
            coded_data[data] = coded_item["theme"]

            # Remember as new theme
            added_codes.append(coded_item["theme"])

            themes.append(coded_item["theme"])
            continue

        elif not type(coded_item["id"]) == str:
            logging.info(f"Unable to code item: {data}. Got output {response}.")
            logging.info(f"Retrying coding once for {data}")

            prompt = prompt_temp["str1"] +  prompt_temp["str2"] + json.dumps(codebook_copy) + prompt_temp["str3"] + str(data) + prompt_temp["str4"] + initial_codes[i]["theme"] + prompt_temp["str5"] + initial_codes[i]["description"] + prompt_temp["str6"]

            # Get response
            response = get_completion(prompt)

            # Store value
            coded_item = json.loads(response)

            logging.info(f"Coded item (retry): {coded_item}")

            if not type(coded_item["id"]) == str:
                logging.info(f"Unable to code item (second try): {data}. Got output {response}.")
                continue

        coded_data[data] = coded_item["id"]

        # Add theme mapping
        if coded_item["id"] in codebook_copy:
            theme = codebook_copy[coded_item["id"]].copy()
            theme["data"] = data
            theme["codebook_id"] = coded_item["id"]
            themes.append(theme)
        else:
            themes.append("NA")

    logging.info(f"Codebook After Coding ({postmortem_key}):\n" + json.dumps(codebook_copy, indent=3) + "\n\n")

    logging.info(json.dumps(coded_data, indent=4))
    
    logging.info("\nFinished coding data with codebook for : " + str(postmortem_key))

    return codebook_copy, coded_data, themes

def get_clustered_data(codebook: dict, input_data_list: list, id_list: list) -> dict:
    
    logging.info("Group data")
    
    # Make cluster dict with key=theme, value=list of causes within theme
    clusters = {}
    for code in codebook.values():
        clusters[code["theme"]] = []
        clusters[code["theme"] + "_ids"] = []

    # Group data
    for index, item in enumerate(input_data_list):

        if isinstance(item, str):
            logging.info(item)
            try:
                item = json.loads(item)
                if not isinstance(item, dict):
                    logging.info(f"Item {index} is not a dictionary after JSON parsing.")
                    continue
            except json.JSONDecodeError:
                logging.info(f"Item {index} is not a valid JSON string.")
                continue

        theme_id = item["codebook_id"]
        theme = item["theme"]
        data = item["data"]

        if theme_id not in codebook:
            logging.info(f"Invalid code (skipping data point): {data}, {theme}")
            continue

        clusters[codebook[theme_id]["theme"]].append(data)
        clusters[codebook[theme_id]["theme"] + "_ids"].append(id_list[index])

    logging.info(json.dumps(clusters, indent=4))

    for theme, causes in clusters.items():
        if theme[-4:0] == "_ids":
            continue
        logging.info(f"Length of {theme}: {len(causes)}")

    return clusters

def write_dict_to_csv(data: dict, csv_file_path: str):
    # Determine field names from the first dictionary entry
    if not data:
        logging.info("Dictionary is empty. Nothing to write to CSV.")
        return

    fieldnames = list(data[next(iter(data))].keys())

    # Write data to CSV file
    with open(csv_file_path, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        writer.writeheader()
        for key, value in data.items():
            writer.writerow({field: value.get(field, '') for field in fieldnames})

    logging.info(f'Data has been saved to {csv_file_path}')

def update_db_themes(postmortem_key: str, codebook: dict, theme_list: list, id_list: list, delete_themes: bool=False):

    # Delete all themes for postmortem if delete_themes==True
    if delete_themes == True:
        themes_to_delete = Theme.objects.filter(postmortem_key=postmortem_key)
        themes_to_delete.delete()
        sub_themes_to_delete = SubTheme.objects.filter(postmortem_key=postmortem_key)
        sub_themes_to_delete.delete()
        logging.info(f"Deleting themes under postmortem key {postmortem_key}. (delete_themes=={delete_themes})")

    # Create Theme objects based on codebook
    logging.info(f"Creating theme objects for postmortem key: {postmortem_key}.")
    for key, theme_data in codebook.items():
        theme_name = theme_data["theme"]
        description = theme_data["description"]

        # Check if theme for postmortem key already exists
        curr_theme = Theme.objects.filter(postmortem_key=postmortem_key, theme=theme_name).first()

        # If not existing theme, create new object
        if not curr_theme:
            curr_theme = Theme.objects.create(postmortem_key=postmortem_key, theme=theme_name)

        # Update definition
        curr_theme.definition = description
        curr_theme.save()

    # Assign incident ids to themes
    logging.info(f"Mapping incidents to themes for postmortem key: {postmortem_key}.")
    for incident_id, theme_data in zip(id_list, theme_list):
        if isinstance(theme_data, str):
            try:
                theme_data = json.loads(theme_data)
                if not isinstance(theme_data, dict):
                    logging.info(f"Item is not a dictionary after JSON parsing.")
                    continue
            except json.JSONDecodeError:
                logging.info(f"Item is not a valid JSON string.")
                continue

        theme_name = theme_data["theme"]

        # Get incident to add to theme
        incident = Incident.objects.get(pk=incident_id)

        # Get the respective theme
        theme = Theme.objects.filter(postmortem_key=postmortem_key, theme=theme_name)
        
        if not theme:
            logging.info(f"Unable to find theme. Couldn't assign incident {incident_id} to theme \'{theme_name}\' for postmortem key {postmortem_key}.")
            continue
        elif len(theme) > 1:
            logging.info(f"Assigning incident to first theme. More than one theme with theme \'{theme_name}\' for postmortem key {postmortem_key}.")
            
        theme = theme.first()

        # Assign the theme to the incident
        incident.themes.add(theme)

def update_db_sub_themes(postmortem_key: str, major_theme: str, codebook: dict, theme_list: list, id_list: list, delete_themes: bool=False):

    # Delete all themes for postmortem if delete_themes==True
    if delete_themes == True:
        major_theme_objects = Theme.objects.filter(postmortem_key=postmortem_key, theme=major_theme)

        for major_theme_object in major_theme_objects:
            sub_themes = major_theme_object.subthemes.all()
            sub_themes.delete()

        logging.info(f"Deleting all sub themes relating for postmortem key {postmortem_key} and major theme {major_theme}. Due to delete_themes={delete_themes}.")

    # Create Theme objects based on codebook
    logging.info(f"Creating sub theme objects for postmortem key: {postmortem_key}, Major theme: {major_theme}.")
    for key, theme_data in codebook.items():
        print(codebook)
        theme_name = theme_data["theme"]
        description = theme_data["description"]

        # Check if theme for postmortem key already exists
        parent_theme = Theme.objects.filter(postmortem_key=postmortem_key, theme=major_theme).first()
        if parent_theme:
            curr_theme = parent_theme.subthemes.filter(sub_theme=theme_name)
        else:
            curr_theme = None

        # If not existing theme, create new object
        if not curr_theme:
            curr_theme = SubTheme.objects.create(postmortem_key=postmortem_key, sub_theme=theme_name, theme=Theme.objects.filter(postmortem_key=postmortem_key, theme=major_theme).first())
        else:
            curr_theme = curr_theme.first()

        # Update definition
        curr_theme.definition = description

        # Link to major theme
        major_theme_object = Theme.objects.filter(postmortem_key=postmortem_key, theme=major_theme).first()
        curr_theme.theme = major_theme_object
        curr_theme.save()

    # Assign incident ids to themes
    logging.info(f"Mapping incidents to sub themes for postmortem key: {postmortem_key}.")
    for incident_id, theme_data in zip(id_list, theme_list):
        theme_name = theme_data["theme"]

        # Get incident to add to theme
        incident = Incident.objects.get(pk=incident_id)

        # Get the respective theme
        theme = SubTheme.objects.filter(postmortem_key=postmortem_key, sub_theme=theme_name)
        
        if not theme:
            logging.info(f"Unable to find theme. Couldn't assign incident {incident_id} to sub theme \'{theme_name}\' for postmortem key {postmortem_key}.")
            continue
        elif len(theme) > 1:
            logging.info(f"Assigning incident to first sub theme. More than one sub theme with sub theme \'{theme_name}\' for postmortem key {postmortem_key}.")
            
        theme = theme.first()

        # Assign the theme to the incident
        incident.subthemes.add(theme)
        