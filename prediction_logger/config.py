import os
import yaml
from pathlib import Path

# Required configuration keys with default sources
REQUIRED_KEYS = [
    'forecast_folder', 'output_csv', 'schedule_time',
    'slack_webhook_url', 'thinkorswim'
]
CONFIG = None

def parse_env_var_override(val: str) -> str:
    """
    Parse env var override syntax: ${ENV_VAR:-default}
    Returns the value from the environment or the default.
    """
    if val.startswith('${') and val.endswith('}:-default}'):  # Defensive, but not needed for standard
        val = val[2:-1]
    if val.startswith('${') and ':-' in val:
        env, default = val.strip('${}').split(':-', 1)
        return os.getenv(env, default)
    return val

def validate_config(cfg: dict):
    """
    Validate that all required config keys are present.
    """
    missing = [k for k in REQUIRED_KEYS if k not in cfg]
    if missing:
        raise KeyError(f"Missing required config keys: {missing}")

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
                cfg[key] = parse_env_var_override(val)
            else:
                cfg[key] = val
        validate_config(cfg)
        CONFIG = cfg
    return CONFIG