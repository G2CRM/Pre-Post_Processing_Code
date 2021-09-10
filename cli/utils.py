"""
v1.8

General utils to support CSRM simulation.

Change log:

13OCT2020 v1.5
Added WorkingCalculations_ and DiscountedDamages_ and as available prefixes

15OCT2020 v1.6
Added FWP as a possible alternative to derive_alt

23FEB2021 v1.7
Fixed filter to work with str 'filename_contains' in full_paths_by_type

04MAR2021 v1.8
Add arg to hide logging in full_paths_by_type
"""

import glob
import os
import shutil
from typing import List, Union
import re
import datetime
import logging
import sys
import datetime


class LogManager:
    """Cookie cutter logging manager - writes to console and file"""
    logger = logging.getLogger(__name__)

    def __init__(self, filePath):
        self.setupLogger(filePath)
        self.logger.setLevel(logging.DEBUG)

    def setupLogger(self, filePath):
        """Set up console and file handlers"""
        # console handler
        cHandler = logging.StreamHandler(sys.stdout)
        cHandler.setLevel(logging.INFO)
        # file handler
        fHandler = logging.FileHandler(filePath, mode='a') 
        fHandler.setLevel(logging.INFO)

        cFormatter = logging.Formatter(
            '%(message)s')
        fFormatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s', '%m/%d/%Y %H:%M:%S')
        
        cHandler.setFormatter(cFormatter)
        fHandler.setFormatter(fFormatter)
        self.logger.addHandler(cHandler)
        self.logger.addHandler(fHandler)

    def log_error(self, exception):
        self.logger.error(exception, exc_info=True)
    
    def log_warning(self, msg):
        self.logger.warning(msg)
    
    def log_info(self, msg):
        self.logger.info(msg)


def full_paths_by_type(directory: str, extension: str, filename_contains: Union[List[str],str], print_log:bool=False):
    """Generate a list of filepaths based on extension and substr contained in filename"""
    extension = "*." + extension
    if print_log:
        print(f"Retrieving {extension} file list containing '{filename_contains}' from {directory}")
    all_files = [file for path, subdir, files in os.walk(directory) for file in glob.glob(os.path.join(path, extension))]
    
    filename_contains = [filename_contains] if isinstance(filename_contains, str) else filename_contains

    for filter_phrase in filename_contains:
        # returns all paths 
        all_files = [x for x in all_files if filter_phrase in remove_path(x)]
    return all_files


def timestamp_inplace(file_name: str):
    """Check if timestamp is already in name"""
    return bool(re.search(r"\d{8}-\d{6}", file_name))


def remove_meta(path: str):
    return remove_timestamp(remove_extension(remove_path(path)))


def remove_path(path: str):
    """Strip out pathing info"""
    return path.split("\\")[-1]


def remove_extension(file_name_with_extension: str):
    """Strip out file extension"""
    return file_name_with_extension.split(".")[:-1][0]


def remove_timestamp(file_name_without_extension: str):
    """Strip out timestamp"""
    return re.sub(r"_\d{8}-\d{6}", "", file_name_without_extension)


def folder_path(path: str):
    return "\\".join(path.split("\\")[:-1])


def derive_slc(path: str):
    scenarios = ["High_", "Low_", "Intermediate_"]
    for scenario in scenarios:
        if re.search(scenario, remove_path(path)):
            break
    else:
        if (derive_extension(path) is not "csv") or (derive_extension(path) is not "sqlite"):
            # Skipping over non-data files
            return "NoData"
        raise(Exception(f"Unable to derive SLC curve for {path}"))
    return scenario.replace("_", "")


def derive_alt(path: str) -> str:
    alts = ["FWOP", "S0", "S1", "S2", "S3", "S4", "S5", "S6", "S7", "S8", "S9", "NS", "FWP"]
    
    working_str = remove_path(path)
    working_str = re.sub(derive_prefix(path) + '_', '', working_str)
    working_str = re.sub(derive_slc(path) + '_', '', working_str)
    
    for alt in alts:
        if re.search(alt.lower(), working_str.lower()):
            break
    else:
        if (derive_extension(path) is not "csv") or (derive_extension(path) is not "sqlite"):
            # Skipping over non-data files
            return "NoData"
        raise(Exception(f"Unable to derive alternative name for {path}"))
    return alt.replace("_", "")


def derive_prefix(path: str) -> str:
    prefixes = [
        ".echo"
        "CustomSQL_",
        "AssetDamageDetail_",
        "AssetDamageHistory_",
        "AssetDepreciationDetail_",
        "AssetLifeLoss_",
        "AssetRaising_",
        "AssetStormDetail_",
        "CsvOutputs_",
        "DeploymentEvent_",
        "Event_",
        "FloodBarrierPSEDetail_",
        "Iteration_",
        "IterationSeason_",
        "IterationYear_", 
        "MapOutputs_",
        "MessageFile_",
        "ModeledAreaStorm_",
        "ProtectiveSystemElementStorm_",
        "RemovedAssets_",
        "StormEvent_",
        "Tide_",
        "Timing_",
        "WaveCalculation_",
        "AssetMACorrespondence_",
        "Assets_",
        "AssetsAllStatistics_",
        "AssetsPVDamage_",
        "AssetsTimesRebuilt_",
        "BulkheadPSE_",
        "ClosurePSE_",
        "FloodBarrierPSE_",
        "FragilityFunction_",
        "FragilityFunctionValue_",
        "FunctionType_",
        "InterflowElement_",
        "LeveePSE_",
        "LeveePSEFailureRepair_",
        "LocalSeaLevelChange_",
        "Location_",
        "MA_",
        "MAStatistics_",
        "MAType_",
        "PSE_",
        "PSEStatistics_",
        "PSEType_",
        "PolderMA_",
        "PumpPSE_",
        "SpatialIndex_",
        "Statistics_",
        "Structures_",
        "TransitionPSE_",
        "TransitionPSEFailureRepair_",
        "UnprotectedMA_",
        "UplandMA_",
        "VolumeStageFunction_",
        "VolumeStageFunctionValue_",
        "WallPSE_",
        "WallPSEFailureRepair_",
        "WaterMA_",
        "WetlandMA_",
        "WorkingCalculations_",
        "DiscountedDamages_"]
    for prefix in prefixes:
        if re.search(prefix, remove_path(path)):
            break
    else:
        if (derive_extension(path) is not "csv") or (derive_extension(path) is not "sqlite"):
            # Skipping over non-data files
            return derive_extension(path)
        else:
            raise(Exception(f"Unable to derive file prefix for {path}"))
    return prefix.replace("_", "")


def derive_extension(path:str) -> str:
    return path.split(".")[-1]


def derive_ma_code(path: str):
    """
    Returns MA code based using file path
    Usage:
        path = "C:\Local etc\Models\Collier\Econ Appendix\data\YearIteration\IterationYear_Intermediate_MA01a__FWOP_INT.csv"
        prefix = "IterationYear"
        get_MA_num_from_file_name(path, prefix)
    """
    
    working_str = remove_path(path)
    working_str = re.sub(derive_prefix(path) + '_', '', working_str) # remove prefix
    working_str = re.sub(derive_slc(path) + '_', '', working_str) # remove slc
    
    # remove typos
    working_str = re.sub(r'_{2,}', '_', working_str)
    working_str = re.sub(r'-', '_', working_str)
    working_str = re.sub(r'\.', '_', working_str)
    
    try: 
        ma = [x for x in working_str.split("_") if "ma" in x.lower()][0]
    except Exception:
        ma = "NoData"
    # except Exception:
    #     raise Exception(f"Unable to derive MA for {path}")
    return ma


def filter_data_files():
    raise NotImplementedError



