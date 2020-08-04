import os
import sys
import argparse
from text_processing import text_processing_functions as tpf

def main(raw_args):
  parser = argparse.ArgumentParser(description='Input arguments for manually tagged txt files.')
  parser.add_argument('-i', '--input_path', type=str, required=True, help='The path which contains the txt files')
  parser.add_argument('-o', '--ouput_path', type=str, required=True, help='The path where the json files should be saved')
  parser.add_argument('-m', '--metadata_path', type=str, required=True, help="The path to the metadata tab-delimited tsv file.")
  args = vars(parser.parse_args(raw_args))

  tpf.process_all_plays(args['input_path'], args['ouput_path'], args['metadata_path'], tpf.regex_pattern)

if __name__ == '__main__':
    main(sys.argv[1:])
