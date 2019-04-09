import setuptools

with open("README.md", "r") as fh:
    long_description = fh.read()

setuptools.setup(
    name="cloudformation-repos",
    version="0.0.1",
    author="Eamonn Faherty",
    author_email="python-packages@designandsolve.co.uk",
    description="Making it easier to find CloudFormation templates",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/eamonnfaherty/cloudformation-repos",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    entry_points={
        'console_scripts': [
            'cloudformation-repos = cloudformation_repos.cli:cli'
        ]},
    install_requires=[
        'pyyaml',
        'click',
        'requests',
    ],
)
