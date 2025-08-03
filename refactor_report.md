# 🛠 Refactor Report

## 🔄 Refactored Forecast Path References
- `test_logger.py`: Line 1
  - Old: `import sysimport ossys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))# Existing importsimport pytestimport pandas as pdfrom datetime import datetimefrom prediction_logger.logger import runfrom prediction_logger.sources import JSONFileForecastSourceimport jsonimport timefrom pathlib import Pathdef mock_actuals_source(date):    """Mock actuals source for testing."""    return {        'high': 23660,        'low': 23410,        'close': 23500    }def test_logger_missing_forecast(monkeypatch):    """Test that the logger handles missing forecast files gracefully."""    monkeypatch.setattr('os.getcwd', lambda: os.path.dirname(__file__))  # Mock current directory    forecast_folder = 'tests/forecast'  # Use relative path consistently    project_root = Path(__file__).resolve().parents[1]    forecast_path = project_root / 'forecast' / forecast_filename    config_path = os.path.join(os.getcwd(), 'config.yaml')    try:        with open(config_path, 'w') as f:            f.write("""            forecast_folder: tests/forecast            output_csv: nq_daily_eval.csv            schedule_time: "16:30"            slack_webhook_url: http://example.com/webhook            thinkorswim:              host: localhost              port: 8080              use_ssl: false            """)        print(f"Forecast folder: {forecast_folder}")        print(f"Config path: {config_path}")        monkeypatch.setattr('prediction_logger.config.load_config', lambda: {            'forecast_folder': forecast_folder,  # Use the relative path            'output_csv': 'nq_daily_eval.csv'  # Use relative path        })        run(date=datetime(2025, 7, 31), actuals_source=mock_actuals_source)    except SystemExit as e:        assert e.code == 1  # Ensure the script exits with code 1    finally:        if os.path.exists(config_path):            os.remove(config_path)def test_logger_valid_forecast(monkeypatch):    """Test that the logger processes a valid forecast correctly."""    test_dir = os.path.dirname(__file__)    os.makedirs(os.path.join(test_dir, 'forecast'), exist_ok=True)    # Use the forecast folder as specified in the config    forecast_folder = 'tests/forecast'  # Match path in config.yaml    output_csv = os.path.join(test_dir, 'nq_daily_eval.csv')    config_path = os.path.join(test_dir, 'config.yaml')        # Patch getcwd to return test directory    monkeypatch.setattr('os.getcwd', lambda: test_dir)    cfg = {            'forecast_folder': forecast_folder,            'output_csv': output_csv        }    # Create forecast in the correct location    forecast_path = os.path.join(os.path.dirname(test_dir), cfg['forecast_folder'], "2025-07-31.json")    os.makedirs(os.path.dirname(forecast_path), exist_ok=True)    with open(forecast_path, "w") as f:        json.dump({            "scenario": "fade",            "resistance": 23650,            "support": 23400,            "sigma_plus": 23725,            "sigma_minus": 23240        }, f)    assert os.path.exists(forecast_path), f"Forecast file not found at {forecast_path}"    try:        with open(config_path, 'w') as f:            f.write("""            forecast_folder: tests/forecast            output_csv: nq_daily_eval.csv            schedule_time: "16:30"            slack_webhook_url: http://example.com/webhook            thinkorswim:              host: localhost              port: 8080              use_ssl: false            """)        # Create an empty CSV file        with open(output_csv, 'w') as f:            f.write("date,scenario,hit\n")        print(f"Forecast folder: {forecast_folder}")        print(f"Forecast path: {forecast_path}")        print(f"Output CSV: {output_csv}")        monkeypatch.setattr('prediction_logger.config.load_config', lambda: {            'forecast_folder': 'tests/forecast',  # Match the path in config.yaml            'output_csv': output_csv,            'schedule_time': "16:30",            'slack_webhook_url': "http://example.com/webhook",            'thinkorswim': {                'host': 'localhost',                'port': 8080,                'use_ssl': False            }        })        run(date=datetime(2025, 7, 31), actuals_source=mock_actuals_source)        # Validate CSV output        df = pd.read_csv(output_csv)        assert not df.empty        assert df.iloc[0]['scenario'] == 'fade'        assert df.iloc[0]['hit'] == 1    finally:        if os.path.exists(forecast_path):            os.remove(forecast_path)        if os.path.exists(output_csv):            os.remove(output_csv)        if os.path.exists(config_path):            os.remove(config_path)def validate_forecast_path_consistency(config_path: str, forecast_filename: str) -> None:    """    Validates that the forecast file exists at the location specified in the config.    Raises descriptive errors if mismatch is found.    Args:        config_path (str): Path to the configuration JSON file.        forecast_filename (str): Filename of the forecast file to check.    """    # Resolve absolute path to config    config_path = os.path.abspath(config_path)    # Load config    with open(config_path, "r") as f:        cfg = json.load(f)    # Resolve forecast folder from config    config_folder = os.path.abspath(cfg.get("forecast_folder", ""))    forecast_path = os.path.join(config_folder, forecast_filename)    # Debug output    print(f"[CONFIG] forecast_folder = {config_folder}")    print(f"[EXPECTED] Forecast file = {forecast_path}")    print(f"[CWD] Current Working Dir = {os.getcwd()}")    # Assert path validity    if not os.path.exists(forecast_path):        raise FileNotFoundError(            f"Forecast file '{forecast_filename}' not found in '{config_folder}'.\n"            f"Check config['forecast_folder'] and file creation path for alignment."        )    print("[PASS] Forecast path validated successfully.")# Add this validation to the test suitedef test_forecast_path_alignment():    validate_forecast_path_consistency(        config_path="tests/config/test_config.json",        forecast_filename="2025-07-31.json"    )`
  - New: `forecast_path = Path(test_dir).parent / '[    forecast_folder, output_csv, schedule_time,    slack_webhook_url, thinkorswim]CONFIG' / forecast_filename`

---
## ✅ Test Outcomes
```
============================= test session starts =============================
platform win32 -- Python 3.13.2, pytest-8.3.2, pluggy-1.6.0 -- C:\Users\RobMo\dev\tools\python.exe
cachedir: .pytest_cache
rootdir: C:\Users\RobMo\OneDrive\Documents\prediction-vs-reality-logger
configfile: pyproject.toml
plugins: cov-6.2.1
collecting ... collected 0 items / 7 errors

=================================== ERRORS ====================================
_____________________ ERROR collecting tests/test_cli.py ______________________
..\..\..\dev\tools\Lib\site-packages\_pytest\python.py:493: in importtestmodule
    mod = import_path(
..\..\..\dev\tools\Lib\site-packages\_pytest\pathlib.py:582: in import_path
    importlib.import_module(module_name)
..\..\..\dev\tools\Lib\importlib\__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
<frozen importlib._bootstrap>:1387: in _gcd_import
    ???
<frozen importlib._bootstrap>:1360: in _find_and_load
    ???
<frozen importlib._bootstrap>:1331: in _find_and_load_unlocked
    ???
<frozen importlib._bootstrap>:935: in _load_unlocked
    ???
..\..\..\dev\tools\Lib\site-packages\_pytest\assertion\rewrite.py:165: in exec_module
    source_stat, co = _rewrite_test(fn, self.config)
..\..\..\dev\tools\Lib\site-packages\_pytest\assertion\rewrite.py:345: in _rewrite_test
    tree = ast.parse(source, filename=strfn)
..\..\..\dev\tools\Lib\ast.py:54: in parse
    return compile(source, filename, mode, flags,
E     File "C:\Users\RobMo\OneDrive\Documents\prediction-vs-reality-logger\tests\test_cli.py", line 1
E       from pathlib import Pathdef test_cli_invocation():    # Placeholder test for CLI    assert True
E                                   ^^^^^^^^^^^^^^^^^^^
E   SyntaxError: invalid syntax
____________________ ERROR collecting tests/test_config.py ____________________
..\..\..\dev\tools\Lib\site-packages\_pytest\python.py:493: in importtestmodule
    mod = import_path(
..\..\..\dev\tools\Lib\site-packages\_pytest\pathlib.py:582: in import_path
    importlib.import_module(module_name)
..\..\..\dev\tools\Lib\importlib\__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
<frozen importlib._bootstrap>:1387: in _gcd_import
    ???
<frozen importlib._bootstrap>:1360: in _find_and_load
    ???
<frozen importlib._bootstrap>:1331: in _find_and_load_unlocked
    ???
<frozen importlib._bootstrap>:935: in _load_unlocked
    ???
..\..\..\dev\tools\Lib\site-packages\_pytest\assertion\rewrite.py:165: in exec_module
    source_stat, co = _rewrite_test(fn, self.config)
..\..\..\dev\tools\Lib\site-packages\_pytest\assertion\rewrite.py:345: in _rewrite_test
    tree = ast.parse(source, filename=strfn)
..\..\..\dev\tools\Lib\ast.py:54: in parse
    return compile(source, filename, mode, flags,
E     File "C:\Users\RobMo\OneDrive\Documents\prediction-vs-reality-logger\tests\test_config.py", line 1
E       import sysimport ossys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))# Existing importsimport pytestfrom prediction_logger.config import load_configfrom pathlib import Pathdef test_load_config_missing_file(monkeypatch):    """Test that a missing config file raises FileNotFoundError."""    monkeypatch.setattr('os.getcwd', lambda: os.path.dirname(__file__))  # Mock current directory    config_path = os.path.join(os.getcwd(), 'config.yaml')    if os.path.exists(config_path):        os.remove(config_path)  # Ensure file does not exist    with pytest.raises(FileNotFoundError):        load_config()def test_load_config_missing_keys(monkeypatch):    """Test that missing required keys raise KeyError."""    monkeypatch.setattr('os.getcwd', lambda: os.path.dirname(__file__))  # Mock current directory    config_path = os.path.join(os.getcwd(), 'config.yaml')    try:        with open(config_path, 'w') as f:            f.write("{}")  # Empty config        with pytes
E                        ^^^^^
E   SyntaxError: invalid syntax
____________________ ERROR collecting tests/test_logger.py ____________________
tests\test_logger.py:1: in <module>
    forecast_path = Path(test_dir).parent / '[    forecast_folder, output_csv, schedule_time,    slack_webhook_url, thinkorswim]CONFIG' / forecast_filename
E   NameError: name 'Path' is not defined
________________ ERROR collecting tests/test_notifications.py _________________
..\..\..\dev\tools\Lib\site-packages\_pytest\python.py:493: in importtestmodule
    mod = import_path(
..\..\..\dev\tools\Lib\site-packages\_pytest\pathlib.py:582: in import_path
    importlib.import_module(module_name)
..\..\..\dev\tools\Lib\importlib\__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
<frozen importlib._bootstrap>:1387: in _gcd_import
    ???
<frozen importlib._bootstrap>:1360: in _find_and_load
    ???
<frozen importlib._bootstrap>:1331: in _find_and_load_unlocked
    ???
<frozen importlib._bootstrap>:935: in _load_unlocked
    ???
..\..\..\dev\tools\Lib\site-packages\_pytest\assertion\rewrite.py:165: in exec_module
    source_stat, co = _rewrite_test(fn, self.config)
..\..\..\dev\tools\Lib\site-packages\_pytest\assertion\rewrite.py:345: in _rewrite_test
    tree = ast.parse(source, filename=strfn)
..\..\..\dev\tools\Lib\ast.py:54: in parse
    return compile(source, filename, mode, flags,
E     File "C:\Users\RobMo\OneDrive\Documents\prediction-vs-reality-logger\tests\test_notifications.py", line 1
E       from pathlib import Pathdef test_notifications():    # Placeholder test for notifications    assert True
E                                   ^^^^^^^^^^^^^^^^^^
E   SyntaxError: invalid syntax
___________________ ERROR collecting tests/test_sources.py ____________________
..\..\..\dev\tools\Lib\site-packages\_pytest\python.py:493: in importtestmodule
    mod = import_path(
..\..\..\dev\tools\Lib\site-packages\_pytest\pathlib.py:582: in import_path
    importlib.import_module(module_name)
..\..\..\dev\tools\Lib\importlib\__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
<frozen importlib._bootstrap>:1387: in _gcd_import
    ???
<frozen importlib._bootstrap>:1360: in _find_and_load
    ???
<frozen importlib._bootstrap>:1331: in _find_and_load_unlocked
    ???
<frozen importlib._bootstrap>:935: in _load_unlocked
    ???
..\..\..\dev\tools\Lib\site-packages\_pytest\assertion\rewrite.py:165: in exec_module
    source_stat, co = _rewrite_test(fn, self.config)
..\..\..\dev\tools\Lib\site-packages\_pytest\assertion\rewrite.py:345: in _rewrite_test
    tree = ast.parse(source, filename=strfn)
..\..\..\dev\tools\Lib\ast.py:54: in parse
    return compile(source, filename, mode, flags,
E     File "C:\Users\RobMo\OneDrive\Documents\prediction-vs-reality-logger\tests\test_sources.py", line 1
E       import sysimport ossys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../')))# Existing importsimport pytestimport jsonfrom datetime import datetimefrom prediction_logger.sources import JSONFileForecastSourcefrom pathlib import Pathdef test_json_file_forecast_source_missing_file():    """Test that a missing forecast file raises FileNotFoundError."""    source = JSONFileForecastSource(folder='tests')    date = datetime(2025, 7, 31)    with pytest.raises(FileNotFoundError):        source.load(date)def test_json_file_forecast_source_invalid_json(monkeypatch):    """Test that an invalid JSON file raises ValueError."""    monkeypatch.setattr('os.getcwd', lambda: os.path.dirname(__file__))  # Mock current directory    project_root = Path(__file__).resolve().parents[1]    forecast_path = project_root / 'forecast' / forecast_filename    try:        with open(forecast_path, 'w') as f:            f.write("{invalid_json}")  # Write invalid JSON        source = JSONFileFo
E                        ^^^^^
E   SyntaxError: invalid syntax
_________________ ERROR collecting tests/test_thinkorswim.py __________________
..\..\..\dev\tools\Lib\site-packages\_pytest\python.py:493: in importtestmodule
    mod = import_path(
..\..\..\dev\tools\Lib\site-packages\_pytest\pathlib.py:582: in import_path
    importlib.import_module(module_name)
..\..\..\dev\tools\Lib\importlib\__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
<frozen importlib._bootstrap>:1387: in _gcd_import
    ???
<frozen importlib._bootstrap>:1360: in _find_and_load
    ???
<frozen importlib._bootstrap>:1331: in _find_and_load_unlocked
    ???
<frozen importlib._bootstrap>:935: in _load_unlocked
    ???
..\..\..\dev\tools\Lib\site-packages\_pytest\assertion\rewrite.py:165: in exec_module
    source_stat, co = _rewrite_test(fn, self.config)
..\..\..\dev\tools\Lib\site-packages\_pytest\assertion\rewrite.py:345: in _rewrite_test
    tree = ast.parse(source, filename=strfn)
..\..\..\dev\tools\Lib\ast.py:54: in parse
    return compile(source, filename, mode, flags,
E     File "C:\Users\RobMo\OneDrive\Documents\prediction-vs-reality-logger\tests\test_thinkorswim.py", line 1
E       from pathlib import Pathdef test_thinkorswim():    # Placeholder test for thinkorswim    assert True
E                                   ^^^^^^^^^^^^^^^^
E   SyntaxError: invalid syntax
___________________ ERROR collecting tests/test_version.py ____________________
..\..\..\dev\tools\Lib\site-packages\_pytest\python.py:493: in importtestmodule
    mod = import_path(
..\..\..\dev\tools\Lib\site-packages\_pytest\pathlib.py:582: in import_path
    importlib.import_module(module_name)
..\..\..\dev\tools\Lib\importlib\__init__.py:88: in import_module
    return _bootstrap._gcd_import(name[level:], package, level)
<frozen importlib._bootstrap>:1387: in _gcd_import
    ???
<frozen importlib._bootstrap>:1360: in _find_and_load
    ???
<frozen importlib._bootstrap>:1331: in _find_and_load_unlocked
    ???
<frozen importlib._bootstrap>:935: in _load_unlocked
    ???
..\..\..\dev\tools\Lib\site-packages\_pytest\assertion\rewrite.py:165: in exec_module
    source_stat, co = _rewrite_test(fn, self.config)
..\..\..\dev\tools\Lib\site-packages\_pytest\assertion\rewrite.py:345: in _rewrite_test
    tree = ast.parse(source, filename=strfn)
..\..\..\dev\tools\Lib\ast.py:54: in parse
    return compile(source, filename, mode, flags,
E     File "C:\Users\RobMo\OneDrive\Documents\prediction-vs-reality-logger\tests\test_version.py", line 1
E       from prediction_logger import versionfrom pathlib import Pathdef test_version():    assert hasattr(version, '__version__')    assert isinstance(version.__version__, str)
E                                                 ^^^^^^^
E   SyntaxError: invalid syntax
=========================== short test summary info ===========================
ERROR tests/test_cli.py
ERROR tests/test_config.py
ERROR tests/test_logger.py - NameError: name 'Path' is not defined
ERROR tests/test_notifications.py
ERROR tests/test_sources.py
ERROR tests/test_thinkorswim.py
ERROR tests/test_version.py
!!!!!!!!!!!!!!!!!!! Interrupted: 7 errors during collection !!!!!!!!!!!!!!!!!!!
============================== 7 errors in 0.61s ==============================

```
