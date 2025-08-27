from setuptools import setup, find_packages

setup(
    name="mupac",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "aiofiles",
        "aiohttp", 
        "beautifulsoup4",
        "pydantic"
    ],
    entry_points={
        "console_scripts": [
            "mupac = mupac.__main__:main"
        ]
    }
)