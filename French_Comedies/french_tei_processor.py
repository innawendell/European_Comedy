import os
import sys
import argparse
from text_processing import french_tei_functions as ftf

def main(raw_args):
  parser = argparse.ArgumentParser(description='Input arguments for manually tagged txt files.')
  parser.add_argument('-i', '--input_path', type=str, required=True, help='The path which contains the txt files')
  parser.add_argument('-o', '--ouput_path', type=str, required=True, help='The path where the json files should be saved')
  parser.add_argument('-c', '--custom_flag', type=bool, required=False, help='Indicate whether you want to provide a custom metadata file.')
  parser.add_argument('-m', '--metadata_path', type=str, required=False, help='Path to the tab-delimited tsv file with metadata')
  args = vars(parser.parse_args(raw_args))

  frf.process_all_plays(args['input_path'], args['ouput_path'], args['metadata_path'])

if __name__ == '__main__':
    main(sys.argv[1:])
