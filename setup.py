from setuptools import setup, find_packages

setup(name="webdriver",
    version="0",
    packages=find_packages(),
    description="It's a scrapers server",
    author="HAL9000",
    entry_points={'console_scripts':['webdriver = webdriver:run']}
    )