from setuptools import setup, find_packages


# ---------------------------------------------------------------------------------------------------------
# BASE CONFIGURATION
# ---------------------------------------------------------------------------------------------------------

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()
    
BASE_PACKAGE = 'gethighs'

base_kwargs = dict(
    name = 'gethighs',
    packages = [BASE_PACKAGE] + [f"{BASE_PACKAGE}." + e for e in find_packages(where=BASE_PACKAGE)],
    version = '0.0.1',
    license='Apache License 2.0',
    description = 'A Python interface to use HiGHS executable files with Pyomo',
    long_description=long_description,
    long_description_content_type="text/markdown",
    author = 'Bruno Scalia C. F. Leite',
    author_email = 'bruscalia12@gmail.com',
    url = 'https://github.com/bruscalia/gethighs',
    download_url = 'https://github.com/bruscalia/gethighs',
    keywords = [
            'Optimization',
            'Optimisation',
            'Modeling',
            'Modelling',
            'Operations Research'
            'Linear programming',
            'Integer programming',
            'Mixed-integer programming'
        ],
    install_requires=[
            'numpy>=1.19.*',
            'pyomo==6.*',
        ],
)


setup(**base_kwargs)
