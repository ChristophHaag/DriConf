#!/bin/sh

set -e

PYTHON=python2.1
PREFIX=/usr/local

SOURCES="dri driconf driconf_tb_icons"
for x in $SOURCES; do
    echo -n "Byte compiling $x.py ... "
    rm -f $x.pyo $x.pyc
    echo "import ${x}" | $PYTHON -O
    echo "done."
done

for x in $SOURCES; do
    echo -n "Installing $x.pyo to $PREFIX/lib/$PYTHON ... "
    install -m 644 -o root $x.pyo $PREFIX/lib/$PYTHON
    echo "done."
done
echo -n "Installing driconf to $PREFIX/bin ... "
install -m 755 -o root driconf $PREFIX/bin
echo "done."
