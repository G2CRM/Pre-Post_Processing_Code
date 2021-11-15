"""
v1.1

Concatenate data vertically for files with the same format.

python aggregate_ma_from_csv.py --help

"""
import argparse
import pandas as pd
import utils

def get_parser():
    parser = argparse.ArgumentParser(description="Aggregate data from different CSV files")
    parser.add_argument(
        '-i', 
        '--input_folder', 
        nargs='+', 
        help='Path to input folder containing all csv files')
    parser.add_argument(
        '-o', 
        '--output_file', 
        nargs='+', 
        help='Path to output file')
    parser.add_argument(
        '-c', 
        '--contains', 
        nargs='+', 
        help='Unique str identifier e.g. FWOP')
    return parser


def main(input_folder: str, output_file: str, contains: str):

    # Get list of files
    files = utils.full_paths_by_type(input_folder, "csv", contains)
    
    flag_first_file = True
    # iterate through all files

    for i, file in zip(range(len(files)), files):
        print(f"{str(i+1).zfill(2)}/{len(files)} - Loading {utils.remove_path(file)}")
        working_data = pd.read_csv(file)

        # create empty df
        if flag_first_file:
            working_columns = list(working_data.columns)
            # print(working_columns)
            working_columns.append("ModelArea")
            working_columns.append("SLC")
            working_columns.append("Alternative")
            data = pd.DataFrame(columns=working_columns)
            flag_first_file = False

        # merging files
        working_data = pd.read_csv(file)
        working_data["ModelArea"] = utils.derive_ma_code(file)
        working_data["SLC"] = utils.derive_slc(file)
        working_data["Alternative"] = utils.derive_alt(file)

        data = data.append(working_data)

    # export to csv
    # print(data)
    data.to_csv(output_file, index=False)
    print(f"Saved aggregated data to {output_file}")


if __name__ == "__main__":
    args, random = get_parser().parse_known_args()
    main(args.input_folder[0], args.output_file[0], args.contains[0])