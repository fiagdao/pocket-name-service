import os
from setuptools import setup, find_packages

_dir = os.path.abspath(os.path.dirname(__file__))
_readme_path = os.path.join(_dir, "README.md")

with open(_readme_path, "r") as rm:
    README = rm.read()

setup(
    name="pns",
    version="0.01",
    description="Python Client for PNS for Pocket Network.",
    author="Pierre",
    author_email="pierre@thunderstake.io",
    license="MIT",
    packages=["pns"],
    entry_points={
        "console_scripts": ["pns=pns.main:main"],
    },
)
