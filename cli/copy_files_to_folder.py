"""
v1.3

Copies files located in subdirectories of a master input folder based
on name and file extension.

python copy_files_folder.py --help

Changelog:

23FEB2021 - v1.3
Added skip logging option

"""
import argparse
import utils
import re
import datetime
import shutil
import os


def get_parser():
    parser = argparse.ArgumentParser(description="Copy files from master/subfolders based on file type and partial name")
    parser.add_argument(
        '-i', 
        '--input_folder', 
        nargs='+', 
        help='Path to input folder containing all csv files')
    parser.add_argument(
        '-x', 
        '--extension', 
        nargs='+',
        help='File extension e.g. csv, sqlite')
    parser.add_argument(
        '-o', 
        '--output_folder', 
        nargs='+', 
        help='Path to output folder')
    parser.add_argument(
        '-c', 
        '--contains', 
        nargs='+', 
        help='Unique str identifier e.g. FWOP, S1, Intermediate, etc.')
    return parser


def main(input_folder: str, output_folder: str, extension: str, contains: str, print_log: bool = True):

    logger = utils.LogManager(os.path.join(output_folder, "copy_files_to_folder.log"))

    if print_log: print(f"Copying files to {output_folder}")
    file_list = utils.full_paths_by_type(input_folder, extension, contains)

    # get output folder files list
    existed_files_with_meta = utils.full_paths_by_type(output_folder, extension, ".")
    existed_files_without_path = list(map(utils.remove_path, existed_files_with_meta))
    existed_files = list(map(utils.remove_meta, existed_files_with_meta))

    skip_count = 0
    copy_count = 0
    for i, file in zip(range(len(file_list)), file_list):
        if utils.remove_meta(file) in existed_files: # check if file is already copied
            existed_index = existed_files.index(utils.remove_meta(file))
            if print_log:
                logger.log_info(f"{str(i+1).zfill(2)}/{len(file_list)} - File in folder - {file} as {existed_files_without_path[existed_index]}")
            skip_count += 1
        elif re.search("ombined", utils.remove_meta(file)) or re.search("ggregate", utils.remove_meta(file)):
            if print_log:
                logger.log_info(f"{str(i+1).zfill(2)}/{len(file_list)} - Skipping over aggregated file - {utils.remove_path(file)}")
            skip_count += 1
        else:
            # create new file path
            now = str(datetime.datetime.now())[:19]
            now = now.replace("-","")
            now = now.replace(":","")
            now = now.replace(" ","-")
            copy_path = output_folder + "\\" + utils.remove_extension(utils.remove_path(file))
            if not utils.timestamp_inplace(utils.remove_path(file)):
                copy_path += ("_" + now)
            copy_path += ("." + extension)

            if print_log:
                logger.log_info(f"{str(i+1).zfill(2)}/{len(file_list)} - Copying - {file} to {utils.remove_path(copy_path)}")

            shutil.copy2(file, copy_path)
            copy_count += 1

    if print_log:
        logger.log_info(f"Copied {copy_count} files - skipped {skip_count} files - total {len(file_list)} files")
        logger.log_info(f"All files were saved to {output_folder}")


if __name__ == "__main__":
    args, random = get_parser().parse_known_args()
    main(args.input_folder[0], args.output_folder[0], args.extension[0], args.contains)