from setuptools import find_packages, setup

setup(
    name="blueflare",
    version="0.0.1",
    packages=find_packages(),
    install_requires=[
        "tornado>=6",
        "geoip2",
        "chardet",
    ],
    package_data={
        "": ["privilege-icons/*.*"],
    }
)
