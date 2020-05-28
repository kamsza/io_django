#!/bin/sh

# run this script as root, once, at installation

# more will go here (e.g. initialization of postgres database)

# part of the program running inside network namespace
# will run under this user
useradd --system 0tdns
