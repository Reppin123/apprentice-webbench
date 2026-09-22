#!/bin/zsh
cd -- "${0:A:h}"
python3 bench.py pilot
printf '\nPress Enter to close.\n'
read
