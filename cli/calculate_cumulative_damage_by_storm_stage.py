"""
v 1.0

Calculate cumulative damage by storm stage based on G2CRM AssetDamageDetail file

  python calculate_cumulative_damage_by_storm_stage.py --help

"""

import argparse
import pandas as pd
import math
import numpy as np


def get_parser():
    parser = argparse.ArgumentParser(description="Aggregate data from different CSV files")
    parser.add_argument(
        '-i', 
        '--input_file', 
        nargs='+', 
        help='Path to input file')
    parser.add_argument(
        '-o', 
        '--output_file', 
        nargs='+',
        help='Path to output file')
    parser.add_argument(
        '-l',
        '--linspace', 
        type=int,
        help='Specifies the number of max storm surge values')
    parser.add_argument(
        '-int',
        '--integer', 
        action='store_true',
        help='Calculate whole max storm surge values only')
    return parser


def calculate_totallosspv(data: pd.DataFrame, iter: int, storm_stage: int):
    """Reduces dataset based on iteration and storm stage, returns aggregated damages"""
    working_data = data[data["Iteration"] == iter]
    working_data = working_data[working_data["MaxStormStage"] <= storm_stage]
    return working_data["TotalLossPV"].sum()


def main(input_file: str, output_file: str, linspace: int, integer: bool):

    if linspace and integer: raise Exception("-int and -l tags are mututally exclusive")

    print(f"Calculating damages using data from {input_file}")
    data = pd.read_csv(input_file)
    data = data[["Iteration", "MaxStormStage", "TotalLossPV"]]
    
    if integer:
        storm_stages = np.arange(round(data["MaxStormStage"].min())-1,math.ceil(data["MaxStormStage"].max())+1, 1)
    elif linspace:
        storm_stages = np.linspace(round(data["MaxStormStage"].min())-1,math.ceil(data["MaxStormStage"].max())+1, linspace)
    else:
        storm_stages = np.arange(round(data["MaxStormStage"].min())-1,math.ceil(data["MaxStormStage"].max())+1, .5)

    iters = range(1, data["Iteration"].max()+1)

    storm_stage_damages = []
    no_storm_stage_values = len(storm_stages)
    for j, storm_stage in zip(range(no_storm_stage_values), storm_stages):
        
        # logging to console
        print(
            f"{str(j+1).zfill(2)}/{no_storm_stage_values} - Calculating damages for MaxStormStage = {storm_stage}", 
            end="\n" if j+1==no_storm_stage_values else "\r")

        working_iters = []
        for i in iters:
            working_iters.append(calculate_totallosspv(data, i, storm_stage))
        storm_stage_damages.append(np.mean(working_iters))
        
 
    print(f"Saving outputs to {output_file}")
    pd.DataFrame(np.c_[storm_stages, storm_stage_damages], columns=["MaxStormStage", "CumulativeTotalLossPV"]).to_csv(output_file, index=False)

if __name__ == "__main__":
    args, random = get_parser().parse_known_args()
    main(args.input_file[0], args.output_file[0], args.linspace, args.integer)