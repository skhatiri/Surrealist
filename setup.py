import setuptools

with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

setuptools.setup(
    name="flight2sim",
    version="0.0.1",
    author="Sajad Khatiri",
    author_email="s.khatiri@gmail.com",
    description="Flight2Sim",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/skhatiri/Flight2Sim",
    project_urls={"Bug Tracker": "https://github.com/skhatiri/Flgith2Sim/issues"},
    license="GNU GPLv3",
    packages=setuptools.find_packages(),
    include_package_data=True,
    install_requires=[
        "git+git+https://github.com/skhatiri/Aerialist.git@packaging"
    ],
    entry_points={"console_scripts": ["flight2sim=flight2sim"]},
)
