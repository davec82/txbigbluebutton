long_description = open('README.txt').read()

from setuptools import setup, find_packages


setup(
    name='txbigbluebutton',
    version='0.5.1',
    author='Davide Colombo',
    maintainer='davec82@gmail.com',
    maintainer_email='davec82@gmail.com',
    description='API for bigbluebutton.',
    long_description=long_description,
    keywords='txbigbluebutton',
    license='MIT',
    packages=find_packages(),
    #install_requires=requires,
)
