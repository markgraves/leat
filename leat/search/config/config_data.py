"""Configuration data for search"""

from collections import defaultdict
import csv
import json
from pathlib import Path
import re
from typing import NamedTuple, Optional, Union

from .predefined_configurations import PredefinedConfigurations

try:
    import openpyxl

    EXCEL_READ_AVAILABLE = True
except ModuleNotFoundError:
    print(
        "WARNING:",
        "Excel config file reading not available. Need to: pip install openpyxl",
    )
    EXCEL_READ_AVAILABLE = False


class ConfigData:
    "Configuration data for search"

    def __init__(
        self,
        config_file: Optional[Union[str, Path]] = None,
        save_json_if_outdated: bool = True,
        load_json_if_current: bool = True,
        json_config_file: Optional[Union[str, Path]] = None,
        predefined_configuration: Optional[str] = None,
    ):
        self.data: dict = {}
        self.config_file = None
        self.short_name: str = 'Empty'
        if predefined_configuration:
            config_file = PredefinedConfigurations.data.get(predefined_configuration)
            if config_file:
                if config_file.exists():
                    self.load_config_file(config_file, json_config_file=None)
                    self.short_name = '#' + predefined_configuration
                else:
                    print(
                        "ERROR:",
                        "Internal error. Known configuration named",
                        predefined_configuration,
                        "not found at",
                        config_file,
                    )
            else:
                print("ERROR:", "Unknown configuration name:", predefined_configuration)
        elif config_file is None and json_config_file is None:
            pass
        else:
            self.load_config_file(
                config_file,
                save_json_if_outdated,
                load_json_if_current,
                json_config_file,
            )

    def load_config_file(
        self,
        config_file: Optional[Union[str, Path]] = None,
        save_json_if_outdated: bool = True,
        load_json_if_current: bool = True,
        json_config_file: Optional[Union[str, Path]] = None,
    ):
        if not config_file:
            if json_config_file:
                return self.load_config_file_json(json_config_file)
            print("ERROR:", "No config file specified to load.")
            return
        config_file = Path(config_file)
        config_file_type = self.get_config_file_type(config_file)
        if config_file_type == "csv":
            return self.load_config_file_csv(config_file)
        if config_file_type == "json":
            return self.load_config_file_json(config_file)
        if config_file_type != "xlsx":
            print(
                "ERROR:",
                "Unknown config file type",
                config_file_type,
                "for load file:",
                config_file,
            )
            return
        if json_config_file:
            json_config_file = Path(json_config_file)
        else:
            json_config_file = json_config_file_for_excel(config_file)
        if (
            json_config_file
            and json_config_file.exists()
            and config_file.exists()
            and json_config_file.stat().st_mtime > config_file.stat().st_mtime
        ):
            if load_json_if_current:
                return self.load_config_file_json(json_config_file)
            self.load_config_file_xlsx(config_file)
            return
        if self.load_config_file_xlsx(config_file) and save_json_if_outdated:
            self.write_config_data_json(json_config_file)

    @staticmethod
    def get_config_file_type(filename):
        fileext = Path(filename).suffix.strip(".")
        return fileext

    def load_config_file_csv(self, filename):
        "Read csv configuration file, returning config dict"
        print("INFO:", "Loading csv config file:", filename)
        with open(filename, "r", encoding="utf-8-sig") as ifp:
            reader = csv.DictReader(ifp)
            result = defaultdict(list)
            for row in reader:
                for k, v in row.items():
                    if v:
                        result[k].append(v.strip())
        self.data = dict(result)
        self.config_file = filename
        self.short_name = filename.stem
        return True

    def load_config_file_xlsx(self, filename):
        "Load Excel xlsx configuration file"
        print("INFO:", "Loading xlsx config file:", filename)
        wb = openpyxl.load_workbook(filename, data_only=True)
        result = {}
        for sn in wb.sheetnames:
            sheet_type = self.get_sheetname_type(sn)
            if sheet_type == "SEARCH":
                result[sn.strip()] = read_config_sheet_search(wb[sn])
            elif sheet_type == "PATTERN":
                result[sn.strip()] = read_config_sheet_pattern(wb[sn])
        self.data = dict(result)
        self.config_file = filename
        self.short_name = filename.stem
        return True

    @staticmethod
    def get_sheetname_type(sheet_name):
        "Return the type of sheet name, e.g., SEARCH, PATTERN, or UNKNOWN"
        lower = sheet_name.casefold()
        if "search" in lower:
            return "SEARCH"
        if "pattern" in lower:
            return "PATTERN"
        return "UNKNOWN"

    def write_config_data_json(self, filename):
        "Write config information as json"
        newconfig = {k: config_json_format_simplify(v) for k, v in self.data.items()}
        print("INFO:", "Saving json config file", filename)
        with open(filename, "w") as ofp:
            json.dump(newconfig, ofp, indent=4)

    def load_config_file_json(self, filename):
        "Read config information from json file"
        print("INFO:", "Loading json config file:", filename)
        with open(filename, "r") as ifp:
            data = json.load(ifp)
        # Hooks to correct serialized type changes
        config = {k: config_json_format_restore(v) for k, v in data.items()}
        self.data = config
        self.config_file = filename
        self.short_name = filename.stem
        return True

    def __str__(self):
        return f'<{__class__.__name__} {self.short_name}>'


class PatternConcept(NamedTuple):
    "Concept for pattern that tracks flag for matching"
    concept: str
    flags: int = 0  # re.NOFLAG


CLEAN_COLUMN_NAMES_MAPPING = {
    "concept": "CONCEPT",
    "entity": "CONCEPT",
    "pattern": "PATTERN",
    "regex": "PATTERN",
    "regular expression": "PATTERN",
    "case insensitive": "CASE INSENSITIVE",
    "case insens": "CASE INSENSITIVE",
    "ignore case": "CASE INSENSITIVE",
}


def clean_column_name_index(colnames):
    "Clean and index column names for config sheets"
    result = {}
    for i, cn in enumerate(colnames):
        cn_lower = cn.casefold().strip()
        for k, v in CLEAN_COLUMN_NAMES_MAPPING.items():
            if k in cn_lower:
                if v not in result:
                    # Take first match, ignoring extra columns in sheet
                    result[v] = i
                break
    return result


def read_config_sheet_search(sheet):
    "Read config search sheet, returning dict of values"
    sheetvalues = {"_sheet_type": "SEARCH"}
    for col in sheet.iter_cols():
        if col[0].value:
            sheetvalues[col[0].value] = [x.value.strip() for x in col[1:] if x.value]
    return sheetvalues


def read_config_sheet_pattern(sheet):
    "Read config pattern sheet, returning dict of values"
    sheetvalues = defaultdict(list)
    sheetvalues["_sheet_type"] = "PATTERN"
    column_name_map = clean_column_name_index(x.value for x in sheet[1])
    for row in sheet.iter_rows(min_row=2):
        if "CONCEPT" not in column_name_map or "PATTERN" not in column_name_map:
            print(
                "Error: Pattern sheet",
                sn,
                "needs concept and pattern columns in",
                str(filename),
            )
        if "CASE INSENSITIVE" in column_name_map:
            val = row[column_name_map["CASE INSENSITIVE"]].value
            if val:
                flags = (
                    re.IGNORECASE if val.casefold().startswith("y") else 0
                )  # re.NOFLAG # noflag in python 3.11
            else:
                # Default is case sensitive for patterns
                flags = 0  # re.NOFLAG # noflag in python 3.11
        else:
            flags = 0  # re.NOFLAG # noflag in python 3.11
        sheetvalues[
            PatternConcept(concept=row[column_name_map["CONCEPT"]].value, flags=flags)
        ].append(row[column_name_map["PATTERN"]].value)
    return dict(sheetvalues)


def json_config_file_for_excel(excel_filename):
    "Replaces xlsx filename extension with json"
    return Path(excel_filename).with_suffix(".json")


def config_json_format_simplify(sheet_config):
    "Hooks to change serialized types"
    if sheet_config.get("_sheet_type", "") == "PATTERN":
        result = defaultdict(dict)
        for pattern_concept, pats in sheet_config.items():
            if type(pattern_concept) == str and pattern_concept.startswith("_"):
                result[pattern_concept] = pats
                continue
            assert type(pattern_concept) == PatternConcept
            result[pattern_concept.concept][pattern_concept.flags] = pats
        return result
    else:
        return sheet_config


def config_json_format_restore(sheet_config):
    "Hooks to revert serialized type changes"
    if sheet_config.get("_sheet_type", "") == "PATTERN":
        result = defaultdict(list)
        for concept, flag_sub_dict in sheet_config.items():
            if concept.startswith("_"):
                result[concept] = flag_sub_dict
                continue
            for flags, pats in flag_sub_dict.items():
                result[PatternConcept(concept, int(flags))] = pats
        return dict(result)
    else:
        return sheet_config
