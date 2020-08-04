from setuptools import setup, find_packages
import os

requirements = open('requirements.txt', 'r').readlines()

setup(
    name='player',
    version='1.0.0',
    description='Extracts features from txt, xml (TEI), and Word files for dramatic plays.',
    packages=find_packages(exclude=["tests*"]),
    install_requires=requirements,
    # Install all the scripts by default
    scripts=[os.path.join(os.path.dirname(__file__), 'scripts', os.path.basename(script_file)) for script_file in os.listdir('scripts')
             if script_file.endswith('.py') or script_file.endswith('.sh')]
)
