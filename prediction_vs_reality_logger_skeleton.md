# Repository Skeleton: prediction_vs_reality_logger

```
.
├── venv/                      # Python virtual environment
├── start-app.ps1              # Unified startup script with initialization checks
├── config.yaml               # Centralized settings
├── pyproject.toml            # Packaging & versioning
├── prediction_logger/        # Main package
│   ├── __init__.py
│   ├── config.py             # YAML loader & validation
│   ├── version.py            # __version__
│   ├── sources.py            # ForecastSource interface + implementations with errors
│   ├── logger.py             # Core logging logic with injectable actuals and error handling
│   ├── cli.py                # CLI entrypoint (Click) with global exception handler
│   ├── notifications.py      # Alerting (Slack/email) with retries
│   └── thinkorswim.py        # Thinkorswim socket client with safe-run wrapper
├── Dockerfile                # Containerization
├── k8s/
│   └── cronjob.yaml          # Kubernetes CronJob manifest (UTC schedule)
├── tests/                    # Unit tests for each module
│   ├── test_config.py
│   ├── test_version.py
│   ├── test_sources.py
│   ├── test_logger.py
│   ├── test_cli.py
│   ├── test_notifications.py
│   └── test_thinkorswim.py
├── dashboard/
│   └── rolling_metrics.ipynb # Notebook stub
└── README.md                 # Usage & developer guide
```
```

---

## prediction_logger/config.py
```python
import os
import yaml

# Required configuration keys with default sources
REQUIRED_KEYS = [
    'forecast_folder', 'output_csv', 'schedule_time',
    'slack_webhook_url', 'thinkorswim'
]

CONFIG = None

def load_config():
    """
    Load configuration from config.yaml or environment variables,
    validate required keys, and cache result.
    """
    global CONFIG
    if CONFIG is None:
        base = os.getcwd()
        path = os.path.join(base, 'config.yaml')
        try:
            with open(path, 'r') as f:
                raw = yaml.safe_load(f) or {}
        except FileNotFoundError:
            raise FileNotFoundError(f"Configuration file not found at {path}")

        # Override with environment variables
        cfg = {}
        for key, val in raw.items():
            if isinstance(val, str) and val.startswith('${'):
                # ENV var override syntax: ${KEY:-default}
                env, default = val.strip('${}').split(':-')
                cfg[key] = os.getenv(env, default)
            else:
                cfg[key] = val

        # Validate required
        missing = [k for k in REQUIRED_KEYS if k not in cfg]
        if missing:
            raise KeyError(f"Missing required config keys: {missing}")

        CONFIG = cfg
    return CONFIG
```

## prediction_logger/sources.py
```python
import abc
import os
import json
from datetime import datetime

class ForecastSource(abc.ABC):
    @abc.abstractmethod
    def load(self, date: datetime) -> dict:
        """Load forecast data for a given date."""
        pass

class JSONFileForecastSource(ForecastSource):
    def __init__(self, folder: str):
        self.folder = folder

    def load(self, date: datetime) -> dict:
        filename = os.path.join(self.folder, date.strftime("%Y-%m-%d") + ".json")
        try:
            with open(filename, 'r') as f:
                data = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"Forecast file not found: {filename}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in {filename}: {e}")

        # Validate essential keys
        if 'scenario' not in data or 'resistance' not in data:
            raise KeyError(f"Forecast JSON missing required fields in {filename}")
        return data
```

## prediction_logger/logger.py
```python
import logging
import pandas as pd
from datetime import datetime
from .config import load_config
from .sources import JSONFileForecastSource


def run(date: datetime = None, actuals_source=None):  # pylint: disable=unused-argument
    """
    Execute one logging cycle: load forecast, fetch actuals, record result.
    """
    cfg = load_config()
    date = date or datetime.now()
    folder = cfg['forecast_folder']
    source = JSONFileForecastSource(folder)

    try:
        forecast = source.load(date)
    except Exception as e:
        logging.error(f"Failed to load forecast: {e}")
        from .notifications import notify
        notify(f"Error loading forecast for {date}: {e}")
        return

    # Fetch actuals via injection or default stub
    try:
        if actuals_source:
            actuals = actuals_source(date)
        else:
            # TODO: replace with real data connector
            actuals = {'high': forecast['resistance'] + 1, 'low': forecast.get('support', 0) - 1}
    except Exception as e:
        logging.error(f"Failed to fetch actuals: {e}")
        from .notifications import notify
        notify(f"Error fetching actuals for {date}: {e}")
        return

    # Evaluate hit
    scenario = forecast['scenario']
    try:
        if scenario == 'breakout':
            hit = actuals['high'] >= forecast['resistance']
        elif scenario == 'fade':
            hit = actuals['high'] <= forecast['resistance']
        else:
            logging.warning(f"Unknown scenario '{scenario}'")
            hit = False
    except Exception as e:
        logging.error(f"Error evaluating scenario: {e}")
        notify(f"Evaluation error for {date}: {e}")
        return

    row = {
        'date': date.strftime("%Y-%m-%d"),
        'scenario': scenario,
        'hit': int(hit),
    }

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

    df = df.append(row, ignore_index=True)
    try:
        df.to_csv(csv_file, index=False)
    except Exception as e:
        logging.error(f"Error writing CSV: {e}")
        notify(f"CSV write error: {e}")
```

## prediction_logger/cli.py
```python
import click
import logging
from dateutil.parser import parse
from .logger import run


def setup_logging(verbose):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format='[%(levelname)s] %(message)s')

@click.command()
@click.option('--date', help='Date for forecast (YYYY-MM-DD)', default=None)
@click.option('--dry-run', is_flag=True, help='Preview without writing outputs')
@click.option('--verbose', is_flag=True, help='Enable verbose logging')
def main(date, dry_run, verbose):
    setup_logging(verbose)
    try:
        logging.debug(f"CLI invoked for date={date}, dry_run={dry_run}")
        if dry_run:
            logging.info("DRY RUN: exiting without changes")
            return
        run(parse(date) if date else None)
    except Exception as e:
        logging.critical(f"Unhandled error: {e}")
        from .notifications import notify
        notify(f"Critical failure in CLI: {e}")
        raise

if __name__ == '__main__':
    main()
```

## prediction_logger/notifications.py
```python
import requests
import logging
import time
from .config import load_config


def notify(message: str):
    cfg = load_config()
    url = cfg.get('slack_webhook_url')
    secondary = cfg.get('secondary_webhook_url')
    payload = {'text': message}

    if url:
        for attempt in range(3):
            try:
                resp = requests.post(url, json=payload, timeout=5)
                resp.raise_for_status()
                logging.info("Slack notification sent")
                return
            except Exception as e:
                logging.error(f"Slack notify attempt {attempt+1} failed: {e}")
                time.sleep(2 ** attempt)
    if secondary:
        try:
            resp = requests.post(secondary, json=payload, timeout=5)
            resp.raise_for_status()
            logging.info("Secondary notify sent")
        except Exception as e:
            logging.error(f"Secondary notify failed: {e}")
```

## prediction_logger/thinkorswim.py
```python
import asyncio
import json
import websockets
import logging
from .config import load_config

async def _connect():
    cfg = load_config()
    host = cfg['thinkorswim']['host']
    port = cfg['thinkorswim']['port']
    use_ssl = cfg['thinkorswim']['use_ssl']
    scheme = 'wss' if use_ssl else 'ws'
    uri = f"{scheme}://{host}:{port}"
    try:
        async with websockets.connect(uri) as ws:
            await ws.send(json.dumps({"action": "subscribe", "symbols": ["NQ"]}))
            async for msg in ws:
                data = json.loads(msg)
                logging.debug(f"Received market data: {data}")
    except Exception as e:
        logging.error(f"Thinkorswim socket error: {e}")


def run_socket():
    try:
        asyncio.run(_connect())
    except Exception as e:
        logging.critical(f"Socket run failed: {e}")
```

---
All modules now include robust error handling, validation, and clear logging/notification paths. Let me know if you want deeper enhancements!


## start-app.ps1
```powershell
<#
.SYNOPSIS
    Initialize and start the Prediction vs Reality Logger application.
.DESCRIPTION
    Checks for Python virtual environment, activates it, installs dependencies if needed,
    and runs the CLI. Reports errors and exits with a non-zero code on failure.
#>
param(
    [string]$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
)

# Navigate to script directory
Set-Location $ScriptDir

# Check for virtual environment activation script
$venvActivate = Join-Path $ScriptDir 'venv\Scripts\Activate.ps1'
if (-Not (Test-Path $venvActivate)) {
    Write-Host "Error: Virtual environment not found. Please run 'python -m venv venv'." -ForegroundColor Red
    exit 1
}

# Activate virtual environment
try {
    . $venvActivate
} catch {
    Write-Host "Error activating virtual environment: $_" -ForegroundColor Red
    exit 1
}

# Install or update dependencies
if (-Not (Test-Path "venv\Lib\site-packages\prediction_logger")) {
    Write-Host "Installing dependencies..."
    try {
        pip install .
    } catch {
        Write-Host "Dependency installation failed: $_" -ForegroundColor Red
        exit 1
    }
}

# Run the application
try {
    prediction-logger --verbose
} catch {
    Write-Host "Application execution failed: $_" -ForegroundColor Red
    exit 1
}
```

