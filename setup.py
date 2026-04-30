from setuptools import setup, find_packages

setup(
    name="mailsense",
    version="0.1",
    packages=find_packages(),
)
#in order to prevent changing the directory of each file from each folder which are stored in different folders, we use setuptools to manage the package.