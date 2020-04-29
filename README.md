# ANNO 1800 Asset viewer

This program displays .cfg and rdm files from the game Anno 1800. The goal is to provide a visual feedback for modders while editing theses files (check props position/orientation for example).

## Disclaimer:
This program is a WIP. Some files are displayed with bugs, or not parsed at all.

## How to use:
### Installation
At the moment you need a python distribution (at least python 3.7). 
You can download vanilla python here:
https://www.python.org/

Anaconda is also great if you want to do science related stuff in future project:
https://www.anaconda.com/

You will also need to resolve some depenencies by downloading following packages (most recent versions):

- wxPython
- pyOpengl
- pillow
- lxml
- numpy

You also need the package for the rdm parser:
https://github.com/VonZeeple/Anno-RDM-Converter

Then using cmd, go to the folder containing main.py and run: python main.py
### Loading files
- For .rdm files, simply select a rdm file using the tree on the left.
- For .cfg files, you have to extract data (.prp, .cfg, .rdm, textes ect...), used in your .cfg from the game (contained in rda archives).
You can use Kskudlik's rda extractor: https://github.com/kskudlik/Anno-1800-RDA-Extractor.
Specify the folder where you extracted the data using file->select data folder.
Then, open your.cfg using the tree on the left.