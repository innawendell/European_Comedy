import os
import sys
import pandas as pd
from os import listdir
from os import path
from os.path import isfile, join
import re
import numpy as np
import string 
from collections import Counter
import json
import copy 
regex_pattern = '[А-Я+Ѣ+І]+.\w[А-Я+Ѣ+І]+.\w[А-Я+Ѣ+І]+\w[А-Я+Ѣ+І]|[А-Я+Ѣ+І]+.\w[А-Я+Ѣ+І]+ [А-Я+Ѣ+І] |[А-Я+Ѣ+І]+.\w[А-Я+Ѣ+І]+.\w[А-Я+Ѣ+І]+|[А-Я+Ѣ+І]+.\w[А-Я+Ѣ+І]+|[А-Я+Ѣ+І]+.\w[А-Я+Ѣ+І]+ [А-Я+Ѣ+І]'
 
def process_all_plays(input_directory, output_path, metadata_path, regex_pattern):
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
    all_files = [f for f in listdir(input_directory) if f.count('.txt')>0]
    metadata_df = pd.read_csv(metadata_path, sep='\t')
    for file in all_files:
        play_data_dict = process_play(input_directory+file, metadata_df, input_directory, regex_pattern)
        json_name = output_path +str(file.replace('.txt', '.json')) 
        with open(json_name, 'w') as fp:
            json.dump(play_data_dict, fp, ensure_ascii=False, indent=2)


def split_text(play_file, old_ortho_flag=True):
    """
    The function splits the text into two parts: the first with the dramatic character cast
    and the second one with the text of the play.
    Params:
        play_file - string with the text of the entire play.
        old_ortho_flag - bool, indicating whether the text is in the old Russian orthography.
    Returns:
        cast_text - string, contains the list of the dramatic characters.
        play_text - string, play text aftet the list of dramatic characters.
    """
    if old_ortho_flag:
        acting_characters = 'ДѢЙСТВУЮЩІЕ'
        act = 'ДѢЙСТВІЕ'
    else:
        acting_characters = 'ДЕЙСТВУЮЩИЕ'
        act = 'ДЕЙСТВИЕ'
        
    cast_start_index = play_file.find('{} ЛИЦА'.format(acting_characters)) 
    if cast_start_index == -1:
        cast_start_index = play_file.find('{} <ЛИЦА>'.format(acting_characters))
        if cast_start_index == -1:
            cast_start_index = play_file.find('<{}> ЛИЦА'.format(acting_characters))
            if cast_start_index == -1:
                cast_start_index = play_file.find('ДѢЙСТВУЮЩIЯ ЛИЦА'.format(acting_characters))
    cast_end_index = play_file.find(act)
    cast_text = play_file[cast_start_index:cast_end_index].split('ЛИЦА')[1]
    play_text = play_file[cast_end_index:]
    
    return cast_text, play_text

def identify_character_names(line):
    """
    The function identifies which character names are present in the string
    Params:
        line - each line from string from the text with charcters (split at '\n')
    Returns:
        characters - a list of character names or 0 if not present in that line
    """

    pattern = r'[А-Я+Ѣ+І]+.\w[А-Я+Ѣ+І]+.\w[А-Я+Ѣ+І]+.\w[А-Я+Ѣ+І]+.\w[А-Я+Ѣ+І]+|[А-Я+Ѣ+І]+.\w[А-Я+Ѣ+І]+ [А-Я+Ѣ+І] |[А-Я+Ѣ+І]+.\w[А-Я+Ѣ+І]+.\w[А-Я+Ѣ+І]+.\w[А-Я+Ѣ+І]+|[А-Я+Ѣ+І]+.\w[А-Я+Ѣ+І]+.\w[А-Я+Ѣ+І]+|[А-Я+Ѣ+І]+.\w[А-Я+Ѣ+І]+'
    characters = [name.group() for name in re.finditer(pattern, line)]
    if len(characters) > 0:
        return characters
    else:
        return 0

def handle_alternative_names(line):
    """
    The function helps extract alternative names for each dramatic character in character list.
    Params:
        line - a string corresponding to a line in cast_text.
    Returns:
        cast_dictionary - a dictionary with alternative names for each dramatic character, values are lists of 
        names (strings).
    """
    cast_dictionary = {}
    character_name = identify_character_names(line)[0].strip()
    tag = '<alternative_name'
    alternative_names = line[line.find(tag)+len(tag):line.find('>')].strip().split(', ')
    
    return character_name, alternative_names

def make_reverse_dictionary(cast_dictionary):
    """
    The function allows us to reverse a cast dictionary, so that we could look up the character names in reverse, e.g.
    from 'COUNT' to 'COUNT VIAZEMSKII'.
    Params:
        cast_dictionry -  dictionary where keys are character names as they appear in the cast list and 
                          values are character names as they appear in the play text.
    Returns:
        reverse_cast_dictionary - the dictionary with keys and values reversed.
    """
    reverse_cast_dictionary = {}
    for item in cast_dictionary.items():
        if item[1]['alternative_names']:
            for name in item[1]['alternative_names']:
                reverse_cast_dictionary[name] = item[0]
            
    return reverse_cast_dictionary

def get_collective_number(line):
    """
    The function extracts collective number, i.e., whether a character like guards should be counted as 1 or 2 
    based on the text of the play, from a text line character cast.
    Params:
        line - a string corresponding to a line in dramatic character cast.
    Returns:
        name - dramatic character name
        collective_number - the number corresponding to the dramatic character, e.g. 2.
    """
    name = identify_character_names(line)[0]
    match = re.findall(r'<collective_number \d>', line)
    collective_number = match[-1].split(' ')[-1]

    return name, collective_number.replace('>', '')

def identify_character_cast(cast_string):
    """
    The function parses the string with the dramatic character cast and creates a dictionary with information
    about each dramatic character's alternative names and collective numbers. If no alternative names or 
    collective numbers, None is recorded.
    Params:
        cast_string - a string containing a list of dramatic characters of the play.
    Returns:
        cast - a dictionary where keys are dramatic characters and values are their alternative names 
        and collective numbers.
    """
    cast = {}
    for line in cast_string.split('\n'):
        characters = identify_character_names(line)
        if characters != 0:
            if line.find('<alternative_name')!= -1 and line.find('<collective_number ') != -1:
                character_name, alternative_name  = handle_alternative_names(line)
                _, collective_number = get_collective_number(line)
                cast[character_name] = {'alternative_names': alternative_name, 'collective_number': collective_number}
            elif line.find('<alternative_name')!= -1:
                character_name, alternative_name  = handle_alternative_names(line)
                cast[character_name] = {'alternative_names':alternative_name, 'collective_number': None}
            elif line.find('<collective_number ') != -1:
                character_name, collective_number = get_collective_number(line)
                cast[character_name] = {'alternative_names': None, 'collective_number': collective_number}
                
            else:
                cast[characters[0]] =  {'alternative_names': None, 'collective_number': None}
                
    return cast

def split_a_scene(scene_string):
    """
    The function splits a string of a scene into two parts: first containig the dramatic characters, 
    the second with the text of the scene.
    Params:
        scene_string - string with the text of the scene.
    Returns:
        scene_cast - a string with dramatic characters in the scene.
        scene_itself - a string with the text of the scene, without dramatic characters enumeration.
    """
    starting_with_cast = scene_string[scene_string.find('<cast '):]
    scene_itself = starting_with_cast.replace(starting_with_cast[:starting_with_cast.find('>')]+'>','') 
    scene_cast = starting_with_cast[:starting_with_cast.find('>')].replace('<cast ', '').strip().split(', ')
    
    return scene_cast, scene_itself

def quality_check_cast(cast_list, character_cast_dictionary, reverse_character_cast):
    """
    The function checks if all dramatic characters which are listed for a particular scene can be found
    either in the character_cast_dictionary or reverse_character_cast. This allows us to check for potential errors
    in the text.
    Params:
        cast_list - a list with dramatic characters which are expected in the scene.
        character_cast_dictionary - a dictionary where keys are dramatic character names as they appear in the list,
                                    values are other names used for the same characters in the text.
       reverse_cast_dictionary - a dictionary where keys and values of the character_cast_dictionary are switched.
    Returns:
        No return, raises an error.
    """
    for name in cast_list:
        if name not in character_cast_dictionary:
            if name in reverse_character_cast:
                pass
            else:
                raise Exception("Error. Name not found', name")

def get_scene_status(scene):
    """
    The function checks a scene and identifies its status, whether it is it 'extra' meaning that it marks a dramatic
    character entrance or exit but it is not marked in the publication; 'no_change' means that it is marked in the 
    publication but no change in character cast happens; 'regular' means that that it simply corresponds to the 
    publication, and it is not extra or no change.
    Params:
        scene - a string with the text of a play scene.
    Returns:
        scene_status - either 'regular', 'no_change' or 'extra'.
    """
    if scene.count('SCENE>')== 0 and scene.count('<no_change_SCENE>')==0:
        scene_status = 'regular'
    elif scene.count('<no_change_SCENE>')>0:
        scene_status = 'no_change'
    elif scene.count('SCENE>')>0 and scene.count('<no_change_SCENE>')==0:
        scene_status = 'extra'
    
    return scene_status

def check_alternative_names(name, character_cast_dictionary, reverse_character_cast):
    """
    The function checks if a dramatic character name has any alternative variants.
    Params:
        name - string, dramatic character name.
        character_cast_dictionary, reverse_character_cast - dictionaries for looking up alternative character names.
    """
    try:
        alt_names = character_cast_dictionary[name]['alternative_names']
    except KeyError:
        alt_names = character_cast_dictionary[reverse_character_cast[name]]['alternative_names']
        
    return alt_names

def check_utternaces_by_alternative_names(alt_names, reverse_character_cast, utterances):
    """
    Count utternaces that appear in the text under alternative dramatic character names.
    Params:
        alt_names - a list of alternative names for a dramatic character.
        reverse_character_cast - a dictionary where keys are names as they appear in the text, values- names as they 
                                appear in the list at the beginning of the play.
        utterances - a list of dramatic character names extracted from the text of the scene.
    Returns:
        speaker_total - int, the number of utternaces by a speaker in the scene.
    """
    speaker_total = 0
    for alt in alt_names: 
        try:
            speaker_total+=utterances.count(alt)
        except KeyError:
            speaker_total+=utterances.count(reverse_character_cast[alt])
    
    return speaker_total


def count_utterances(scene_cast, utterances, character_cast_dictionary, reverse_character_cast):
    """
    The function counts the number of utternaces for each dramatic character listed for the scene.
    Params:
        scene_cast - a list of dramatic characters which are present in the scene.
        utterances - a list of dramatic character names extracted from the text of the scene.
        character_cast_dictionary, reverse_character_cast - dictionaries for looking up alternative character names.
    Returns:
        scene_info - a dictionary where keys are dramatic character names and values are numbers of utterances.
    """
    scene_info = {}
    # if there is only one character in a scene, he will have one utterance
    if len(scene_cast) == 1:
            scene_info[scene_cast[0]] = 1
    else:
        for name in scene_cast:
            utterance_count = utterances.count(name)
            if utterance_count != 0:
                scene_info[name] = utterance_count
            # in case the character appears in the text under a different name
            else:
                alt_names = check_alternative_names(name, character_cast_dictionary, reverse_character_cast)
                #in case there are alternative names
                if alt_names:
                    # there may be a few alternative names associated with a character
                    speaker_total = check_utternaces_by_alternative_names(alt_names, reverse_character_cast, utterances)
                    scene_info[name] = speaker_total
                else:
                    scene_info[name] = utterances.count(name)
                    
    return scene_info                 


def compare_two_scenes(cast_one, cast_two):
    """
    The function helps identify if the dramatic character cast changed.
    Params:
        cast_one - a list of characters in scene one.
        cast_two - a list of characters in scene two.
    Returns:
        no_change_scene - 'no_change_scene' if two scenes are the same, None otherwise.
    """
    if set(cast_one) == set(cast_two):
        no_change_scene = 'no_change'
    else:
        no_change_scene = None
    
    return no_change_scene

def count_speaking_characters(scene_summary_dict, scene_cast):
    """
    The function parses scene_summary_dict with information about number of utterances by each character
    and identifies the total number of speakers in the scene.
    Params:
        scene_summary_dict: a dictionary where keys are dramatic characters and values are number of utterances.
        scene_cast - a list of characters present in the scene.
    Returns:
        num_speakers - a number of speaking dramatic characters in the scene.
    """
    num_speakers = len([item[0] for item in scene_summary_dict.items() if item[1] != 0 and item[0] in scene_cast])
    
    return num_speakers


def handle_scene_name_and_count(scene, sc_num, extra_scene_number):
    """
    The function checks the scene status, whether it is extra or not and assigns the number. Extra scenes are counted
    as for example 1.1 the first extra scene of the main scene 1.
    Params:
        scene - text of a scene.
        sc_number - number of the scene as it appears in the order of all scenes for a particular act.
        extra_scene_number - the number of the extra scene for each main scene, e.g. 1.1, 1.2, 1.3 etc. 
    Returns:
        scene_status - whether a scene is regular, no_change, or extra.
        sc_number - number of the main scene.
        extra_scene_number - number of the extra scene.
    """
    sc_num = int(float(sc_num))
    scene_status = get_scene_status(scene)
    if scene_status == 'extra':
        sc_num = str(sc_num)+ '.'+str(extra_scene_number)
        extra_scene_number+=1
    else:
        sc_num +=1
        extra_scene_number = 1
        
    return scene_status, sc_num, extra_scene_number

def check_if_no_change(current_scene_cast, previous_cast, scene_status):
    """
    The function checks if the cast for the new scene is different from the previous scene.
    Params:
        scene_names - a set of scenes names in the order they appear in the text.
        previous_cast - a set of characters in the previous scene.
        scene_status - whether a scene is regular or extra.
    Returns:
        scene_status - a string, updated in case to 'no_change' if the character cast did not change.
    
    """

    # compare the current scene cast with the cast of the previous scene
    no_change = compare_two_scenes(current_scene_cast, previous_cast)
    if no_change:
        scene_status = no_change   

    return scene_status

def parse_scenes(scenes, name_pattern, character_cast_dictionary, reverse_character_cast):
    """
    The function goes through a list of scenes and updates complete_scene_info dictionary with informtion
    about each scene speaking characters, their utterance counts, and percentage of non-speaking characters.
    Params:
        scenes - a list scenes.
        name_pattern - regex experssion for identifying character names.
        character_cast_dictionary, reverse_character_cast - dictionaries for lookup of alternative names 
                                                            for each dramatic character.
    Returns:
        complete_scene_info - a dictionary where keys are scenes and values are dramatic characters and their 
                             utternace counts as well as the number of speakers and percentage of non-speakers.
    """
    other_meta_fields = ['num_speakers', 'perc_non_speakers', 'num_utterances']
    complete_scene_info = {} 
    scene_casts = []
    sc_num = 0
    extra_scene_number = 1
    for scene in scenes:
        scene_status, sc_num, extra_scene_number = handle_scene_name_and_count(scene, sc_num, extra_scene_number)
   
        # split a scene string into two substrings, one with cast, the other - without
        scene_cast, scene_itself = split_a_scene(scene)
        if float(sc_num) > 1:
            scene_status = check_if_no_change(scene_cast, scene_casts[-1], scene_status)
        scene_casts.append(scene_cast)
        #check to make sure all character names are in scene cast as they appear in the play cast
        quality_check_cast(scene_cast, character_cast_dictionary, reverse_character_cast)
        utterances =  [name.group().strip() for name in re.finditer(name_pattern, scene_itself)]
        scene_summary = count_utterances(scene_cast, utterances, character_cast_dictionary, reverse_character_cast)
        scene_summary['num_utterances'] = sum(list(scene_summary.values()))
        scene_summary['num_speakers'] = count_speaking_characters(scene_summary, scene_cast)
        scene_summary['perc_non_speakers'] = round(((len(scene_cast) - scene_summary['num_speakers']) / 
                                              len(scene_cast)) * 100, 3)
        complete_scene_info[str(sc_num)+'_'+str(scene_status)] =  scene_summary
    
    return complete_scene_info

def split_acts(play_text, number_acts, old_ortho_flag):
    """
    The function splits the text of the play into acts. If the number doesn't match expected number, raises an exception.
    Params:
        play_text - string with the text of the play.
        number_acts - the number of acts we expect.
        old_ortho_flag - bool, True if a play is published in the old orthography.
    Returns:
        acts - a list of acts as strings.
        rus_scene - a string with the spelling of 'scene' in Russian in the corresponding orthography.
    """
    if old_ortho_flag == True:
        rus_act = 'ДѢЙСТВІЕ'
        rus_scene = 'ЯВЛЕНІЕ'
    else:
        rus_act = 'ДЕЙСТВИЕ'
        rus_scene = 'ЯВЛЕНИЕ'
    acts = play_text.split(rus_act)[1:]
    if len(acts)!= number_acts:
        raise Exception('The number of acts is not {}.'.format(number_acts))
        
    return acts, rus_scene

def parse_play(play_text, name_pattern, number_acts, old_ortho_flag, 
               character_cast_dictionary, reverse_character_cast):
    """
    The function splits the play into acts and scenes and parses each scene.
    Params:
        play_text - string with the text of the play.
        number_acts - the number of acts we expect.
        old_ortho_flag - bool, True if a play is published in the old orthography.
        character_cast_dictionary, reverse_character_cast - dictionaries for lookup of alternative names 
                                                            for each dramatic character.
    Returns:
        act_info - a dictionary where keys are acts and values are scenes with their info.
    """
    acts, rus_scene = split_acts(play_text, number_acts, old_ortho_flag)
    act_info = {}
    for act_num, act in enumerate(acts, 1):
        scenes = re.split('{}|<extra'.format(rus_scene),act)[1:]
        act_info['act'+'_'+str(act_num)] = parse_scenes(scenes, 
                                                        name_pattern, 
                                                        character_cast_dictionary,
                                                        reverse_character_cast)

    return act_info


def splitting_verse_line(scene):
    """
    The function splits a scene at the end of verse lines.
    Params:
        scene - a string, text of a scene.
    Returns:
        splits - a list of strings split at the end of verse lines.
    """
    splits = re.split('<end_verse_line>|<end_verse_line_interscene_rhyme>', scene)
    
    return splits

def remove_numbers(input_string):
    """
    The helper function removes number from a string.
    """
    if input_string.isalpha() is False:
        numbers = re.findall('\d+',input_string)
        for num in numbers:
            input_string = input_string.replace(num, '')
            
    return input_string


def replace_tags(line):
    """
    The helper function that replaces the text of a stage direction with ' STAGE'
    Params:
        line - a line of text with a stage direction in it.
    Returns:
        line - a line of text with stage directions replaced by ' STAGE'
    """
    for _ in range(line.count('<stage>')):
        stage_direction_text = line[line.find('<stage>')+len('<stage>'):line.find('</stage>')]
        line = line.replace('<stage>'+stage_direction_text+'</stage>', ' STAGE ')
        
    return line

def clean_stage_direction(line):
    """
    The function helps clean a piece of text by removing tags to prepare it for stage direction extraction.
    Params:
        line - a line of play text.
    Returns:
        line - without tags.
    """
    entities = re.findall(r'ЯВЛЕНІЕ +\w+|ЯВЛЕНИЕ +\w+|[А-Я+Ѣ+І]+.\w[А-Я+Ѣ+І]+.\w[А-Я+Ѣ+І]+|[А-Я+Ѣ+І]+.\w[А-Я+Ѣ+І]+', 
                          line)
    punctuation = [symb for symb in string.punctuation + '—' + '\n' + '\t']
    tags = ['extra_SCENE', 'cast', 'no_change_SCENE', 'intermedia', 'stage separator',
            'speaker_clarification', 'speaking_character_no_utterance']              
    for item in tags + punctuation + entities:
        line = line.replace(item, ' ')
        
    return line

def remove_start_end_stage_directions(verse_line):
    """
    The function removes stage directions at the beginning and end of a verse line as they should not be 
    counted as stage direction splitting verse lines.
    Params:
        verse_line - string with the verse line with all stage directions marked as STAGE.
    Returns:
        verse_line - without stage directions at the beginning and end.
    """
    verse_line = verse_line.strip()
    while verse_line[:5]=='STAGE' or verse_line[-5:]=='STAGE':
        if verse_line[-5:]=='STAGE':
            verse_line = verse_line[:-5].strip()
        elif verse_line[:5]=='STAGE':
            verse_line = verse_line[5:].strip()
            
    return verse_line

def estimate_verse_line_splitting_stage_directions(text_string):
    """
    The function counts the number of stage directions that split verse lines, i.e., appear within it but not
    at the beginning or end of a verse line.
    Params:
        text_string - text of the play.
    Returns:
        number_splitting_stage_directions - int 
    """
    # split verse lines
    splits = splitting_verse_line(text_string)
    number_splitting_stage_directions = 0
    for split in splits:
        # remove any numbers that could appear in the string
        line = remove_start_end_stage_directions(
                                                clean_stage_direction(
                                                replace_tags(
                                                remove_numbers(split))))
        number_splitting_stage_directions+= line.count('STAGE')
        
    return number_splitting_stage_directions


def count_number_word_tokens(play_text):
    """
    The function counts the total number of word tokens in stage directions in the entire play.
    The word tokens are split at white spaces.
    Params:
        play_text - str, text of a play.
    Returns:
        total_number_word_tokens - int
    """
    total_number_word_tokens = 0
    indices = []
    for index_pair in zip([i.span()[1] for i in re.finditer(r'<stage>', play_text)], 
                   [i.span()[0] for i in re.finditer(r'</stage>', play_text)]):
        indices.append(index_pair)
    for index_pair in indices:
        stage_direction = play_text[index_pair[0]:index_pair[1]]
        punctuation = [symb for symb in string.punctuation + '—' + '\n' + '\t']
        for punct in punctuation:
            stage_direction = stage_direction.replace(punct, '')
        num_tokens = len(stage_direction.strip().split(' '))
        total_number_word_tokens += num_tokens   
        
    return total_number_word_tokens


def check_end_of_scene(scene_string):
    """
    Check if a scene ends with the end of a verse line or in the middle of a verse line.
    Params:
        scene_string - a string of a line of text.
    Returns:
        True - if the string ends with an end of a verse line
        False - otherwise
    """
    if scene_string[-16:] != '<end_verse_line>': 
        if scene_string[-33:] != '<end_verse_line_interscene_rhyme>':
            return True
        else:
            return False
    else:
        return False

def tackle_alternative_scene(play_text):
    """
    A helper function that replaces alternative tags for scenes (in case they are within <>, meaning not present
    in the publication text).
    """
    play_text = play_text.replace('<ЯВЛЕНІЕ>', 'ЯВЛЕНІЕ').replace('<ЯВЛЕНИЕ>', 'ЯВЛЕНИЕ')
    
    return play_text


def split_scenes(play_text, old_ortho_flag=True):
    """
    The helper function which splits play text into scenes.
    """
    if old_ortho_flag:
        rus_scene = 'ЯВЛЕНІЕ'
    else:
        rus_scene = 'ЯВЛЕНИЕ'
    # make sure the scenes with alternative mark up (where scenes are not using the word ЯВЛЕНІЕ in the text)
    play_text = tackle_alternative_scene(play_text)
    scenes = re.split('{}|<extra'.format(rus_scene),play_text)
    
    return scenes


def verse_split_between_scenes(play_text, old_ortho_flag=True):
    """
    The function calculates the number of scenes that are connected with other scenes via a verse line, rhyme or both.
    Params:
        play_text - string with the text of the play.
        old_ortho_flag - whether the play is in the old Russian orthography.
    Returns:
        scenes_counts - a dictionary with count of scenes with each type of inter-scene connection.
    """
    scenes_counts = {'scenes_split_verses': 0, 'scenes_rhymes': 0, 'both': 0}
    scenes = split_scenes(play_text, old_ortho_flag=True)
    for scene in scenes[1:]:
        if scene.count('<end_verse_line_interscene_rhyme>') > 0:
            scenes_counts['scenes_rhymes'] +=1
        scene_cleaned = replace_tags(remove_numbers(scene)).strip()
        if check_end_of_scene(scene_cleaned):
                entities = re.findall(r'ЯВЛЕНІЕ +\w+|ЯВЛЕНИЕ +\w+|[А-Я+Ѣ+І]+.\w[А-Я+Ѣ+І]+.\w[А-Я+Ѣ+І]+|[А-Я+Ѣ+І]+.\w[А-Я+Ѣ+І]+', 
                                      scene)
                symbols = [symb for symb in string.punctuation + '—' + '\n' + '\t' 
                           if symb not in ['_', '<', '>']] + ['STAGE'] + entities
                for symbol in symbols:
                    scene_cleaned = scene_cleaned.replace(symbol, '').strip()
                if check_end_of_scene(scene_cleaned):
                    scenes_counts['scenes_split_verses']+=1
                    if scene_cleaned.count('<end_verse_line_interscene_rhyme>') > 0:
                        scenes_counts['both']+=1
                        
    return scenes_counts

def estimate_number_scenes(scene_summary):
    """
    The function calcualtes the number of scenes per text and per Iarkho (i.e., as marked by actual dramatic character
    entrances and exits).
    Params:
        scene_summary - a dictionary output of the parse_play function.
    Returns:
        total_number_scenes_per_text - number of scenes as they are printed
        total_number_scenes_iarkho - number of scnes per Iarkho, which he calls mobility coefficient (MC)
    """
    total_number_scenes_per_text = 0
    total_number_scenes_iarkho = 0
    for key in scene_summary.keys():
        # get the number of scenes as it is printed in the text
        total_number_scenes_per_text+=len([scene for scene in scene_summary[key].keys() if scene.count('extra')==0])
        # count scenes as marked by actual entrances and exits                                  
        total_number_scenes_iarkho+=len([scene for scene in scene_summary[key].keys() if scene.count('no_change')==0])
    
    return total_number_scenes_per_text, total_number_scenes_iarkho

def number_speaking_no_change_case(previous_scene, no_change_scene):
    speaking_set = set()
    non_speaking_set = set()
    characters = [key for key in previous_scene.keys() if key not in ["num_utterances", 
                                                         "num_speakers", 
                                                         "perc_non_speakers"]]
    for key in characters:
        if previous_scene[key] > 0 or no_change_scene[key] > 0:
            speaking_set.add(key)
        if previous_scene[key] == 0 or no_change_scene[key]== 0:
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

def remove_combined_scenes(play_dict, values_to_exclude):
    """
    The function removes info about scenes that we have previously combined and calculated combined data
    for in cases when there was no change in character cast.
    Params:
        play_dict - a dictionary with speakers for each scene.
        values_to_exlude - a list of typles where the first value is the act and the other values are scenes.
        
    Returns:
        play_dict - without exluded scenes.
    """
    for value in values_to_exclude:
        result = {key : val for key, val in play_dict[value[0]].items() 
                        if key not in value[1:]}
        play_dict[value[0]] = result
        
    return play_dict

def preprocess_play_summary(play_summary_copy):
    values_to_exclude, speakers, perc_non_speakers = combine_no_change_scenes(play_summary_copy)
    play_summary_updated = remove_combined_scenes(play_summary_copy, values_to_exclude)
    for key in play_summary_updated.keys():
        for scene in play_summary_updated[key]:
            speakers.append((play_summary_updated[key][scene]['num_speakers']))
            perc_non_speakers.append(round(play_summary_updated[key][scene]['perc_non_speakers'], 3))
    
    return speakers, perc_non_speakers

def sigma_iarkho(variants, weights):  
    """ 
    The function allows calculating standard range following iarkho's procedure. 
    Parameters: 
        variants - a list with distinct variants in the ascending order, e.g. [1, 2, 3, 4, 5] 
        weights - a list of weights corresponding to these variants, e.g. [20, 32, 18, 9, 1] 
    Returns: 
        sigma - standard range per iarkho 
    """  
    weighted_mean_variants = np.average(variants, weights=weights)  
    differences_squared = [(variant - weighted_mean_variants)**2 for variant in variants] 
    weighted_mean_difference = np.average(differences_squared, weights=weights)  
    sigma = weighted_mean_difference**0.5  
      
    return sigma 

def parse_play_summary(play_summary):
    """
    The function parses the dictionary with play_summary produced by parse_play function
    and outputs total number of utterances 
    Params:
        play_summary - a dictionary output by parse_play function.
        
    Returns:
        total_utterances_in_play - total number of utterances in a play.
    """
    total_utterances_in_play = 0
    total_non_duologues = 0
    for key in play_summary.keys():
        for scene in play_summary[key].keys():
            total_utterances_in_play += play_summary[key][scene]['num_utterances']         
    
    return total_utterances_in_play

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
                if item != 'num_utterances' and item != 'num_speakers' and item != 'perc_non_speakers':
                    all_present_characters.add(item)
    total_number_present_characters = 0
    for character in play_dictionary['characters'].keys():
        alt_names = play_dictionary['characters'][character]['alternative_names']
        # in case there are alternative names
        if alt_names:
            possible_names = [character] + alt_names
        else:
            possible_names = [character]
        if len(set(possible_names).intersection(set(all_present_characters))) > 0:
            coll_number = play_dictionary['characters'][character]['collective_number']
            # if there is a collective number for this character
            if coll_number:
                total_number_present_characters += int(coll_number)
            else:
                total_number_present_characters += 1
                
    return total_number_present_characters


def percentage_of_each_speech_type(speech_distribution):
    """
    The function calculates the percentage of each speech type (monologue, duologue, non-duologue (meaning not two
    speakers), and over-two speakers) of the total accross all speech types.
    Params:
        speech_distibution - number of scenes with a specified number of speakers.
    Returns:
        speech_types - a dictionary with percentages corresponding to each speech type.
    """
    speech_types = {}
    total_scenes = np.sum([speech_type[1] for speech_type in  speech_distribution])
    speech_types['perc_monologue'] = np.round((np.sum([speech_type[1] for speech_type in  speech_distribution 
                                    if speech_type[0] ==1]) / total_scenes) *100, 2)
    speech_types['perc_duologue'] = np.round((np.sum([speech_type[1] for speech_type in  speech_distribution 
                                    if speech_type[0] == 2])/ total_scenes) * 100, 2)
    speech_types['perc_non_duologue'] = np.round((np.sum([speech_type[1] for speech_type in  speech_distribution 
                                        if speech_type[0] != 2])/ total_scenes) * 100, 2)
    speech_types['perc_over_two_speakers'] = np.round((np.sum([speech_type[1] for speech_type in  speech_distribution 
                                             if speech_type[0] > 2])/ total_scenes) * 100, 2)
    
    return speech_types


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
    speech_types = percentage_of_each_speech_type(speech_distribution)
    av_perc_non_speakers = round(np.mean((perc_non_speakers)), 3)
    
    return speech_distribution, speech_types, av_perc_non_speakers


def process_speakers_features(play_string, play_data, metadata_dict, old_ortho_flag):
    """
    Iarkho's features described in Iarkho's work on the evolution of 5-act tragedy in verse.
    """
    metadata_dict['num_present_characters'] = number_present_characters(play_data)
    metadata_dict['num_scenes_text'] = estimate_number_scenes(play_data['play_summary'])[0]
    metadata_dict['num_scenes_iarkho'] = estimate_number_scenes(play_data['play_summary'])[1]
    play_summary_copy = copy.deepcopy(play_data['play_summary'])
    distribution, speech_types, non_speakers = speech_distribution_iarkho(play_summary_copy)
    metadata_dict['speech_distribution'] = distribution
    metadata_dict['percentage_monologues'] = speech_types['perc_monologue']
    metadata_dict['percentage_duologues'] = speech_types['perc_duologue']
    metadata_dict['percentage_non_duologues'] = speech_types['perc_non_duologue']
    metadata_dict['percentage_above_two_speakers'] = speech_types['perc_over_two_speakers']
    metadata_dict['av_percentage_non_speakers'] = non_speakers
    metadata_dict['sigma_iarkho'] = round(sigma_iarkho(
                                    [item[0] for item in metadata_dict['speech_distribution']],
                                    [item[1] for item in metadata_dict['speech_distribution']]), 3)
    
    return metadata_dict

def process_features_verse(play_string, play_data, metadata_dict, old_ortho_flag):
    """
    Iarkho's features described in the work on Corneille's comedies and tragedies.
    """
    metadata_dict['total_utterances'] = parse_play_summary(play_data['play_summary'])
    metadata_dict['num_verse_lines'] = play_string.count('<end_verse_line>') + play_string.count(
                                       '<end_verse_line_interscene_rhyme>')
    if play_data['free_iambs'] == 1:
        metadata_dict['rescaled_num_verse_lines'] = int(metadata_dict['num_verse_lines'] * .796)
        metadata_dict['dialogue_vivacity'] = round(metadata_dict['total_utterances'] / 
                                             metadata_dict['rescaled_num_verse_lines'], 3)
    else:
        metadata_dict['dialogue_vivacity'] = round(metadata_dict['total_utterances'] / 
                                             metadata_dict['num_verse_lines'], 3)
    metadata_dict['num_scenes_with_split_verse_lines'] = verse_split_between_scenes(
                                                         play_string, old_ortho_flag)['scenes_split_verses']
    metadata_dict['num_scenes_with_split_rhymes'] = verse_split_between_scenes(
                                                    play_string, old_ortho_flag)['scenes_rhymes']
    metadata_dict['percentage_scene_split_verse'] = round((metadata_dict['num_scenes_with_split_verse_lines'] / 
                                                    metadata_dict['num_scenes_iarkho'])*100, 3)
    metadata_dict['percentage_scene_split_rhymes'] = round((metadata_dict['num_scenes_with_split_rhymes'] / 
                                                    metadata_dict['num_scenes_iarkho'])*100, 3)
    metadata_dict['num_scenes_with_split_rhymes_verses'] = verse_split_between_scenes(
                                                            play_string, old_ortho_flag)['both']
    metadata_dict['num_open_scenes'] = (metadata_dict['num_scenes_with_split_verse_lines'] + 
                                        metadata_dict['num_scenes_with_split_rhymes'] - 
                                        metadata_dict['num_scenes_with_split_rhymes_verses'])
    metadata_dict['percentage_open_scenes'] = round((metadata_dict['num_open_scenes']/
                                              metadata_dict['num_scenes_iarkho']) * 100, 3)
    metadata_dict['percentage_scenes_rhymes_split_verse'] = round((metadata_dict['num_scenes_with_split_rhymes_verses']/
                                                            metadata_dict['num_scenes_iarkho']) * 100, 3)
    
    return metadata_dict

def process_stage_directions_features(play_string, play_data, metadata_dict, cast_string, old_ortho_flag):
    """
    Sperantov's stage-directions features
    """
    if play_data['free_iambs'] == 1:
        number_verse_lines = metadata_dict['rescaled_num_verse_lines']
    else:
        number_verse_lines = metadata_dict['num_verse_lines']
    entire_text = play_string + cast_string
    metadata_dict['num_stage_directions'] = entire_text.count('<stage>')
    metadata_dict['stage_directions_frequency'] = round((metadata_dict['num_stage_directions'] /
                                                  number_verse_lines) * 100, 3)
    metadata_dict['num_word_tokens_in_stage_directions'] = count_number_word_tokens(entire_text)
    metadata_dict['average_length_of_stage_direction'] = round(metadata_dict['num_word_tokens_in_stage_directions']/
                                                        metadata_dict['num_stage_directions'], 3)
    metadata_dict['num_verse_splitting_stage_directions'] = estimate_verse_line_splitting_stage_directions(play_string)
    metadata_dict['degree_of_verse_prose_interaction'] = round((metadata_dict['num_verse_splitting_stage_directions'] /
                                                         number_verse_lines) * 100, 3)
    
    return metadata_dict

def percentage_of_scenes_discont_change(play_string, play_data, metadata_dict, old_ortho_flag):
    """
    The function calculates percentage of scenes with a discontinuous change of dramatic characters, i.e., when no
    a single dramatic character from the scene 1 re-appears in the next scene, e.g., scene 1. FILIPIN, ANGELIQUE. 
    scene 2. ORONTE.
    Params:
        play_string - string, play text.
        play_data - a dictionary with information about the play.
        metadata_dict - a dictionary where we are storing play features; eventually will be combined with play_data.
        old_ortho_flag - bool, True if the text is in the old Russian orthogoraphy.
    Returns:
        metadata_dict - updated with the new feature, i.e., percentage_scenes_with_discontinuous_change_characters.
    """
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
    
def additional_metadata(play_string, play_data, cast_string, old_ortho_flag):
    """
    Process all play features in stages
    """
    metadata_dict = {}
    for process in [process_speakers_features, process_features_verse, 
                    process_stage_directions_features, percentage_of_scenes_discont_change]:
        if process == process_stage_directions_features:
            metadata_dict = process(play_string, play_data, metadata_dict, cast_string, old_ortho_flag)
        else:
            metadata_dict = process(play_string, play_data, metadata_dict, old_ortho_flag)

    return metadata_dict


def add_play_info(metadata):
    """
    Update play metadata from the metadata_df.
    """
    play_data = {}
    play_data['title'] = metadata[0][0]
    play_data['author'] = metadata[0][1] + ', ' + metadata[0][2]
    play_data['creation_date'] = metadata[0][3]
    play_data['free_iambs'] = metadata[0][4]
    
    return play_data

def process_play(file_name, metadata_df, input_path, regex_pattern):
    """
    The function parses a txt file and creates a summary with features and metadata for the play.
    Params:
        file_name - a string, name of the file with the play text.
        metadata_df - a dataframe containing the info about the play.
        input_path - path where the txts are stored.
        regex_pattern - pattern which helps find dramatic characters.
    Returns:
        play_data - a dictionary with detailed play summary by scenes, metadata, and features
    """
    print(file_name)
    play_index = file_name.replace(input_path, '').replace('.txt', '')
    play_meta = metadata_df[metadata_df['index']==play_index][['title', 'last_name', 
                                                            'first_name', 'creation_date',
                                                            'free_iambs']].values                                                      
    comedy = open(file_name, 'r') .read()
    number_acts = int(metadata_df[metadata_df['index']==play_index]['num_acts'].values[0])

    # add logic for detecting if the text is in old orthography
    if comedy.count('Ѣ') >0:
        old_ortho_flag=True
    else:
        old_ortho_flag=False
    # split the text into the part with the cast names and the play itself
    cast_text, play_text = split_text(comedy, old_ortho_flag)

    character_cast_dictionary = identify_character_cast(cast_text)
    reverse_character_cast = make_reverse_dictionary(character_cast_dictionary)
    play_data = add_play_info(play_meta)
    play_data['characters'] = character_cast_dictionary.copy()
    play_data['play_summary'] = parse_play(play_text, regex_pattern, 
                                          number_acts, old_ortho_flag, 
                                          character_cast_dictionary, 
                                          reverse_character_cast)
    play_data['metadata'] = additional_metadata(play_text, play_data, cast_text, old_ortho_flag)
    
    return play_data
