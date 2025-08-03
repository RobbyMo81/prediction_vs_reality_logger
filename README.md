
# Prediction vs Reality Logger

## Overview
This project provides a robust, production-ready framework for logging, evaluating, and analyzing predictions versus actual outcomes in financial or forecasting scenarios. It features modular ingestion, analytics (tensor/LLM), notifications, automation, and CI/CD support.

## Features
- Modular forecast ingestion and schema validation
- Actuals fetching (pluggable sources)
- Scenario evaluation and results persistence
- Tensor analytics (PyTorch) and LLM (OpenAI) integration
- Configurable notifications (Slack, webhook, email)
- CLI interface with flexible options
- Automation: Docker, Kubernetes, GitHub Actions
- Comprehensive testing and code coverage

## Getting Started

### 1. Clone the Repository
```sh
git clone <repo-url>
cd prediction-vs-reality-logger
```

### 2. Install Dependencies
```sh
pip install -r requirements.txt
```

### 3. Install in Editable Mode (Recommended for Development)
```sh
pip install -e .
```

### 4. Configuration
- Place your configuration in `config.yaml` or use environment variables.
- See `config/` for schema and examples.

## Usage

### CLI
Run the logger via CLI:
```sh
python -m prediction_logger.cli --help
```
Key options:
- `--date`: Specify forecast date
- `--dry-run`: Preview without writing outputs
- `--tensor`: Enable tensor model integration
- `--actuals`: Choose actuals source

### Running Tests
```sh
pytest
pytest --cov=prediction_logger --cov-report=term-missing
```

## Testing & Quality
- See `TESTING_PHASE_CHECKLIST.md` for a full testing and handoff process
- Aim for 90%+ code coverage
- Add/verify tests for all modules (tensor, translator, notifications, CLI)

## Documentation & Dashboard
- Update and consult the Implementation Plan (`Implementation_Plan.md`)
- Add code comments and docstrings as you contribute
- Dashboard: See `dashboard/` (Jupyter notebook stub for results exploration)

## Contribution Guidelines
- Follow the phased checklist in `TESTING_PHASE_CHECKLIST.md`
- Document all issues and test failures clearly
- Use feature branches and submit PRs for review

## Roadmap & Enhancements
- See Implementation Plan for current and future tasks
- Planned: expanded notification support, advanced analytics, multi-symbol/scaling, and more

---
Contributions and suggestions are welcome!
