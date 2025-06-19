
from setuptools import setup, find_packages

setup(
    name="lego_hub_controller",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        'bleak>=0.21.1',  # For BLE communication
        'asyncio>=3.4.3',  # For async/await support
    ],
    author="LEGO Hub Controller Team",
    description="A Python library for controlling LEGO Technic Smart Hub",
    long_description=open('README.md').read(),
    long_description_content_type="text/markdown",
    keywords="lego, bluetooth, control, hub, technic",
    python_requires='>=3.7',
)
