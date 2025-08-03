
import os
import sys
import time
import json
import logging
import argparse
import pandas as pd
import yaml
import requests

def validate_results():

    # --- Logging setup ---
    logger = logging.getLogger("validate_results")
    logger.setLevel(logging.INFO)
    log_formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
    # File handler
    file_handler = logging.FileHandler('validation.log')
    file_handler.setFormatter(log_formatter)
    logger.addHandler(file_handler)
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(log_formatter)
    logger.addHandler(console_handler)

    def notify_slack(message: str):
        webhook_url = os.environ.get("SLACK_WEBHOOK")
        if webhook_url:
            try:
                requests.post(webhook_url, json={"text": message}, timeout=5)
            except Exception as e:
                logger.warning(f"Failed to send Slack notification: {e}")

    def read_file_with_retry(path, mode='r', retries=3):
        for i in range(retries):
            try:
                with open(path, mode) as f:
                    return f.read()
            except IOError as e:
                if i < retries - 1:
                    time.sleep(2 ** i)
                else:
                    raise

    results_path = os.getenv("RESULTS_FILE_PATH")
    schema_path = os.getenv("SCHEMA_FILE_PATH")

    report = {
        "file_valid": False,
        "missing_fields": [],
        "schema_errors": [],
        "row_errors": [],
        "valid_rows": 0,
        "invalid_rows": 0
    }

    # --- Env var checks ---
    if not results_path:
        logger.error("Missing RESULTS_FILE_PATH environment variable.")
        notify_slack(":x: Validation failed: Missing RESULTS_FILE_PATH env var.")
        report["schema_errors"].append("Missing RESULTS_FILE_PATH environment variable.")
        return report, 1
    if not schema_path:
        logger.error("Missing SCHEMA_FILE_PATH environment variable.")
        notify_slack(":x: Validation failed: Missing SCHEMA_FILE_PATH env var.")
        report["schema_errors"].append("Missing SCHEMA_FILE_PATH environment variable.")
        return report, 1

    # --- Load CSV ---
    try:
        csv_data = read_file_with_retry(results_path)
        from io import StringIO
        df = pd.read_csv(StringIO(csv_data))
    except FileNotFoundError:
        logger.error(f"Results file not found: {results_path}")
        notify_slack(f":x: Validation failed: Results file not found: {results_path}")
        report["schema_errors"].append(f"Results file not found: {results_path}")
        return report, 2
    except pd.errors.EmptyDataError:
        logger.error(f"Results file is empty: {results_path}")
        notify_slack(f":x: Validation failed: Results file is empty: {results_path}")
        report["schema_errors"].append(f"Results file is empty: {results_path}")
        return report, 2
    except Exception as e:
        logger.error(f"Failed to read results file: {e}")
        notify_slack(f":x: Validation failed: Failed to read results file: {e}")
        report["schema_errors"].append(f"Failed to read results file: {e}")
        return report, 2

    # --- Load YAML schema ---
    try:
        schema_data = read_file_with_retry(schema_path)
        if schema_data is None:
            raise FileNotFoundError(f"Schema file not found or empty: {schema_path}")
        schema = yaml.safe_load(schema_data)
    except FileNotFoundError:
        logger.error(f"Schema file not found: {schema_path}")
        notify_slack(f":x: Validation failed: Schema file not found: {schema_path}")
        report["schema_errors"].append(f"Schema file not found: {schema_path}")
        return report, 2
    except yaml.YAMLError as e:
        logger.error(f"Failed to parse schema YAML: {e}")
        notify_slack(f":x: Validation failed: Failed to parse schema YAML: {e}")
        report["schema_errors"].append(f"Failed to parse schema YAML: {e}")
        return report, 3
    except Exception as e:
        logger.error(f"Failed to read schema file: {e}")
        notify_slack(f":x: Validation failed: Failed to read schema file: {e}")
        report["schema_errors"].append(f"Failed to read schema file: {e}")
        return report, 2

    # --- Validate schema structure ---
    if not isinstance(schema, dict) or "fields" not in schema:
        logger.error("Schema file missing required 'fields' key.")
        notify_slack(":x: Validation failed: Schema file missing required 'fields' key.")
        report["schema_errors"].append("Schema file missing required 'fields' key.")
        return report, 3

    required_fields = [field for field in schema["fields"]]
    for index, row in df.iterrows():
        row_errors = []
        for field in required_fields:
            value = row.get(field) if hasattr(row, 'get') else row[field] if field in row else None
            is_missing = value is None
            try:
                if not is_missing:
                    is_missing = bool(pd.isna(value))
            except Exception:
                pass
            if is_missing:
                row_errors.append(f"Missing {field}")
        if row_errors:
            report["invalid_rows"] += 1
            report["row_errors"].append({"row": index, "errors": row_errors})
        else:
            report["valid_rows"] += 1

    # --- Final report and exit code ---
    if report["schema_errors"]:
        report["file_valid"] = False
        logger.error("Schema validation failed.")
        notify_slack(":x: Schema validation failed.")
        return report, 3
    if report["invalid_rows"] > 0:
        report["file_valid"] = False
        logger.warning(f"Validation completed with {report['invalid_rows']} invalid rows.")
        notify_slack(f":warning: Validation completed with {report['invalid_rows']} invalid rows.")
        return report, 4
    report["file_valid"] = True
    logger.info("Validation succeeded. All rows valid.")
    notify_slack(":white_check_mark: Validation succeeded. All rows valid.")
    return report, 0


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate results file against schema.")
    parser.add_argument('--json-report', action='store_true', help='Write validation_summary.json for CI/CD')
    args = parser.parse_args()

    report, exit_code = validate_results()
    print(json.dumps(report, indent=2))
    if args.json_report:
        with open("validation_summary.json", "w") as f:
            json.dump(report, f, indent=2)
    sys.exit(exit_code)
