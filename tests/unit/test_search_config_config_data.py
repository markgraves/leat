from pathlib import Path
import re

import pytest

from leat.search.config import ConfigData, PatternConcept

TEST_DATA_DIRECTORY = Path(__file__).parent.parent / "data" / "config"

BASIC_SEARCH_1 = {
    "Performance Metrics": [
        "precision",
        "recall",
        "sensitivity",
        "specificity",
        "F1",
        "accuracy",
    ],
    "Data Ethics": ["bias", "fairness", "transparency", "accountability"],
    "Ethical Principles": [
        "beneficience",
        "nonmaleficence",
        "do good",
        "do no harm",
        "non-maleficence",
        "justice",
        "respect for autonomy",
        "patient autonomy",
        "autonomy",
    ],
}

BASIC_SEARCH_2 = {
    "Basic Search": {
        "_sheet_type": "SEARCH",
        "Performance Metrics": [
            "precision",
            "recall",
            "sensitivity",
            "specificity",
            "F1",
            "accuracy",
        ],
        "Data Ethics": ["bias", "fairness", "transparency", "accountability"],
        "Ethical Principles": [
            "beneficience",
            "nonmaleficence",
            "do good",
            "do no harm",
            "non-maleficence",
            "justice",
            "respect for autonomy",
            "patient autonomy",
            "autonomy",
        ],
    },
    "Patterns": {
        "_sheet_type": "PATTERN",
        PatternConcept(concept="Data Ethics", flags=re.IGNORECASE): ["\\bequit"],
        PatternConcept(concept="Test", flags=re.IGNORECASE): ["\\b\\d\\d\\d\\d\\b"],
        PatternConcept(concept="Test", flags=0): ["WHO", "MAR", "Sen"],
    },
}


def test_read_csv():
    test_file = TEST_DATA_DIRECTORY / "Basic-Search-1.csv"
    assert test_file.exists()
    cd = ConfigData(test_file)
    assert cd.data == BASIC_SEARCH_1


def test_read_excel():
    test_file = TEST_DATA_DIRECTORY / "Basic-Search-2.xlsx"
    assert test_file.exists()
    cd = ConfigData(
        test_file,
        save_json_if_outdated=False,
        load_json_if_current=False,
        json_config_file=None,
    )
    assert cd.data == BASIC_SEARCH_2

def test_read_write_json(tmp_path):
    test_file = TEST_DATA_DIRECTORY / "Basic-Search-2.xlsx"
    temp_json = tmp_path / "temp.json"
    assert test_file.exists()
    cd = ConfigData(
        test_file,
        save_json_if_outdated=False,
        load_json_if_current=False,
        json_config_file=None,
    )
    cd.write_config_data_json(temp_json)
    newcd = ConfigData(json_config_file=temp_json)
    assert cd.data == newcd.data
    # test init load of json
    cd3 = ConfigData(temp_json)
    assert temp_json.exists()
    assert cd3.data == BASIC_SEARCH_2
   

def test_init_args(tmp_path):
    test_file = TEST_DATA_DIRECTORY / "Basic-Search-2.xlsx"
    temp_json = tmp_path / "temp.json"
    assert test_file.exists()
    cd = ConfigData(
        test_file,
        save_json_if_outdated=True,
        load_json_if_current=False,
        json_config_file=temp_json,
    )
    assert cd.data == BASIC_SEARCH_2
    assert cd.config_file.suffix == ".xlsx"
    assert temp_json.exists()
    newcd = ConfigData(
        test_file,
        save_json_if_outdated=True,
        load_json_if_current=True,
        json_config_file=temp_json,
    )
    assert newcd.data == BASIC_SEARCH_2
    assert newcd.config_file.suffix == ".json"
    cd3 = ConfigData(
        test_file,
        save_json_if_outdated=True,
        load_json_if_current=False,
        json_config_file=temp_json,
    )
    assert cd3.data == BASIC_SEARCH_2
    assert cd3.config_file.suffix == ".xlsx"
