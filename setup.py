from setuptools import setup, find_packages

from glob import glob

setup(
    name="prediction_vs_reality_logger",
    version="0.1.0",
    packages=["prediction_vs_reality_logger", "prediction_logger"],
    install_requires=[
        "click",
        "PyYAML",
        "pandas",
        "python-dateutil",
        "requests",
        "websockets",
    ],
    entry_points={
        'console_scripts': [
            'prediction-logger=prediction_logger.cli:main',
        ],
    },
    include_package_data=True,
    package_data={
        '': ['config/*.yaml', '*.yaml'],
    },
)
