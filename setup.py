from setuptools import setup, find_packages

setup(
    name="logit",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "markdown>=3.3.0",
        "pandas>=1.3.0",
    ],
    entry_points={
        'console_scripts': [
            'logit=src.logit:main',
        ],
    },
    package_data={
        'logit': ['configs/*.json', 'js/*.js'],
    },
) 