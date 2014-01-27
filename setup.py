
from setuptools import setup

setup(
    name = "javasphinx",
    packages = ["javasphinx"],
    version = "0.9.10",
    author = "Chris Thunes",
    author_email = "cthunes@brewtab.com",
    url = "http://github.com/bronto/javasphinx",
    description = "Sphinx extension for documenting Java projects",
    classifiers = [
        "Programming Language :: Python",
        "Development Status :: 4 - Beta",
        "Operating System :: OS Independent",
        "License :: OSI Approved :: MIT License",
        "Intended Audience :: Developers",
        "Topic :: Software Development :: Libraries"
        ],
    install_requires=["javalang>=0.9.5", "lxml", "beautifulsoup4"],
    entry_points={
        'console_scripts': [
            'javasphinx-apidoc = javasphinx.apidoc:main'
            ]
        },
    long_description = """\
==========
javasphinx
==========

javasphinx is an extension to the Sphinx documentation system which adds support
for documenting Java projects. It includes a Java domain for writing
documentation manually and a javasphinx-apidoc utility which will automatically
generate API documentation from existing Javadoc markup.
"""
)
