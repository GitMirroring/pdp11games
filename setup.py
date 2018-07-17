import setuptools

with open("README.rst", "r") as fh:
    long_description = fh.read()


setuptools.setup(
    name="pdp11games",
    version="1.0",
    author="Peter Cherepanov",
    author_email="mathmoth@mathmoth.org",
    description="Reimplementations of old PDP-11 console games",
    long_description=long_description,
    long_description_content_type="text/x-rst",
    url="https://savannah.nongnu.org/projects/pdp11games",
    packages=["pdp11games"],
    classifiers=(
        "Programming Language :: Python :: 3",
        "Development Status :: 4 - Beta",
        "License :: OSI Approved :: GNU General Public License v3 (GPLv3)",
        "Environment :: Console :: Curses",
        "Operating System :: OS Independent",
        "Intended Audience :: End Users/Desktop",
        "Natural Language :: English",
        "Operating System :: POSIX :: Linux",
        "Operating System :: MacOS :: MacOS X",
        "Topic :: Games/Entertainment",
    ),
    keywords="retro retrocomputing pacman pdp11 game console CLI curses ncurses",
    install_requires=[],
    python_requires='>=3',
#    entry_points={
#        "console_scripts": [
#            "sp21=pdp11games:sp21",
#            "xonix=pdp11games:xonix",
#            "marswar=pdp11games:marswar",
#        ],
    entry_points={
        "console_scripts": [
            "sp21=pdp11games.sp21:main",
            "xonix=pdp11games.xonix:main",
            "marswar=pdp11games.marswar:main",
        ],
    }
)
