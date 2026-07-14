from setuptools import setup, find_packages

setup(
    name="sphinx-kataglyphis-theme",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        "sphinx_kataglyphis": ["_static/css/*.css"],
    },
)
