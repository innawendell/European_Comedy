import numpy as np
import pandas as pd
import docx2txt
import re
import json
from os import listdir
from collections import Counter
import copy
from text_processing import text_processing_functions as tpf
from text_processing import russian_tei_functions as rtf

def process_all_plays(input_directory, output_path, metadata_path):
    """
    The function allows to process all files in a specified directory.
    Params:
        input_directory - the path to the folder containing the txt files
        output_path - directory in which the json summaries will be saved.
        metadata_path - path to the metadata file, a tab-delimited txt file with informtion about all plays.
        regex_pattern - a regex pattern which identifies dramatic character names.
    Returns:
        no returns, the files will be saved in output_path directory.
    """
    all_files = [f for f in listdir(input_directory) if f.count('.docx')>0]
    metadata_df = pd.read_csv(metadata_path, sep='\t')
    for file in all_files:
        print(file)
        play_data_dict = process_play(input_directory+file, metadata_df, input_directory)
        json_name = output_path + 'F_' + str(file.replace('.docx', '.json')) 
        with open(json_name, 'w') as fp:
            json.dump(play_data_dict, fp, ensure_ascii=False, indent=2)

            
def parse_characters(play_text):
    """
    The function creates a dictionary where the keys are dramatic characters and values are their collective_numbers if applicable.
    Params:
        play_text - a string with the play summary.
    Returns:
        characters_summary - the dictionary with dramatic character info.
    """
    play_text = play_text.replace('\n\n', '\n')
    characters_summary = {}
    characters = play_text[play_text.find('LES ACTEURS')+len('LES ACTEURS'):
                                   play_text.find('ACTE 1')]
    noise = ['', ' ', '\xa0', '-', '–', '/']
    dramatic_characters = [character.strip() for character in characters.split('\n') if character not in noise]
    for character in dramatic_characters:
        collective_number = re.findall('\d', character)
        if len(collective_number) == 0:
            characters_summary[character] = {'collective_number': None}
        else:
            number = collective_number[0]
            character = character.replace(number, '').strip()
            characters_summary[character] = {'collective_number': int(number)}
    
    return characters_summary


def speach_analysis(scene_characters, characters_dict):
    """
    The function counts the number of speaking and non-speaking characters.
    Params:
        scene_characters - a dictionary where keys are dramatic characters who are present in the scene
        and values are 'speaking' or 'non-speaking'.
        characters_dict - a dictionary with the info about evey dramaic character of the play.
    Returns:
        speech_dict - the dictionary with the number of speaking and non-speaking characters in the scene.
    """
    speach_dict = {'number_speaking_characters': 0, 'number_non_speaking_characters':0}
    characters = [key for key in scene_characters.keys() if key not in ['num_speakers']]
    for character in  characters:
        collective_num = characters_dict[character]['collective_number']
        if scene_characters[character] == 'speaking' and collective_num == None:
            speach_dict['number_speaking_characters'] += 1
        elif scene_characters[character] == 'speaking' and collective_num != None:
            speach_dict['number_speaking_characters'] += characters_dict[character]['collective_number']
        elif scene_characters[character] == 'non_speaking':
            speach_dict['number_non_speaking_characters'] += 1
    speach_dict['percentage_non_speaking'] = round((speach_dict['number_non_speaking_characters'] / 
                                                    len(characters)) * 100, 3)              
    return speach_dict


def character_parsing(names, characters):
    """
    The function processes a scene and counts the number of speaking and non-speaking characters.
    Params:
        names - lines of strings with dramatic character names accompanied by "МОЛЧИТ" in case they are not speaking.
        characters - a dictionary with the info about evey dramaic character of the play.
    Returns:
        scene_characters - the dictionary with the number of speaking and non-speaking characters in the scene.
    """
    scene_characters = {}
    for name in names:                 
        symbols = ['-', '–', '*', '/']
        for symbol in symbols:
            name = name.replace(symbol, '')
        if name.lower().count('молчит')> 0 :
            name = name.lower().replace('молчит', '').upper()
            speaking_status = 'non_speaking'
        else:
            speaking_status = 'speaking'
        name = name.strip()
        if name.isdigit() == False and name != '':
            scene_characters[name] = speaking_status
    speech_dict = speach_analysis(scene_characters, characters)
    scene_characters['num_speakers'] = speech_dict['number_speaking_characters']
    scene_characters['perc_non_speakers'] = speech_dict['percentage_non_speaking']
    
    return scene_characters


def parse_scenes(scenes,  characters):
    """
    The function proceses the scenes and creates a scene summary, i.e., a dictionary where keys are scen numbers with 
    statuses, for example "1_regular" and keys are dramatic characters and their speaking statuses 
    (speaking or non_speaking). 
    Scene statuses incluse: regular - if a scene is the same as is given in the publication.
                            extra - if a scene was added by us in the markup indicating an entrace or exit of a 
                            dramatic character.
                            no_change - if a scene has the same dramatic characters as the scene before it.
    Returns:
        scene_summary - a dictionary where keys are scenes and dramatic characters are values.
    """
    scene_summary = {}
    noise = ['', ' ', '\xa0', '-', '–', '/']
    extra_scene_number = 1
    regular_num = 1
    for scene in scenes:
        names = [name.strip() for name in scene[1:].split('\n') if name not in noise]
        if scene[0].isdigit() and scene[1:5].count('*') == 0:
            scene_name = str(regular_num) +'_regular'
            regular_num += 1
            extra_scene_number = 1
        elif scene[0].isdigit() and scene[1:5].count('*') > 0:
            scene_name =  str(regular_num) + '_no_change'
            regular_num += 1
            extra_scene_number = 1
        else: 
            scene_name =  str(regular_num - 1)+'.' + str(extra_scene_number) +'_extra'
            extra_scene_number += 1
        scene_summary[scene_name] = character_parsing(names,  characters)
    
    return scene_summary


def process_play_summary(play_data, play_text):
    play_data['characters'] = parse_characters(play_text)
    play_summary = {}
    noise = ['', ' ', '\xa0', '-', '–', '/']
    acts = [act for act in play_text[play_text.find('ACTE 1'):].split('ACTE') if act not in noise]
    for act_num, act in enumerate(acts, 1):
        scenes =   [scene.strip() for scene in act.split('SCENE')][1:]
        play_summary['act_'+ str(act_num)] = parse_scenes(scenes,  play_data['characters'])
    play_data['play_summary'] = play_summary
    
    return play_data


def number_speaking_no_change_case(previous_scene, no_change_scene):
    """
    The function handles such instances when there is no change in the character cast between two scenes, therefore,
    according to Iarkho's methodology, they should be counted as one scene. The function calculates the number 
    of speakers and percentage of non-speaking characters.
    
    Params:
        previous_scene - the first of the two scenes between which no change of cast happens.
        no_change_scene - the second of the two scenes between which no change of cast happens.
    """
    speaking_set = set()
    non_speaking_set = set()
    for key in previous_scene.keys():
        if previous_scene[key] =='speaking' or no_change_scene[key]=='speaking':
            speaking_set.add(key)
        if previous_scene[key] =='non_speaking' or no_change_scene[key]=='non_speaking':
            non_speaking_set.add(key)
    num_non_speaking = len(non_speaking_set.difference(speaking_set))
    num_speaking = len(speaking_set)
    perc_non_speaking = round((num_non_speaking / (num_non_speaking + num_speaking)) * 100, 3)
    
    return num_speaking, perc_non_speaking


def combine_no_change_scenes(play_summary):
    which_to_exclude = []
    speakers = []
    perc_non_speakers = []
    for act in play_summary.keys():
        analysed_scenes = []
        for scene in list(play_summary[act].keys()):
            if scene.count('no_change') > 0:

                num_speaking, perc_non_speaking = number_speaking_no_change_case(
                                                  play_summary[act][analysed_scenes[-1]],
                                                  play_summary[act][scene])
                speakers.append(num_speaking)
                perc_non_speakers.append(perc_non_speaking)
                which_to_exclude.append((act, scene, analysed_scenes[-1]))
            analysed_scenes.append(scene)
    
    return which_to_exclude, speakers, perc_non_speakers


def preprocess_play_summary(play_summary_copy):
    values_to_exclude, speakers, perc_non_speakers = combine_no_change_scenes(play_summary_copy)
    play_summary_updated = tpf.remove_combined_scenes(play_summary_copy, values_to_exclude)
    for key in play_summary_updated.keys():
        for scene in play_summary_updated[key]:
            speakers.append((play_summary_updated[key][scene]['num_speakers']))
            perc_non_speakers.append(round(play_summary_updated[key][scene]['perc_non_speakers'], 3))
    
    return speakers, perc_non_speakers


def speech_distribution_iarkho(play_summary_copy):
    """
    The function creates speech distrubution per Iarkho, i.e., the number of speaking characters by number of scenes.
    Params:
        play_summary - a dictionary output by parse_play function.
    Returns:
        speech_distribution - a list of tuples were the 0 element is the number of speaking characters
                              and the 1 element is the number of scenes with such number of speaking characters.
    """
    
    speakers, perc_non_speakers = preprocess_play_summary(play_summary_copy)
    counter = Counter
    counted = counter(speakers)
    speech_distribution = sorted(counted.items(), key=lambda pair: pair[0], reverse=False)
    speech_types = tpf.percentage_of_each_speech_type(speech_distribution)
    av_perc_non_speakers = round(np.mean((perc_non_speakers)), 3)
    
    return speech_distribution, speech_types, av_perc_non_speakers

def number_present_characters(play_dictionary):
    """
    The function calculates the number of characters present in the play. If a character is listed in cast, but doesn't
    appear on stage, he/she doesn't count.
    Params:
        play_dictionary - a dictioanry with data for the play, which includes the characters present in each scene.
    Returns:
        total_number_present_characters - int.
    """
    all_present_characters = set()
    for key in play_dictionary['play_summary'].keys():
        for scene in play_dictionary['play_summary'][key]:
            for item in play_dictionary['play_summary'][key][scene].keys():
                if item != 'num_speakers' and item != 'perc_non_speakers':
                    all_present_characters.add(item)
    total_number_present_characters = 0
    if len(set(all_present_characters).difference(set(play_dictionary['characters']))) > 0:
        print('Error. Incorrect character name present in a scene.')
    appearing_on_stage = set(play_dictionary['characters']).intersection(all_present_characters)
    for character in appearing_on_stage: 
        coll_number = play_dictionary['characters'][character]['collective_number']
        # if there is a collective number for this character
        if coll_number:
            total_number_present_characters += int(coll_number)
        else:
            total_number_present_characters += 1

    return total_number_present_characters


def process_speakers_features(play_data, metadata_dict):
    """
    Iarkho's features described in Iarkho's work on the evolution of 5-act tragedy in verse.
    """
    metadata_dict['num_present_characters'] = number_present_characters(play_data)
    scenes = tpf.estimate_number_scenes(play_data['play_summary'])
    metadata_dict['num_scenes_text'] = scenes[0]
    metadata_dict['num_scenes_iarkho'] = scenes[1]
    play_summary_copy = copy.deepcopy(play_data['play_summary'])
    distribution, speech_types, non_speakers = speech_distribution_iarkho(play_summary_copy)
    metadata_dict['speech_distribution'] = distribution
    metadata_dict['percentage_monologues'] = speech_types['perc_monologue']
    metadata_dict['percentage_duologues'] = speech_types['perc_duologue']
    metadata_dict['percentage_non_duologues'] = speech_types['perc_non_duologue']
    metadata_dict['percentage_above_two_speakers'] = speech_types['perc_over_two_speakers']
    metadata_dict['av_percentage_non_speakers'] = non_speakers
    metadata_dict['sigma_iarkho'] = round(tpf.sigma_iarkho(
                                    [item[0] for item in metadata_dict['speech_distribution']],
                                    [item[1] for item in metadata_dict['speech_distribution']]), 3)
    
    return metadata_dict


def percentage_of_scenes_discont_change(play_data, metadata_dict):
    number_scenes = metadata_dict['num_scenes_iarkho']
    characters = []
    num_scenes_with_disc_character_change = 0
    for act in play_data['play_summary'].keys():
        for entry in play_data['play_summary'][act].values():
            new_cast = [item for item in entry.keys() if 
                               item not in ['num_speakers', 'perc_non_speakers', 'num_utterances']]
            if len(characters) > 0:
                if len(set(new_cast).intersection(set(characters[-1]))) == 0:
                    num_scenes_with_disc_character_change += 1
            characters.append(new_cast)
    perc_disc = round((num_scenes_with_disc_character_change /number_scenes) * 100, 3) 
    metadata_dict['number_scenes_with_discontinuous_change_characters'] = num_scenes_with_disc_character_change
    metadata_dict['percentage_scenes_with_discontinuous_change_characters'] = perc_disc
    
    return metadata_dict


def metadata_processing(play_string, play_data):
    """
    Process all play features in stages
    """
    metadata_dict = {}
    for process in [process_speakers_features, percentage_of_scenes_discont_change]:
        metadata_dict = process(play_data, metadata_dict)

    return metadata_dict

def add_play_info(metadata):
    """
    Update play metadata from the metadata_df.
    """
    play_data = {}
    play_data['title'] = metadata[0][0]
    first_name = metadata[0][2]
    if type(first_name) != float:
        play_data['author'] = str(metadata[0][1] + ', ' + metadata[0][2]).replace('\xa0', '')
    else:
        play_data['author'] = metadata[0][1].replace('\xa0', '') 
    play_data['date'] = metadata[0][3]
    
    return play_data


def process_play(file_name, metadata_df,  input_path):
    """
    The function parses a txt file and creates a summary with features and metadata for the play.
    Params:
        file_name - a string, name of the file with the play text.
        metadata_df - a dataframe containing the info about the play.
    Returns:
        play_data - a dictionary with detailed play summary by scenes, metadata, and features
    """
    play_index = file_name.replace(input_path, '').replace('.docx', '').replace('F_', '')
    play_meta = metadata_df[metadata_df['index']=='F_' + play_index][['title', 'last_name', 
                                                            'first_name', 'date']].values                                                      
    comedy = docx2txt.process(file_name)
    number_acts = int(metadata_df[metadata_df['index']=='F_'+play_index]['num_acts'].values[0])
    play_data = add_play_info(play_meta)
    play_data = process_play_summary(play_data, comedy)
    play_data['metadata'] = metadata_processing(comedy, play_data)
    
    return play_data

