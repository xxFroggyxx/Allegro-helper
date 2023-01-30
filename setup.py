from os import path
from setuptools import setup, find_packages

with open("requirements.txt") as f:
    REQUIRES = f.readlines()


def read(fname):
    return open(path.join(path.dirname(__file__), fname)).read()


setup(
    name="Allegro Sale Helper",
    version="1.0.0",
    author="Wojciech Klimczewski",
    description="Helps with sales management on Allegro",
    long_description=read("../docs/en/README.md"),
    packages=find_packages(),
    install_requires=REQUIRES,
)
