#!/bin/sh

set -e

PYTHON=python2.1
PREFIX=/usr/local

SOURCES="dri driconf driconf_tb_icons"
for x in $SOURCES; do
    echo -n "Byte compiling $x.py ... "
    rm -f $x.pyo $x.pyc
    echo "import ${x}" | $PYTHON
    echo "done."
done

mkdir -p $PREFIX/lib/$PYTHON/site-packages
for x in $SOURCES; do
    echo -n "Installing $x.pyc to $PREFIX/lib/$PYTHON/site-packages ... "
    install -m 644 -o root $x.pyc $PREFIX/lib/$PYTHON/site-packages
    echo "done."
done
echo -n "Installing driconf to $PREFIX/bin ... "
install -m 755 -o root driconf $PREFIX/bin
echo "done."
