import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))

# Existing imports
import pytest
import pandas as pd
from datetime import datetime
from prediction_vs_reality_logger.logger import run, validate_forecast_path_consistency
from prediction_vs_reality_logger.sources import JSONFileForecastSource
import json
import time
from pathlib import Path

def mock_actuals_source(date):
    """Mock actuals source for testing."""
    return {
        'high': 23660,
        'low': 23410,
        'close': 23500
    }

def test_logger_missing_forecast(monkeypatch):
    """Test that the logger handles missing forecast files gracefully."""
    monkeypatch.setattr('os.getcwd', lambda: os.path.dirname(__file__))  # Mock current directory
    forecast_folder = 'tests/forecast'  # Use relative path consistently
    os.makedirs(os.path.join(os.getcwd(), forecast_folder), exist_ok=True)
    config_path = os.path.join(os.getcwd(), 'config.yaml')

    try:
        with open(config_path, 'w') as f:
            f.write("""
            forecast_folder: tests/forecast
            output_csv: nq_daily_eval.csv
            schedule_time: "16:30"
            slack_webhook_url: http://example.com/webhook
            thinkorswim:
              host: localhost
              port: 8080
              use_ssl: false
            """)

        print(f"Forecast folder: {forecast_folder}")
        print(f"Config path: {config_path}")

        monkeypatch.setattr('prediction_vs_reality_logger.config.load_config', lambda: {
            'forecast_folder': forecast_folder,  # Use the relative path
            'output_csv': 'nq_daily_eval.csv'  # Use relative path
        })

        run(date=datetime(2025, 7, 31), actuals_source=mock_actuals_source)
    except SystemExit as e:
        assert e.code == 1  # Ensure the script exits with code 1
    finally:
        if os.path.exists(config_path):
            os.remove(config_path)

def test_logger_valid_forecast(monkeypatch):
    """Test that the logger processes a valid forecast correctly."""
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    os.makedirs(os.path.join(root_dir, 'tests/forecast'), exist_ok=True)

    # Use the forecast folder as specified in the config
    forecast_folder = os.path.join(root_dir, 'tests/forecast')  # Use absolute path
    output_csv = os.path.join(root_dir, 'tests/nq_daily_eval.csv')
    config_path = os.path.join(root_dir, 'config.yaml')
    
    # Patch getcwd to return root directory
    monkeypatch.setattr('os.getcwd', lambda: root_dir)

    cfg = {
            'forecast_folder': forecast_folder,
            'output_csv': output_csv
        }
    # Create forecast in the correct location
    root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    forecast_path = os.path.join(root_dir, forecast_folder, "2025-07-31.json")
    os.makedirs(os.path.dirname(forecast_path), exist_ok=True)
    with open(forecast_path, "w") as f:
        json.dump({
            "scenario": "fade",
            "resistance": 23650,
            "support": 23400,
            "sigma_plus": 23725,
            "sigma_minus": 23240
        }, f)
    assert os.path.exists(forecast_path), f"Forecast file not found at {forecast_path}"

    try:
        with open(config_path, 'w') as f:
            f.write("""
            forecast_folder: tests/forecast
            output_csv: nq_daily_eval.csv
            schedule_time: "16:30"
            slack_webhook_url: http://example.com/webhook
            thinkorswim:
              host: localhost
              port: 8080
              use_ssl: false
            """)

        # Create an empty CSV file
        with open(output_csv, 'w') as f:
            f.write("date,scenario,hit\n")

        print(f"Forecast folder: {forecast_folder}")
        print(f"Forecast path: {forecast_path}")
        print(f"Output CSV: {output_csv}")

        monkeypatch.setattr('prediction_vs_reality_logger.config.load_config', lambda: {
            'forecast_folder': forecast_folder,  # Match the path in config.yaml
            'output_csv': output_csv,
            'schedule_time': "16:30",
            'slack_webhook_url': "http://example.com/webhook",
            'thinkorswim': {
                'host': 'localhost',
                'port': 8080,
                'use_ssl': False
            }
        })

        run(date=datetime(2025, 7, 31), actuals_source=mock_actuals_source)

        # Validate CSV output
        df = pd.read_csv(output_csv)
        assert not df.empty
        assert df.iloc[0]['scenario'] == 'fade'
        assert df.iloc[0]['hit'] == 1
    finally:
        if os.path.exists(forecast_path):
            os.remove(forecast_path)
        if os.path.exists(output_csv):
            os.remove(output_csv)
        if os.path.exists(config_path):
            os.remove(config_path)

def validate_forecast_path_consistency(config_path: str, forecast_filename: str) -> None:
    """
    Validates that the forecast file exists at the location specified in the config.
    Raises descriptive errors if mismatch is found.

    Args:
        config_path (str): Path to the configuration JSON file.
        forecast_filename (str): Filename of the forecast file to check.
    """
    # Resolve absolute path to config
    config_path = os.path.abspath(config_path)

    # Load config
    with open(config_path, "r") as f:
        cfg = json.load(f)

    # Get forecast folder from config, resolve relative to CWD
    forecast_folder = cfg.get("forecast_folder")
    if not forecast_folder:
        raise KeyError("Config missing required 'forecast_folder' key")

    # Create the forecast file using the config's path
    project_root = Path(__file__).resolve().parents[1]
    forecast_path = project_root / forecast_folder / forecast_filename

    # Debug output
    print(f"[CONFIG] forecast_folder = {forecast_folder}")
    print(f"[EXPECTED] Forecast file = {forecast_path}")
    print(f"[CWD] Current Working Dir = {os.getcwd()}")

    # Assert path validity
    if not os.path.exists(forecast_path):
        raise FileNotFoundError(
            f"Forecast file '{forecast_filename}' not found in '{forecast_folder}'.\n"
            f"Check config['forecast_folder'] and file creation path for alignment."
        )
    print("[PASS] Forecast path validated successfully.")

# Add this validation to the test suite
def test_forecast_path_alignment():
    validate_forecast_path_consistency(
        config_path="tests/config/test_config.json",
        forecast_filename="2025-07-31.json"
    )
