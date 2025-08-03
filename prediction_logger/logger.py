import logging
import os
import json
import pandas as pd
from datetime import datetime
from .config import load_config
from .sources import JSONFileForecastSource, ActualsSource, StubActualsSource
from .notifications import notify
from pathlib import Path

logging.basicConfig(level=logging.DEBUG)
logging.debug(f"Current working directory: {os.getcwd()}")


def run(date: datetime | None = None, actuals_source: 'ActualsSource | None' = None, tensor_model=None, translator=None):
    """
    Execute one logging cycle: load forecast, fetch actuals, record result.
    """
    cfg = load_config()
    date = date or datetime.now()
    folder = cfg['forecast_folder']
    source = JSONFileForecastSource(folder, actuals_source or StubActualsSource())
    try:
        forecast = source.load(date)
    except Exception as e:
        logging.error(f"Failed to load forecast: {e}")
        notify(f"Error loading forecast for {date}: {e}")
        return
    # Fetch actuals via pluggable source
    try:
        actuals = source.get_actuals(date)
    except Exception as e:
        logging.error(f"Failed to fetch actuals: {e}")
        notify(f"Error fetching actuals for {date}: {e}")
        return
    # Evaluate hit with expanded scenario support
    scenario = forecast['scenario']
    try:
        if not isinstance(actuals, dict) or not isinstance(forecast, dict):
            logging.error(f"actuals or forecast is not a dict. actuals={actuals}, forecast={forecast}")
            notify(f"Evaluation error for {date}: actuals or forecast is not a dict.")
            return
        # Expanded scenario support
        if scenario == 'breakout':
            # Hit if high >= resistance
            hit = actuals['high'] >= forecast['resistance']
        elif scenario == 'fade':
            # Hit if high <= support (or resistance if no support)
            reference_level = forecast.get('support', forecast['resistance'])
            hit = actuals['high'] <= reference_level
        elif scenario == 'range':
            # Hit if low >= support and high <= resistance
            hit = (actuals['low'] >= forecast.get('support', 0)) and (actuals['high'] <= forecast['resistance'])
        elif scenario == 'trend':
            # Hit if close > open
            hit = actuals.get('close', 0) > actuals.get('open', 0)
        elif scenario == 'reversal':
            # Hit if close < open
            hit = actuals.get('close', 0) < actuals.get('open', 0)
        elif scenario == 'momentum':
            # Hit if close > previous close (requires previous actuals)
            prev_close = actuals.get('prev_close')
            hit = prev_close is not None and actuals.get('close', 0) > prev_close
        else:
            logging.warning(f"Unknown scenario '{scenario}'")
            hit = False
    except Exception as e:
        logging.error(f"Error evaluating scenario: {e}")
        notify(f"Evaluation error for {date}: {e}")
        return
    # Tensor model prediction (optional)
    tensor_output = None
    llm_summary = None
    if tensor_model is not None:
        try:
            # Example: use [predicted, actual] as features, can be customized
            features = [forecast.get('resistance', 0), actuals.get('close', 0)]
            tensor_output = tensor_model.predict(features)
        except Exception as e:
            logging.error(f"Tensor model prediction error: {e}")
    # LLM summary (optional)
    if translator is not None and tensor_output is not None:
        try:
            llm_summary = translator.summarize_tensor_output(tensor_output, context=forecast)
        except Exception as e:
            logging.error(f"LLM summary error: {e}")
    # Record result with schema v1.0 + tensor/llm fields

    row = {
        'date': date.strftime("%Y-%m-%d"),
        'symbol': forecast.get('symbol', '/NQ'),
        'predicted': forecast.get('resistance', None),
        'actual': actuals.get('close', None) if isinstance(actuals, dict) else None,
        'scenario': scenario,
        'result': 'hit' if hit else 'miss',
        'version': 'v1.0',
    }
    if tensor_output is not None:
        row['tensor_output'] = tensor_output
    if llm_summary is not None:
        row['llm_summary'] = llm_summary

    # Append to CSV
    csv_file = cfg['output_csv']
    try:
        df = pd.read_csv(csv_file)
    except FileNotFoundError:
        df = pd.DataFrame(columns=list(row.keys()))
    except Exception as e:
        logging.error(f"Error reading CSV: {e}")
        notify(f"CSV read error: {e}")
        return
    # Create a new row DataFrame and concatenate
    new_row = pd.DataFrame([row])
    df = pd.concat([df, new_row], ignore_index=True)

    # Ensure parent directory exists
    os.makedirs(os.path.dirname(csv_file), exist_ok=True)

    try:
        df.to_csv(csv_file, index=False)
    except Exception as e:
        logging.error(f"Error writing CSV: {e}")
        notify(f"CSV write error: {e}")

    # Write schema/version metadata YAML file
    metadata_path = os.path.splitext(csv_file)[0] + '_metadata.yaml'
    import yaml
    metadata = {
        'schema_version': 'v1.0',
        'fields': list(row.keys()),
        'last_updated': datetime.now().isoformat(),
    }
    try:
        with open(metadata_path, 'w') as f:
            yaml.safe_dump(metadata, f)
    except Exception as e:
        logging.error(f"Error writing metadata YAML: {e}")


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
    try:
        with open(config_path, "r") as f:
            cfg = json.load(f)
    except FileNotFoundError:
        raise FileNotFoundError(f"Config file not found: {config_path}")
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON in config file: {e}")

    # Get forecast folder from config, resolve relative to CWD
    forecast_folder = cfg.get("forecast_folder")
    if not forecast_folder:
        raise KeyError("Config missing required 'forecast_folder' key")

    # Resolve to absolute path relative to CWD
    config_folder = os.path.abspath(forecast_folder)
    forecast_path = os.path.join(config_folder, forecast_filename)

    # Debug output
    print(f"[CONFIG] forecast_folder = {config_folder}")
    print(f"[EXPECTED] Forecast file = {forecast_path}")
    print(f"[CWD] Current Working Dir = {os.getcwd()}")

    # Assert path validity
    if not os.path.exists(forecast_path):
        raise FileNotFoundError(
            f"Forecast file '{forecast_filename}' not found in '{config_folder}'.\n"
            f"Check config['forecast_folder'] and file creation path for alignment."
        )