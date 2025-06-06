# leat
The Lightweight Ethical Auditing Tool (LEAT) identifies ethical concepts in documents.

## Features
- Excel interface for defining Concepts of interest and the terms and text patterns that define them
- Searches documents for matching text and identifies the documents and location in the documents they occur
- Light-weight installation on remote machines
- Extended functionality for analyzing search results

## Installation

### Normal installation

1. Create a virtual environment
1. Pip install package -- `pip install git+https://github.com/markgraves/leat.git`

### Minimal installation on remote machines

- Either `git clone https://github.com/markgraves/leat.git` or download and unzip `https://github.com/markgraves/leat/archive/refs/heads/main.zip`
- Basic search functionality for plain text files uses only standard python library
- If searching additional file types, create a virtual environment if desired, and `pip install -r requirements.basic.txt`
- Saved results file can be copied to another machine and analyzed as desired (without copying document text from searched files)

### Full development version

1. Create a virtural environment
1. Pip install dev package -- `pip install "leat[dev] @ git+https://github.com/markgraves/leat.git"`

Or, if installing from source -- `pip install -r requirements.txt -r requirements.dev.txt`

## Getting Started
- See examples in [leat/examples](leat/examples)
- For command line tool, run `./leat.py --help` or `python leat.py --help`
