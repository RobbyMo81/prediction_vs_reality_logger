import abc
import os
import json
from datetime import datetime
from pathlib import Path
from .forecast_schema import Forecast
from pydantic import ValidationError

class ForecastSource(abc.ABC):
    @abc.abstractmethod
    def load(self, date: datetime) -> dict:
        """Load forecast data for a given date."""
        pass

class JSONFileForecastSource(ForecastSource):
    def __init__(self, folder: str, actuals_source=None):
        self.folder = folder  # Keep the folder path as provided
        self.actuals_source = actuals_source

    def load(self, date: datetime) -> dict:
        """
        Load and validate forecast data for a given date using pydantic schema.
        Returns the validated forecast dict or raises ValueError/ValidationError.
        """
        folder_path = self.folder
        if not os.path.isabs(folder_path):
            folder_path = os.path.abspath(os.path.join(os.getcwd(), self.folder))

        filename = os.path.join(folder_path, date.strftime("%Y-%m-%d") + ".json")
        if not os.path.exists(folder_path):
            raise FileNotFoundError(f"Forecast directory not found: {folder_path}")

        try:
            with open(filename, 'r') as f:
                data = json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"No forecast found for {date}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid forecast data for {date}: {e}")

        # Validate schema using pydantic
        try:
            forecast = Forecast(**data)
        except ValidationError as e:
            raise ValueError(f"Forecast schema validation failed for {date}: {e}")
        # Optionally, return the validated model as dict
        return forecast.dict()

    def get_actuals(self, date):
        return self.actuals_source.get_actuals(date) if self.actuals_source else None

class ActualsSource(abc.ABC):
    @abc.abstractmethod
    def get_actuals(self, date) -> dict:
        """Return a dict of actuals for the given date."""
        pass

class StubActualsSource(ActualsSource):
    def get_actuals(self, date):
        return {
            'high': 23660,
            'low': 23410,
            'close': 23500
        }


class FileActualsSource(ActualsSource):
    """
    Loads actuals from a JSON file in a folder, named YYYY-MM-DD.actuals.json.
    """
    def __init__(self, folder):
        self.folder = folder

    def get_actuals(self, date):
        file_name = date.strftime("%Y-%m-%d.actuals.json")
        file_path = os.path.join(self.folder, file_name)
        try:
            with open(file_path, 'r') as f:
                return json.load(f)
        except FileNotFoundError:
            raise FileNotFoundError(f"No actuals found for {date}")
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid actuals data for {date}: {e}")

def get_actuals_source_from_config(cfg):
    """
    Factory to create an ActualsSource based on config dict.
    Supports 'stub' and 'file' types.
    """
    typ = cfg.get('actuals_source', 'stub')
    if typ == 'stub':
        return StubActualsSource()
    elif typ == 'file':
        folder = cfg.get('actuals_folder', './actuals')
        return FileActualsSource(folder)
    else:
        raise ValueError(f"Unknown actuals_source type: {typ}")