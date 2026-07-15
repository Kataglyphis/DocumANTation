from setuptools import find_packages, setup

setup(
    name="sphinx-kataglyphis-theme",
    version="0.1.0",
    packages=find_packages(),
    include_package_data=True,
    package_data={
        # brand.tokens.json is generated from style/brand.json; shipping it
        # lets any installing project read the brand instead of copying values.
        "sphinx_kataglyphis": ["_static/css/*.css", "brand.tokens.json"],
    },
)
