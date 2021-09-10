"""
Summarize runs v1.3

Summarize basic statistics from completed G2CRM runs and output to a csv file. 
The program travels down the subdirectories of a master input folder and search
for an output *.prn file. Each path where a *.prn file is located is assumed to
be a finished run output folder. Requires custom package "utils" v1.8.

The tool can be used via a CLI. Run --help for possible arguments:
  python summarize_runs.py --help
  python summarize_runs.py --input_folder “X:\ Main folder containing all sub branch output folders” –output_file “C:\path\output_file.csv”

Changelog:

v 1.0 - 22FEB2021

v 1.1 - 05MAR2021
Added expected_elevation and expected_removal to output 

v 1.2 - 15MAR2021
Add number of affected structures

v 1.3 - 07JUN2021
Adapt to to G2CRM version 0.4.564.3

"""
import argparse
import utils
import pandas as pd
import re
import os
import traceback
import sqlite3
from typing import List, Union

def expected_elevations(path:str, iters:int):
    try:
        asset_raising_path = utils.full_paths_by_type(path, 'csv', 'AssetRaising')
        asset_raising_path = asset_raising_path[0]
        data = pd.read_csv(asset_raising_path)
        return len(data)/iters
    except:
        return "Error reading from AssetRaising csv file"


def damaged_structures(path:str):
    """
    Count the number of flooded structures. Defined as total PV damages > 5% of structures+contents value.
    Also removes any structure with "-" in its AssetExternalReference
    Do not read if file is bigger than threshold
    """

    # read from db only if MapOutputs file is smaller than this threshold
    # 1mb = 1,000,000
    mapoutputs_size_threshold = 50*1000000 

    try:
        mapoutputs_path = utils.full_paths_by_type(path, 'sqlite', 'MapOutputs')
        mapoutputs_path = mapoutputs_path[0]

        sql = """
            /* Count number of assets with greater than damage threshold as % of value */
            SELECT COUNT(AssetID) FROM
            (
                SELECT 
                    AssetID, 
                    AssetExternalReference, 
                    (MeanValue/Value) AS DamageRatio 
                FROM
                (
                    SELECT 
                        assetID, 
                        (StructureValue + ContentsValue) AS Value, 
                        MeanValue, 
                        AssetExternalReference 
                    FROM AssetsAllStatistics
                    WHERE statisticsTypeName = "PVDamage"
                )
                WHERE
                    DamageRatio > .05 AND /* Damage threshold */
                    AssetExternalReference NOT LIKE "%-%" /* No dashes in Ref ie only structures no debris and auto*/
                )
        """

        file_size = os.path.getsize(mapoutputs_path)

        if file_size > mapoutputs_size_threshold:
            return "MapOutputs sqlite file is too large"

        conn = sqlite3.connect(mapoutputs_path)
        data = pd.read_sql(sql, conn).iloc[0,0]
        conn.close()
        return data
    except:
        traceback.print_exc()
        return "Error reading from MapOutputs sqlite file"


def expected_removals(path:str, iters:int):
    try:
        asset_removal_path = utils.full_paths_by_type(path, 'csv', 'RemovedAssets')
        asset_removal_path = asset_removal_path[0]
        data = pd.read_csv(asset_removal_path)
        return len(data)/iters
    except:
        return "Error reading from RemovedAssets csv file"


def parse_prn(tokens, data:str, mode = 'mean'):
    """
    data = total_life_loss, upland_pvdamage, simulation_name, g2_start_time, iters
    tokens = tokenized prn file by newline \n
    mode = mean, std only for 'total_life_loss' and 'upland_pvdamage'
    """

    empty_index = [i for i, elem in enumerate(tokens) if '' == elem]
    if len(empty_index) < 7: return 'Unfinished Run' # incomplete runs
    if data == 'total_life_loss':
        index = [i for i, elem in enumerate(tokens) if 'Total Life Loss' in elem][0]
        hor_index = 2 if mode == 'mean' else 5
        return float((re.split(r'\s{2,}', tokens[index])[hor_index]).replace(',', ''))
    elif data == 'upland_pvdamage':
        index = [i for i, elem in enumerate(tokens) if 'PV Damage' in elem][0]
        hor_index = 2 if mode == 'mean' else 5
        return float((re.split(r'\s{2,}', tokens[index])[hor_index]).replace(',', ''))
    elif data == 'simulation_name':
        index = [i for i, elem in enumerate(tokens) if 'Simulation Name: ' in elem][0]
        return tokens[index].split(': ')[1]
    elif data == 'g2_start_time':
        index = [i for i, elem in enumerate(tokens) if 'G2CRM Run on ' in elem][0]
        return tokens[index].replace('G2CRM Run on ', '').split(' Model Version:')[0]
    elif data == 'iters':
        index = [i for i, elem in enumerate(tokens) if 'Number of Iterations: ' in elem][0]
        return int(tokens[index].split('Iterations: ')[1])
    elif data == 'seed':
        index = [i for i, elem in enumerate(tokens) if 'Seed: ' in elem][0]
        return int(tokens[index].split(': ')[1])
    elif data == 'slc':
        index = [i for i, elem in enumerate(tokens) if 'Sea Level Change: ' in elem][0]
        return tokens[index].split(': ')[1]
    elif data == 'run_condition':
        index = [i for i, elem in enumerate(tokens) if 'RunConditions: ' in elem][0]
        return tokens[index].split(': ')[1]
    elif data == 'interest_rate':
        index = [i for i, elem in enumerate(tokens) if 'Interest Rate: ' in elem][0]
        return float((tokens[index].split(': ')[1]).replace(',', ''))
    elif data == 'duration':
        index = [i for i, elem in enumerate(tokens) if 'Duration: ' in elem][0]
        return float((tokens[index].split(': ')[1]).replace(',', ''))
    elif data == 'basis_time':
        index = [i for i, elem in enumerate(tokens) if 'Basis Time: ' in elem][0]
        return tokens[index].split(': ')[1]
    elif data == 'start_time':
        index = [i for i, elem in enumerate(tokens) if 'Start Time: ' in elem][0]
        return tokens[index].split(': ')[1]
    elif data == 'slc_basis_year':
        index = [i for i, elem in enumerate(tokens) if 'GlobalSLCBasisYear: ' in elem][0]
        return int(tokens[index].split(': ')[1])
    elif data == 'cum_damage_removal':
        index = [i for i, elem in enumerate(tokens) if 'Do Cumulative Damage Removal: ' in elem][0]
        return True if tokens[index].split(': ')[1] == 'True' else False
    elif data == 'depreciation':
        index = [i for i, elem in enumerate(tokens) if 'Do Depreciation: ' in elem][0]
        return True if tokens[index].split(': ')[1] == 'True' else False
    elif data == 'asset_raising':
        index = [i for i, elem in enumerate(tokens) if 'Do Asset Raising: ' in elem][0]
        return True if tokens[index].split(': ')[1] == 'True' else False
    elif data == 'calculate_life_loss':
        index = [i for i, elem in enumerate(tokens) if 'Calculate Life Loss: ' in elem][0]
        return True if tokens[index].split(': ')[1] == 'True' else False
    elif data == 'g2_version':
        index = [i for i, elem in enumerate(tokens) if 'Model Version: ' in elem][0]
        return tokens[index].split(': ')[1]
    elif data == 'run_time':
        index = [i for i, elem in enumerate(tokens) if 'Computation Time: ' in elem][0]
        return float(((tokens[index].split(': ')[1]).split(' sec')[0]).replace(',', ''))
    elif data == 'plan_alt':
        index = [i for i, elem in enumerate(tokens) if 'Plan Alternative: ' in elem][0]
        return tokens[index].split(': ')[1]
    elif data == 'g2_assets':
        asset_index = [i for i, elem in enumerate(tokens) if 'Assets:' == elem][0]
        return int(tokens[asset_index+1].split(': ')[1])
    elif data == 'number_of_storms':
        index = [i for i, elem in enumerate(tokens) if 'Number of Distinct Storms:' in elem][0]
        return int(tokens[index].split(': ')[1])


def get_parser():
    parser = argparse.ArgumentParser(description="Generate summary statistics for all runs")
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
        help='Unique str identifier e.g. FWOP, S1, Intermediate, etc.')
    return parser


def main(input_folder: str, output_file: str, contains:Union[List[str],str]):

    file_list = utils.full_paths_by_type(input_folder, 'prn', 'prn' if not contains else contains, print_log=True)
    existed_files_without_path = list(map(utils.remove_path, file_list))
    paths = list(map(utils.folder_path, file_list))
    no_files = len(paths)

    data_types = [
        'total_life_loss', 'upland_pvdamage', 'simulation_name', 'g2_start_time', 'iters' , 'seed', 'slc', 
        'run_condition', 'interest_rate', 'duration', 'basis_time', 'start_time', 'slc_basis_year', 'cum_damage_removal',
        'depreciation', 'asset_raising', 'calculate_life_loss', 'g2_version', 'run_time', 'plan_alt', 'g2_assets','number_of_storms']

    col_index = ['total_life_loss_std', 'upland_pvdamage_std'] + data_types + ["assets_elevated", "assets_removed", "damaged_structures"]

    data = pd.DataFrame([], columns=col_index)

    print("File list generated. Parsing data...")
    logger = utils.LogManager(os.path.join(utils.folder_path(output_file), "summarize_runs.log"))

    for i, file in enumerate(file_list):
        print(f'Reading from {file}')
        print(f'{i+1}/{no_files}', end='\r')
        try:
            run_path = utils.folder_path(file)
            with open(file) as f:
                read_data = f.read()
                tokens = read_data.split('\n')
                iters = parse_prn(tokens, 'iters')
                extracted_data = [parse_prn(tokens, 'total_life_loss', 'std'), parse_prn(tokens, 'upland_pvdamage', 'std')] + (
                    [parse_prn(tokens, data_type) for data_type in  data_types]) + [expected_elevations(run_path, iters), expected_removals(run_path, iters), damaged_structures(run_path)]
                
        except Exception as e:
            logger.log_info(f'Error encountered while parsing {file}')
            # logger.log_info(f'Dumping tokenized file')
            # logger.log_info(tokens)
            logger.log_error(e)
            extracted_data  = ['Script Error'] * (len(data_types)+5)

        extracted_series = pd.Series(extracted_data, index=col_index)
        data = data.append([extracted_series], ignore_index=True)

    try:
        data.index = existed_files_without_path
        data.index.name = 'file_name'

        data = data.reset_index()
        data['file_path'] = file_list
        data['folder_path'] = paths

        data['MA'] = data['file_path'].apply(lambda x: utils.derive_ma_code(x))

        data['run_time_hrs'] = data['run_time'].apply(lambda x: x / (60*60) if isinstance(x, float) else x)

        data = data[['file_name', 'file_path', 'folder_path', 'MA', 'simulation_name', 'g2_version', 'g2_start_time', 'run_time', 'run_time_hrs',
            'slc', 'plan_alt', 'iters', 'g2_assets', 'number_of_storms',
            'total_life_loss', 'total_life_loss_std', 'upland_pvdamage', 'upland_pvdamage_std', "assets_elevated", "assets_removed", "damaged_structures",      
            'run_condition', 'seed', 'interest_rate', 'duration', 'basis_time', 'start_time', 'slc_basis_year', 
            'cum_damage_removal', 'depreciation', 'asset_raising', 'calculate_life_loss']]

        data.to_csv(output_file, index=False)
    
    except Exception as e:
        logger.log_info(f'Error encountered during post processing')
        logger.log_info(f'Dumping working dataframe')
        logger.log_info(data)
        logger.log_error(e)
        

if __name__ == "__main__":
    args, random = get_parser().parse_known_args()
    main(args.input_folder[0], args.output_file[0], args.contains)
