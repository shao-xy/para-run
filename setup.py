from setuptools import setup
from common.configs import VERSION

setup(
    name='para-run',
    version=str(VERSION),
    packages=['common', 'tui'],  # Add your subdirectories here
    scripts=['para-run', 'para-multirow', 'para-simple'],  # Add your executables here
    install_requires=[
        # Add any dependencies your project requires
    ],
)
