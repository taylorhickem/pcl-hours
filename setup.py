from setuptools import setup, find_packages

setup(
    name='pcl-hours',
    version='1.0',
    packages=find_packages(),
    url='https://github.com/taylorhickem/pcl-hours.git',
    description='use sqlgsheet to create and update blockytime events and post to gsheet report',
    author='@taylorhickem',
    long_description=open('README.md').read(),
    install_requires=open("requirements.txt", "r").read().splitlines(),
    include_package_data=True
)