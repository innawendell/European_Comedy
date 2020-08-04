import os
import pandas as pd
from os import listdir
from os import path
from os.path import isfile, join
import numpy as np
import string 
from bs4 import BeautifulSoup as bs
import string
import json
import re
import copy
from collections import Counter
from text_processing import russian_tei_functions as rtf
from text_processing import text_processing_functions as tpf

def process_all_plays(input_directory, output_path, custom_flag=False, metadata_path=None):
    """
    The function allows to process all files in a specified directory.
    Params:
        input_directory - the path to the folder containing the txt files
        output_path - directory in which the json summaries will be saved.
        metadata_path - path to the metadata file, a tab-delimited txt file with informtion about all plays.
    Returns:
        no returns, the files will be saved in output_path directory.
    """
    all_files = [f for f in listdir(input_directory) if f.count('.xml')>0]
    if custom_flag:
        metadata_df = pd.read_csv(metadata_path, sep='\t')
    else:
        metadata_df = pd.DataFrame()
    for file in all_files:
        play_data_dict = process_play(input_directory+file, metadata_df, custom_flag)
        json_name = output_path +str(file.replace('.xml', '.json')) 
        with open(json_name, 'w') as fp:
            json.dump(play_data_dict, fp, ensure_ascii=False, indent=2)


def process_summary(soup, character_cast_dictionary):  
    act_info = {}
    acts = soup.find_all('div1', {'type': 'act'})
    for act_num, act in enumerate(acts, 1):
        scenes = act.find_all('div2', {'type': ['scene', 'extra_scene', 'complex_scene']})
        act_info['act'+'_'+str(act_num)] = parse_scenes(scenes, 
                                                        character_cast_dictionary)
    return act_info



def process_play(file_name, metadata_df, custom_flag):
    """
    The function parses a txt file and creates a summary with features and metadata for the play.
    Params:
        file_name - a string, name of the file with the play text.
        metadata_df - a dataframe containing the info about the play.
    Returns:
        play_data - a dictionary with detailed play summary by scenes, metadata, and features
    """
    print(file_name)
    with open(file_name, 'r') as file:
        soup = bs(file, 'lxml')
    if custom_flag:
        if file_name.count('/') > 0:
            play_index = file_name.split('/')[-1].replace('.xml', '')
        else:
            play_index = file_name.replace('.xml', '')
        play_meta = metadata_df[metadata_df['index']==play_index][['title', 'last_name', 
                                                                  'first_name', 'date']].values 
        comedy = open(file_name, 'r') .read()
        number_acts = int(metadata_df[metadata_df['index']==play_index]['num_acts'].values[0])
    else:
        play_meta = []
    play_data = add_play_info(play_meta, custom_flag)
    play_data['characters'] = create_character_cast(soup)
    play_data['play_summary'] = process_summary(soup, play_data['characters'])
    play_data['metadata'] = additional_metadata(soup, play_data)
    
    return play_data


def create_character_cast(play_soup):
    """
    The function creates a dictionary where the keys are dramatic characters and values are their alternative names 
    and collective_numbers if applicable.
    Params:
        play_soup - play xml turned into beautiful soup object.
    Returns:
        character_dict - the dictionary with dramatic character info.
    """
    dramatic_characters = play_soup.find_all('castitem')
    character_dict = {}
    for character_tag in dramatic_characters:
        role = character_tag.find_all('role')
        tag = str(role[0])
        xml_id = tag[tag.find('id='):tag.find(' sex')].replace('\"', '').split('=')[-1]
        #in case there is a collective number 
        collective_number = character_tag.find_all('collective_number')
        if len(collective_number) != 0:
            collective_number = int(collective_number[0].get_text())
        else:
            collective_number = None
        character_dict[role[0].get_text()] = {"alternative_names": xml_id,
                                                   "collective_number": collective_number}   
    return character_dict


def get_scene_status(scene):
    """
    The function identifies whether a scene is "regular" (i.e., as presented in the publication) or "extra" 
    according to our custom markup reflecting Iarkho's division into scenes.
    Params:
        scene - beautiful soup object of a scene xml.
    Returns:
        scene_status - a string that can be either "regular" or "extra"
    """
    scene_str = str(scene)
    scene_desc = scene_str[scene_str.find('type='):scene_str.find('>')].replace('\"', '').split('=')[-1]
    if scene_desc.count('extra') > 0:
        scene_status = 'extra'
    else:
        scene_status = 'regular'
        
    return scene_status


def find_speakers(scene):
    """
    The function creates a list of the speakers in a scene in the order of their utterances. 
    The number of times a speaker appears in the list corresponds to the number of utterances the speaker makes.
    Params:
        scene - a beautiful soup object of the scene xml.
    Returns:
        speakers_lst - a list of speakers in the scene.
    """
    speakers_lst = []
    speakers = [utterance['who'] for utterance in scene.find_all('sp')]
    for speaker in speakers:
        speaker_count = str(speaker).count(',')
        #if multiple speakers
        if speaker_count > 0:
            multiple_speakers = str(speaker).split(',')
            [speakers_lst.append(sp.strip()) for sp in multiple_speakers]
        else:
            speakers_lst.append(speaker)
    
    return speakers_lst


def check_cast_vs_speakers(scene_cast_lst, speakers, scene):
    """
    The function helps check for errors in the publication when a dramatic character speaks in a particular scene
    but is not listed in the scene cast.
    Params:
        scene_cast_lst - a list of dramatic characters who are present in the scene.
        speakers - a list of speakers in the scene.
        scene - a beautiful soup object of the scene xml.
    Returns:
        No return, prints an error and details about the characters who speak but are not listed as presesnt 
        as well as the beginning of the scene where this error is.
    """
    speaker_set = set(speakers)
    scene_cast_set = set(scene_cast_lst)
    if len(speaker_set.difference(scene_cast_set)) > 0 and len(scene_cast_lst) >0:
        print('\tERROR.', 'Speak but do not appear in scene cast:',
              speaker_set.difference(scene_cast_set), 
              'Beginning of the scene:', 
              scene_cast_set, str(scene)[:70])


def tackle_name(character_cast_dict, scene_cast, scene):
    """
    The function identifies which dramatic characters appear in the scene cast.
    Params:
        character_cast_dict - a dictionary with dramatic characters for the play.
        scene_cast - a string that contains information about the dramatic characters in the scene.
        scene - a string with the text of the scene that is needed to check if we have speakers who are not in cast.
    Returns:
        sorted_characters - a list of dramatic characters that appear in the scene in the order they are given in the 
                            scene_cast string.
    """
    updated_characters = []
    for name in character_cast_dict.keys():
        index = scene_cast.find(name.lower())
        if index != -1:
            updated_characters.append((name, index))
    sorted_characters = [element[0] for element in sorted(updated_characters, key = lambda x: x[1])]
    
    return sorted_characters


def count_characters(scene_summary_dict):
    """
    The function parses scene_summary_dict with information about number of utterances by each character
    and identifies the total number of speakers and non_speakers.
    Params:
        scene_summary_dict: a dictionary where keys are dramatic characters and values are number of utterances.
    Returns:
        num_speakers - a number of speaking dramatic characters in the scene.
        perc_non_speakers - percentage of non-speaking dramatic characters in the scene.
    """
    summary = [item for item in scene_summary_dict.items() if item[0] != 'num_utterances' and item[0] != 'num_speakers']
    num_speakers = len([item[0] for item in summary if item[1] != 0])
    num_non_speakers = len([item[0] for item in summary if item[1] == 0]) 
    perc_non_speakers =  round((num_non_speakers / len(summary)) * 100, 3)
    
    return num_speakers, perc_non_speakers


def remove_excluded_characters(character_cast_dict, scene_cast_string, scene):
    """
    The function removes characters who are not present in the scene, as marked by 'excepté', 'moins'.
    Params:
        scene_cast_string - a string that contains the characters who are present in the scene.
    Returns:
        scene_cast_string - without excluded characters, if applicable.
    """
    markers = ['excepté', 'moins']
    for marker in markers:
        if scene_cast_string.lower().count(marker) > 0: 
            excluded_chars_string = scene_cast_string[scene_cast_string.lower().find(marker):]
            scene_cast_string = scene_cast_string[:scene_cast_string.find(marker)]
            characters_to_exclude = tackle_name(character_cast_dict, excluded_chars_string, scene)
        else:
            characters_to_exclude = []
    
    return scene_cast_string, characters_to_exclude


def identify_scene_cast(scene, scene_status, character_cast_dict):
    """
    The function parses the scene xml and identifes the string that contains the dramatic characters' who are present 
    in the scene as well as the dramatic characters who should be excluded from the cast, i.e., after "excepté" or
    "moins."
    Params:
        scene - a beautiful soup object of the scene xml.
        scene_status - if a scene_status is "extra" or "complex_scene," the character cast would be given in the markup,
                        e.g., cast="FILIPIN, ORONTE," otherwise, it will follow the scene number, 
                        e.g., SCENE I. Filipin, Oronte.
        character_cast_dict - a dictionary where keys are dramatic characters and values are their alterantive names
                              and collective numbers.
    Returns:
        scene_cast - a string that contains the dramaric characters present in the scene.
        exluded_characters - a list of characters who should be removed from the scene cast.
    """
    if scene_status.count('extra') != 0 or str(scene).count('complex_scene') != 0:
        scene_cast = str(scene)[str(scene).find('cast=\"'):str(scene).find('type')].lower()
    else:
        scene_cast = str(scene)[str(scene).find('>')+1:str(scene).find('<sp')].lower()
    # remove excluded characters 
    scene_cast, excluded_characters = remove_excluded_characters(character_cast_dict, scene_cast, scene)
    
    return scene_cast, excluded_characters


def handle_preceding_scene_characters(scene_cast, previous_cast, characters_current_scene, excluded_characters):
    """
    A scene would often mention that some of the characters are the same as the ones from a previous scene. 
    This function would help us identify such cases and dramatic characters.
    Params:
        scene_cast - a string that contains the dramatic characters listed for the scene.
        previous_cast - a list of dramatic characters who appeared in the previous scene.
        characters_current_scene - a list of dramatic characters that are listed for the scene.
        excluded_characters - a list of characters who are listed as exluded.
    Returns:
        updated_characters - dramatic characters from a scene, including the ones from a previous scene,
                            if applicable.
    """
    if scene_cast.count('précédent') > 0 or scene_cast.count('precedent') > 0 or scene_cast.count('même') > 0:
        characters = [name for name in previous_cast if name not in excluded_characters]
    else:
        characters = []
    updated_characters = characters_current_scene + characters  
    
    return updated_characters


def extract_utterances(character_cast_dict, scene):
    """
    The function identifies all utterances in a scene and creates a list of dramatic characters who
    make those utterances.
    Params:
        character_cast_dict - a dictionary where keys are dramatic characters and values are their alterantive names
                              and collective numbers.
        scene - a beautiful soup object of the scene xml.
    Returns:
        utterance_lst - a list of speakers who make utterances in the given scene.
    """
    # look up by alternative name
    reverse_dict = dict(zip([val['alternative_names'] for val in character_cast_dict.values()], 
                            character_cast_dict.keys())) 
    utterance_lst = [reverse_dict[name] for name in find_speakers(scene)]
    
    return utterance_lst


def count_handler(characters, utterance_lst):
    """
    The function counts how many utterances each speaker pronounces.
    Params:
        characters - a list of dramatic characters present in the scene.
        utterance_lst - a list of speakers who make utterances in the given scene.
    Returns:
        scene_info - a dictionary where keys are dramatic characters and values are the number o utterances they make
    """
    scene_info = {}
    # if no cast is given, use the speakers for scene cast
    if len(characters) == 0:
        characters = set(utterance_lst)
    if len(characters) > 1:
        for character in characters:
            scene_info[character] = utterance_lst.count(character)
    else:
        scene_info[utterance_lst[0]] = 1
        
    return scene_info


def count_utterances(scene, character_cast_dict, previous_cast, scene_status):
    """
    The function counts the number of utterances each dramatic character makes in a given scene.
    Params:
        scene - a beautiful soup object of the scene xml.
        character_cast_dict - a dictionary where keys are dramatic characters and values are their alterantive names
                              and collective numbers.
        characters_current_scene - a list of dramatic characters that are listed for the scene.
        excluded_characters - a list of characters who are listed as exluded.
        scene_status - scene_status - whether a scene is regular or extra.
    Returns:
        scene_ino - a dictionary where keys are charcters and values are the number of utterances.
    """
    scene_info = {}
    scene_cast, excluded_characters = identify_scene_cast(scene, scene_status, character_cast_dict)
    current_scene_characters = tackle_name(character_cast_dict, scene_cast, scene)
    # account for dramatic characters from a previous scene re-appearing in the new scene.
    characters = handle_preceding_scene_characters(scene_cast, 
                                                   previous_cast, 
                                                   current_scene_characters, 
                                                   excluded_characters)
    utterance_lst = extract_utterances(character_cast_dict, scene)
    # run a quality check
    check_cast_vs_speakers(characters, utterance_lst, scene)
    # count how many utterances each speaker makes
    scene_info = count_handler(characters, utterance_lst)
        
    return scene_info, characters


def parse_scenes(scenes, character_cast_dictionary):
    """
    The function goes through a list of scenes and updates complete_scene_info dictionary with informtion
    about each scene speaking characters, their utterance counts, and percentage of non-speaking characters.
    Params:
        scenes - a list scenes.
        name_pattern - regex expression for identifying character names.
        character_cast_dictionary, reverse_character_cast - dictionaries for lookup of alternative names 
                                                            for each dramatic character.
    Returns:
        complete_scene_info - a dictionary where keys are scenes and values are dramatic characters and their 
                             utternace counts as well as the number of speakers and percentage of non-speakers.
    """
    other_meta_fields = ['num_speakers', 'perc_non_speakers', 'num_utterances']
    complete_scene_info = {} 
    scene_names = []
    sc_num = 0
    extra_scene_number = 1
    for scene in scenes:
        scene_status, sc_num, extra_scene_number = rtf.handle_scene_name_and_count(scene, sc_num, extra_scene_number)
        if sc_num != 1 :
            previous_cast = [name for name in complete_scene_info[scene_names[-1]].keys()
                            if name not in other_meta_fields]
        else:
            previous_cast = []
        scene_summary, scene_cast = count_utterances(scene, character_cast_dictionary, previous_cast, scene_status)
        scene_summary['num_utterances'] = sum(list(scene_summary.values()))
        scene_summary['num_speakers'], scene_summary['perc_non_speakers'] = count_characters(scene_summary)
        if float(sc_num) > 1:
            current_scene = [key for key in scene_summary.keys() if key not in other_meta_fields]
            scene_status = tpf.check_if_no_change(current_scene, previous_cast, scene_status)           
        complete_scene_info[str(sc_num) + '_' + str(scene_status)] =  scene_summary
        #check to make sure all character names are in scene cast as they appear in the play cast
        scene_names.append(str(sc_num) + '_' + str(scene_status))

    return complete_scene_info


def count_all_verse_lines(soup):
    all_lines = soup.find_all('l')
    not_init = soup.find_all('l', {"part": "m"}) + soup.find_all('l', {"part": "i"})
    num_verse_lines = len([line for line in all_lines if line not in not_init])
    
    return num_verse_lines


def process_features_verse(play_soup, play_data, metadata_dict):
    """
    Iarkho's features described in the work on Corneille's comedies and tragedies.
    """
    metadata_dict['total_utterances'] = rtf.total_utterances(play_soup)
    metadata_dict['num_verse_lines'] = count_all_verse_lines(play_soup)
    metadata_dict['dialogue_vivacity'] = round(
                                             metadata_dict['total_utterances'] / 
                                             metadata_dict['num_verse_lines'], 3)
    return metadata_dict


def add_play_info(metadata, custom_flag=False):
    """
    Update play metadata from the metadata_df. We can provide our own metadata or use the TEI metadataa
    """
    play_data = {}
    if custom_flag:
        play_data['title'] = metadata[0][0]
        first_name = metadata[0][2]
        if type(first_name) != float:
            play_data['author'] = str(metadata[0][1] + ', ' + first_name).strip()
        else:
            play_data['author'] = metadata[0][1].strip()
        play_data['creation_date'] = metadata[0][3]
    else:
        play_data['title'] = soup.find('titlepart').get_text()
        play_data['author'] = soup.find('docauthor')['id']
        play_data['creation_date'] = int(soup.find('docdate').get_text().replace('.', ''))
        
    return play_data


def additional_metadata(play_soup, play_data):
    """
    Process all play features.
    """
    metadata_dict = {}
    for process in [rtf.process_speakers_features, 
                    process_features_verse, 
                    rtf.percentage_of_scenes_discont_change]:
        metadata_dict = process(play_soup, play_data, metadata_dict)

    return metadata_dict