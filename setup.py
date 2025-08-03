from setuptools import setup, find_packages

setup(
    name="prediction_vs_reality_logger",
    version="0.1.0",
    packages=["prediction_vs_reality_logger"],
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
            'prediction-logger=prediction_vs_reality_logger.cli:main',
        ],
    },
)
