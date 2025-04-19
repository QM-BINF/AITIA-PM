# AITIA-PM

## Introduction
This repository contains the source code for the AITIA-PM algorithm. For reference, see the papers entitled:

- [Root Cause Analysis in Process Mining with Probabilistic Temporal Logic](https://doi.org/10.1007/978-3-030-98581-3_6)
- [AITIA-PM: Discovering the true causes of events in a process mining context](https://doi.org/10.1016/j.engappai.2023.107145)

## Cloning the Repository

To start working with this repository, it is advised to clone it to your machine:

    git clone https://github.com/QM-BINF/Unsupervised-Event-Log-Abstraction-Framework.git

Once the repository is cloned, you can navigate the project's contents. Make sure you have the necessary software:

- Python 3.x with packages `pandas`, `numpy`, `tqdm`, `pm4py`
- R & Rstudio

## Contents of the Repository
* `\Data` - Contains the modified CSV file to contain case delays as observations.
* `\R` - Contains the source R file to compute the false discovery rates.
* `\Output` - Contains the output files from AITIA-PM.
* `main.py` - The Python source code to apply AITIA-PM on a dataset.
* `Hypothesizer.py` - The Python class built to define the search space.
* `Inference.py` - The Python class to identify cause-effect relations.

## Using the Repository Source Code

