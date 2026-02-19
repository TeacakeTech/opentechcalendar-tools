import setuptools

setuptools.setup(
    name="opentechcalendartools",
    version="0.4.0",
    description="",
    url="https://github.com/TeacakeTech/opentechcalendar-tools",
    project_urls={
        "Home Page": "https://opentechcalendar.co.uk/",
        "Issues": "https://github.com/TeacakeTech/opentechcalendar-tools/issues",
        "Source": "https://github.com/TeacakeTech/opentechcalendar-tools",
    },
    author="Teacake Tech",
    author_email="hello@teacaketech.scot",
    packages=setuptools.find_packages(exclude=["test"]),
    install_requires=[
        "datatig",
        "requests",
        "requests-cache",
        "icalendar",
        "pyyaml",
        "beautifulsoup4",
    ],
    extras_require={
        "dev": [
            "black",
            "isort",
            "flake8",
            "mypy",
        ],
    },
    python_requires=">=3.12",
)
