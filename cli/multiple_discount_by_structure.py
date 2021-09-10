""""
v1.0.0

A wrapper around discount_by_structure.py to automate discounting from multiple
AssetDamageDetail files. All files must be in the same subdirectory.

python multiple_discount_by_structure.py --help

Changelog:

v1.0.0 - 10SEP2021

"""

import os
import utils
import discount_by_structure
import argparse

def get_parser():
    parser = argparse.ArgumentParser(description="Discount from AssetDamageDetailFile")
    parser.add_argument(
        '-i',
        '--input_folder', 
        help='Path to input folder containing all csv files')
    parser.add_argument(
        '-o', 
        '--output_folder', 
        help='Path to output folder')
    parser.add_argument(
        '-r', 
        '--discount_rate',
        type=float,
        help='Discount rate in percentage')
    parser.add_argument(
        '-b', 
        '--base_timestamp', 
        help='Base timestamp using format YYYYMMDD')
    return parser


def main(input_folder: str, output_folder: str, discount_rate: float, base_timestamp: str):

    # Get list of files
    files = utils.full_paths_by_type(input_folder, "csv", "AssetDamageDetail")

    for file in files:
        no_meta_file_name = utils.remove_meta(file)
        output_file = "DiscountedDamages_" + no_meta_file_name.replace(utils.derive_prefix(no_meta_file_name)+"_", "") + ".csv"
        discount_by_structure.main(file, os.path.join(output_folder, output_file), discount_rate, base_timestamp)


if __name__ == "__main__":
    args, random = get_parser().parse_known_args()
    main(args.input_folder, args.output_folder, args.discount_rate, args.base_timestamp)