#! /usr/bin/bash
wget https://pages.cs.wisc.edu/~harter/cs544/data/hdma-wi-2021.zip
# get file, install unzip(if not isntalled), unzip, read file
unzip hdma-wi-2021.zip
# assume unzip is installed (do it in dockerfile)
cat hdma-wi-2021.csv | grep "Multifamily" | wc -l
