#!/bin/bash
CURDIR=$(pwd)
PATH=$CURDIR/.venv/bin:$PATH

source .venv/bin/activate
pyinstaller --noconfirm --log-level WARN Logarithmic.spec
dist/Logarithmic
