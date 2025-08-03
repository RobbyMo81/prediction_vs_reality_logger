import click
import logging
from dateutil.parser import parse
from .logger import run
from pathlib import Path

def setup_logging(verbose):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format='[%(levelname)s] %(message)s')

@click.command(context_settings=dict(help_option_names=['-h', '--help']))
@click.option('--date', help='Date for forecast (YYYY-MM-DD)', default=None)
@click.option('--dry-run', is_flag=True, help='Preview without writing outputs')
@click.option('--verbose', is_flag=True, help='Enable verbose logging')
@click.option('--tensor', is_flag=True, help='Enable tensor model integration')
@click.option('--actuals', type=click.Choice(['stub', 'file'], case_sensitive=False), default='stub', help='Actuals source type')
def main(date, dry_run, verbose, tensor, actuals):
    """
    CLI for Prediction vs Reality Logger.
    Use --help to see all options.
    """
    setup_logging(verbose)
    try:
        logging.debug(f"CLI invoked for date={date}, dry_run={dry_run}, tensor={tensor}, actuals={actuals}")
        if dry_run:
            logging.info("DRY RUN: exiting without changes")
            return
        # Import tensor model and actuals source factory if needed
        tensor_model = None
        if tensor:
            from .tensor_model import TensorModel
            tensor_model = TensorModel('model.pt')  # Path can be made configurable
            tensor_model.load()
        from .sources import get_actuals_source_from_config
        from .config import load_config
        cfg = load_config()
        # Override actuals source type if specified
        if actuals:
            cfg['actuals_source'] = actuals
        actuals_source = get_actuals_source_from_config(cfg)
        run(parse(date) if date else None, actuals_source=actuals_source, tensor_model=tensor_model)
    except Exception as e:
        logging.critical(f"Unhandled error: {e}")
        from .notifications import notify
        notify(f"Critical failure in CLI: {e}")
        raise

if __name__ == '__main__':
    main()