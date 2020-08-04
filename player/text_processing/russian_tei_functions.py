import os
import pandas as pd
from os import listdir
from os.path import isfile, join
import numpy as np
import string
from bs4 import BeautifulSoup as bs
import string
import json
import re
import copy
from collections import Counter
from text_processing import text_processing_functions as tpf


def process_all_plays(input_directory, output_path, custom_flag=False, metadata_path=None):
    """
    The function allows to process all files in a specified directory.
    Params:
        input_directory - the path to the folder containing the txt files
        output_path - directory in which the json summaries will be saved.
        metadata_path - path to the metadata file, a tab-delimited txt file with informtion about all plays.
        custom_flag - bool, True if you have to supply your custom play metadata, False - to use DraCor's metadata.
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
        # if a file is in a folder
        if file_name.count('/') > 0:
            play_index = file_name.split('/')[-1].replace('.xml', '')
        else:
            play_index = file_name.replace('.xml', '')
        play_meta = metadata_df[metadata_df['index']==play_index][['title', 'last_name',
                                                               'first_name', 'creation_date',
                                                               'free_iambs']].values
        comedy = open(file_name, 'r') .read()
        number_acts = int(metadata_df[metadata_df['index']==play_index]['num_acts'].values[0])
    else:
        play_meta = []
    play_data = add_play_info(play_meta, soup, custom_flag)
    play_data['characters'] = create_character_cast(soup)
    play_data['play_summary'] = process_summary(soup, play_data['characters'])
    play_data['metadata'] = additional_metadata(soup, play_data)

    return play_data


def process_summary(soup, character_cast_dictionary):
    act_info = {}
    acts = soup.find_all('div', {'type': 'act'})
    for act_num, act in enumerate(acts, 1):
        scenes = act.find_all('div', {'type': ['scene', 'extra_scene', 'complex_scene']})
        act_info['act'+'_'+str(act_num)] = parse_scenes(scenes,
                                                        character_cast_dictionary)
    return act_info



def create_character_cast(play_soup):
    dramatic_characters = play_soup.find_all('person')
    character_dict = {}
    for character_tag in dramatic_characters:
        tag = str(character_tag)
        xml_id = tag[tag.find('xml:id='):tag.find('>')].replace('\"', '').split('=')[-1]
        # in case there is a collective number
        collective_number = character_tag.find_all('collective_number')
        if len(collective_number) != 0:
            collect_number = int(collective_number[0].get_text())
        else:
            collect_number = None
        character_dict[character_tag.find_all('persname')[0].get_text()] = {"alternative_names": xml_id,
                                                                            "collective_number": collect_number}
    return character_dict


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
        scene_status, sc_num, extra_scene_number = handle_scene_name_and_count(scene, sc_num, extra_scene_number)
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


def check_utterance(scene):
    utterance_dict = {}
    utterances = scene.find_all('sp')
    for utterance in utterances:
        speaker_count = str(utterance).count('#')
        if speaker_count > 1:
            speaker_string = str(utterance)[str(utterance).find('#'):str(utterance).find('\">')]
            speakers = speaker_string.split(' ')
            for speaker in speakers:
                utterance_dict[speaker] = speaker_string

    return utterance_dict


def multi_word_name(character_cast_dict):
    multi_word = []
    for key in character_cast_dict.keys():
        if key.count(' ') > 0:
            multi_word.append(key)
    if len(multi_word) > 0:

        return True
    else:
        return False


def tackle_name(character_cast_dict, scene_cast):
    updated_characters = []
    for name in character_cast_dict.keys():
        if scene_cast.count(name.lower()) >= 2:
            updated_characters.append(name)
        elif scene_cast.count(name.lower()) == 1:
            if name[-2:] != 'ин' and name[-2:] != 'ов' and name[-2:] != 'ев' and name[-2:] != 'аф':
                updated_characters.append(name)
            elif (scene_cast[scene_cast.find(name.lower()):scene_cast.find(name.lower())+len(name.lower())+1][-1] != 'а'and
                 scene_cast[scene_cast.find(name.lower()):scene_cast.find(name.lower())+len(name.lower())+3][-1] != 'я'):
                     updated_characters.append(name)

    return updated_characters


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
        speaker_count = str(speaker).count('#')
        #if multiple speakers
        if speaker_count > 0:
            multiple_speakers = str(speaker).split(' #')
            [speakers_lst.append(sp.strip()) for sp in multiple_speakers]
        else:
            speakers_lst.append(speaker)

    return speakers_lst


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
    utterance_lst = [reverse_dict[name.replace('#', '')] for name in find_speakers(scene)]

    return utterance_lst


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
              'Listed speakers in cast:',
               scene_cast_set,
              'Beginning of the scene:',
               str(scene)[:150])


def identify_scene_cast(scene, scene_status):
    """
    The function parses the scene xml and identifes the string that contains the dramatic characters' who are present
    in the scene.
    Params:
        scene - a beautiful soup object of the scene xml.
        scene_status - if a scene_status is "extra" or "complex_scene," the character cast would be given in the markup,
                        e.g., cast="FILIPIN, ORONTE," otherwise, it will follow the scene number,
                        e.g., SCENE I. Filipin, Oronte.
    Returns:
        scene_cast - a string that contains the dramaric characters present in the scene.
        exluded_characters - a list of characters who should be removed from the scene cast.
    """
    if scene_status.count('extra') != 0 or str(scene).count('complex_scene') != 0:
        scene_cast = str(scene)[str(scene).find('cast=\"'):str(scene).find('type')].lower()
    else:
        scene_cast = scene.find_all('stage')[0].get_text().lower()

    return scene_cast


def handle_preceding_scene_characters(scene_cast, previous_cast, characters_current_scene):
    """
    A scene would often mention that some of the characters are the same as the ones from a previous scene.
    This function would help us identify such cases and dramatic characters.
    Params:
        scene_cast - a string that contains the dramatic characters listed for the scene.
        previous_cast - a list of dramatic characters who appeared in the previous scene.
        characters_current_scene - a list of dramatic characters that are listed for the scene.
    Returns:
        updated_characters - dramatic characters from a scene, including the ones from a previous scene,
                            if applicable.
    """
    if (scene_cast.count('те же') > 0 or scene_cast.count('прежние') > 0 or scene_cast.count('те ж') > 0 or
        scene_cast.count('тот же') > 0 or scene_cast.count('та же') > 0):
        characters = previous_cast
    else:
        characters = []
    updated_characters = characters_current_scene + characters

    return updated_characters


def count_utterances(scene, character_cast_dict, previous_cast, scene_status):
    """
    The function counts the number of utterances each dramatic character makes in a given scene.
    Params:
        scene - a beautiful soup object of the scene xml.
        character_cast_dict - a dictionary where keys are dramatic characters and values are their alterantive names
                              and collective numbers.
        previous_cast - a list of dramatic characters who were present in the preceding scene.
        scene_status - scene_status - whether a scene is regular or extra.
    Returns:
        scene_info - a dictionary where keys are charcters and values are the number of utterances.
    """
    scene_info = {}
    scene_cast = identify_scene_cast(scene, scene_status)
    current_characters = tackle_name(character_cast_dict, scene_cast)
    # make sure to include previous cast in case some of the characters are the same
    updated_characters = handle_preceding_scene_characters(scene_cast, previous_cast, current_characters)
    utterance_dictionary = check_utterance(scene)
    utterance_lst = extract_utterances(character_cast_dict, scene)
    check_cast_vs_speakers(updated_characters, utterance_lst, scene)
    if len(updated_characters) > 1:
        for character in updated_characters:
            in_scene = '#' + character_cast_dict[character]['alternative_names']
            if len(utterance_dictionary) != 0 and in_scene in utterance_dictionary:
                additional_utterances = len(scene.find_all('sp', {'who': utterance_dictionary[in_scene]}))
            else:
                additional_utterances = 0
            num_utterances = additional_utterances + len(scene.find_all('sp', {'who': in_scene}))
            scene_info[character] = num_utterances
    else:
        scene_info[updated_characters[0]] = 1

    return scene_info, updated_characters


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
    appearing_on_stage = set(play_dictionary['characters']).intersection(all_present_characters)
    for character in appearing_on_stage:
        coll_number = play_dictionary['characters'][character]['collective_number']
        # if there is a collective number for this character
        if coll_number:
            total_number_present_characters += int(coll_number)
        else:
            total_number_present_characters += 1

    return total_number_present_characters


def process_speakers_features(soup, play_data, metadata_dict):
    """
    Iarkho's features described in Iarkho's work on the evolution of 5-act tragedy in verse.
    """
    metadata_dict['num_present_characters'] = number_present_characters(play_data)
    scenes = tpf.estimate_number_scenes(play_data['play_summary'])
    metadata_dict['num_scenes_text'] = scenes[0]
    metadata_dict['num_scenes_iarkho'] = scenes[1]
    play_summary_copy = copy.deepcopy(play_data['play_summary'])
    distribution, speech_types, non_speakers = tpf.speech_distribution_iarkho(play_summary_copy)
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


def total_utterances(play_soup):
    """
    The function parses the dictionary with play_summary produced by parse_play function
    and outputs total number of utterances
    Params:
        play_summary - a dictionary output by parse_play function.

    Returns:
        total_utterances_in_play - total number of utterances in a play.
    """
    total_utterances_in_play = len(play_soup.find_all('sp'))

    return total_utterances_in_play


def count_all_verse_lines(soup):
    all_lines = soup.find_all('l')
    not_init = soup.find_all('l', {"part": "M"}) + soup.find_all('l', {"part": "F"})
    num_verse_lines = len([line for line in all_lines if line not in not_init])

    return num_verse_lines


def verse_split_between_scenes(soup):
    """
    The function calculates percentagees of scenes with split vese, i.e, when one verse is split between two scenes,
    percentage of connected by rhymes(percentage_scene_rhymes), percentage of scenes connected by both rhymes and
    by split verses (percentage_scenes_rhymes_split_verse), and percentage of open scenes, i.e, percentage of scenes
    connected by either rhymes or by
    """
    scenes = soup.find_all('div', {'type': ['scene', 'extra_scene', 'complex_scene']})
    counts = {'scenes_with_split_verse':0, 'scenes_split_rhymes':0, 'both':0, 'open': 0}
    for scene in scenes:
        last_ten_lines = str(scene.find_all('l')[-10:])
        last_line = str(scene.find_all('l')[-1])
        verse = last_line[last_line.find("\""):last_line.find('>')].replace('\"', '').split(' ')[0]
        if verse.count('M') > 0 or verse.count('I') > 0:
            counts['scenes_with_split_verse'] += 1
        if last_ten_lines.count('interscene') > 0:
            counts['scenes_split_rhymes'] += 1
        if (verse.count('M') > 0 or verse.count('I') > 0) and last_ten_lines.count('interscene') > 0:
            counts['both'] += 1
        if verse.count('M') > 0 or verse.count('I') > 0 or last_ten_lines.count('interscene') > 0:
            counts['open'] += 1

    counts['percentage_scene_split_verse'] = round((counts['scenes_with_split_verse'] / len(scenes)) * 100, 3)
    counts['percentage_scene_rhymes'] = round((counts['scenes_split_rhymes'] / len(scenes)) * 100, 3)
    counts['percentage_scenes_rhymes_split_verse'] = round((counts['both'] / len(scenes)) * 100, 3)
    counts['percentage_open_scenes'] = round((counts['open'] / len(scenes)) * 100, 3)

    return counts


def process_features_verse(play_soup, play_data, metadata_dict):
    """
    Iarkho's features described in the work on Corneille's comedies and tragedies.
    """
    metadata_dict['total_utterances'] = total_utterances(play_soup)
    metadata_dict['num_verse_lines'] = count_all_verse_lines(play_soup)
    if "free_iambs" in play_data:
        if play_data['free_iambs'] == 1:
            metadata_dict['rescaled_num_verse_lines'] = round(metadata_dict['num_verse_lines'] * .796, 3)
            metadata_dict['dialogue_vivacity'] = round(
                                             metadata_dict['total_utterances'] /
                                             metadata_dict['rescaled_num_verse_lines'], 3)
    else:
        metadata_dict['dialogue_vivacity'] = round(
                                             metadata_dict['total_utterances'] /
                                             metadata_dict['num_verse_lines'], 3)
    metadata_dict['num_scenes_with_split_verse_lines'] = verse_split_between_scenes(
                                                         play_soup)['scenes_with_split_verse']
    metadata_dict['num_scenes_with_split_rhymes'] = verse_split_between_scenes(
                                                    play_soup)['scenes_split_rhymes']
    metadata_dict['percentage_scene_split_verse'] = verse_split_between_scenes(
                                                    play_soup)['percentage_scene_split_verse']
    metadata_dict['percentage_scene_split_rhymes'] = verse_split_between_scenes(
                                                    play_soup)['percentage_scene_rhymes']
    metadata_dict['num_scenes_with_split_rhymes_verses'] = verse_split_between_scenes(
                                                           play_soup)['both']
    metadata_dict['num_open_scenes'] = verse_split_between_scenes(
                                       play_soup)['open']
    metadata_dict['percentage_open_scenes'] = verse_split_between_scenes(
                                              play_soup)['percentage_open_scenes']
    metadata_dict['percentage_scenes_rhymes_split_verse'] = verse_split_between_scenes(
                                                            play_soup)['percentage_scenes_rhymes_split_verse']

    return metadata_dict


def splitting_verse_line(scene):
    splits = re.split('<l>|<l part="I">', scene)

    return splits


def estimate_verse_line_splitting_stage_directions(play_soup):
    splits = splitting_verse_line(str(play_soup))
    total_num = 0
    for line in splits[1:]:
        # find the index of the end of the verse line
        end = [i for i in re.finditer(r'</l>', line)][-1].span()[0]
        verse_line = line[:end]
        if verse_line.count('</stage>')> 0:
            total_num+=verse_line.count('</stage>')

    return total_num


def count_number_word_tokens(play_soup):
    stage_directions = play_soup.find_all('stage')
    total_number_tokens = 0
    for sd in stage_directions:
        sd = sd.get_text()
        for punct in string.punctuation+'stage'+'\n':
            sd = sd.replace(punct, '')
        total_number_tokens += len(sd.split())

    return total_number_tokens

def process_stage_directions_features(play_soup, play_data, metadata_dict):
    """
    Sperantov's stage-directions features
    """
    if 'free_iambs' in play_data:
        if play_data['free_iambs'] == 1:
            number_verse_lines = metadata_dict['rescaled_num_verse_lines']
    else:
        number_verse_lines = metadata_dict['num_verse_lines']
    metadata_dict['num_stage_directions'] = len(play_soup.find_all('stage'))
    metadata_dict['stage_directions_frequency'] = round((metadata_dict['num_stage_directions'] /
                                                  number_verse_lines) * 100, 3)
    metadata_dict['num_word_tokens_in_stage_directions'] = count_number_word_tokens(play_soup)
    metadata_dict['average_length_of_stage_direction'] = round(metadata_dict['num_word_tokens_in_stage_directions']/
                                                        metadata_dict['num_stage_directions'], 3)
    metadata_dict['num_verse_splitting_stage_directions'] = estimate_verse_line_splitting_stage_directions(play_soup)

    metadata_dict['degree_of_verse_prose_interaction'] = round((metadata_dict['num_verse_splitting_stage_directions'] /
                                                             number_verse_lines) * 100, 3)

    return metadata_dict

def percentage_of_scenes_discont_change(play_soup, play_data, metadata_dict):
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


def add_play_info(metadata, soup, custom_flag=False):
    """
    Update play metadata from the metadata_df. We can provide our own metadata or use the TEI metadataa
    """
    play_data = {}
    if custom_flag:
        play_data['title'] = metadata[0][0]
        play_data['author'] = metadata[0][1] + ', ' + metadata[0][2]
        play_data['creation_date'] = metadata[0][3]
        play_data['free_iambs'] = metadata[0][4]
    else:
        play_data['title'] = soup.find_all('title', {'type':'main'})[0].get_text()
        play_data['author'] = soup.find_all('author')[0].get_text()
        try:
            play_data['creation_date'] = int(soup.find_all('date',
                                         {'type':'written'})[0]['when'])
        except KeyError:
            play_data['premier_date'] = int(soup.find_all('date',
                                         {'type':'premiere'})[0]['when'])

    return play_data


def additional_metadata(play_soup, play_data):
    """
    Process all play features in stages
    """
    metadata_dict = {}
    for process in [process_speakers_features, process_features_verse,
                   process_stage_directions_features, percentage_of_scenes_discont_change]:
        metadata_dict = process(play_soup, play_data, metadata_dict)

    return metadata_dict


    return speech_distribution, speech_types, av_perc_non_speakers


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
