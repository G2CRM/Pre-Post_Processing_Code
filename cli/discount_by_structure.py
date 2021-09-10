"""
v1.0

Recalculate present value of damages using a specified discount rate.

Usage:
  python discount_by_structure.py --input_file "C:/Path to AssetDamageDetail file"
    --output_file "C:/Path to output csv file"  --discount_rate 2.5 
    --base_timestamp 20300101

Changelog 

v1.0 19OCT2020

"""
import argparse
import pandas as pd
import utils
import os
import math

# setting flag_mean_pivot as True results in only mean output 
# for each asset rather than damages per Iteration
flag_mean_pivot = True
# save calculation step as WorkingCalculations_ file
flag_save_working_calcs = True


def get_parser():
    parser = argparse.ArgumentParser(description="Discount from AssetDamageDetailFile")
    parser.add_argument(
        '-i',
        '--input_file',
        help='Path to input folder containing AssetDamageDetailFile')
    parser.add_argument(
        '-o', 
        '--output_file', 
        help='Path to output file')
    parser.add_argument(
        '-r', 
        '--discount_rate',
        type=float,
        help='Discount rate in percentage eg 2.5%%')
    parser.add_argument(
        '-b', 
        '--base_timestamp',
        help='Base timestamp in format YYYYMMDD')
    return parser


def calculate_discount_factor(timestamp, base_timestamp, discount_rate):
    if type(timestamp) is str:
        timestamp = pd.Timestamp(timestamp)
    return (1/(1+discount_rate)**((timestamp - base_timestamp).days/365))


def main(input_file: str, output_file: str, discount_rate: float, base_timestamp: str) -> None:
    # print(f"Reading from {input_file}")

    discount_rate = discount_rate / 100
    discount_cols = ['ValueLossStructure', 'ValueLossContents', 'TotalLoss']
    base_timestamp = pd.Timestamp(base_timestamp)
    output_folder = utils.folder_path(output_file)

    data = pd.read_csv(input_file, parse_dates=['Time'], low_memory=False)

    data["DiscountFactor_Script"] = data["Time"].apply(lambda x: calculate_discount_factor(x, base_timestamp, discount_rate))

    # Calculate discount factor and new struct/contents/total damages
    for col in discount_cols:
        data[col+"PV_Script"] = data["DiscountFactor_Script"]*data[col]

    # Output intermediate calculations
    if flag_save_working_calcs:
        data.to_csv(os.path.join(output_folder,"WorkingCalculations_" + utils.remove_meta(input_file) + ".csv"), index=False)

    # aggregate data for each asset
    pv_data = data.pivot_table(values=['ValueLossStructurePV_Script', 'ValueLossContentsPV_Script',
       'TotalLossPV_Script'], index=['AssetExternalReference', 'Iteration'], aggfunc="sum")

    # calculate mean damages for each asset
    if flag_mean_pivot:
        pv_data = pv_data.pivot_table(values=['ValueLossStructurePV_Script', 'ValueLossContentsPV_Script',
            'TotalLossPV_Script'], index=['AssetExternalReference'], aggfunc="sum")
        no_iters = max(data['Iteration'].values)
        for col in discount_cols:
            pv_data[col+"PV_Script"] = pv_data[col+"PV_Script"]/no_iters

    pv_data = pv_data[['ValueLossStructurePV_Script', 'ValueLossContentsPV_Script',
            'TotalLossPV_Script']]

    pv_data.columns = ['ValueLossStructurePV', 'ValueLossContentsPV',
            'TotalLossPV']

    pv_data.to_csv(output_file)
    print(f"Saved data to {output_file}")


if __name__ == "__main__":
    args, random = get_parser().parse_known_args()
    main(args.input_file, args.output_file, args.discount_rate, args.base_timestamp)