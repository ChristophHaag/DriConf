# Convenient makefile for managing translations.

POS=de.po
MOS=$(POS:%.po=%/LC_MESSAGES/driconf.mo)

all: po mo

po: $(POS)

mo: $(MOS)

driconf.pot: driconf.py
	pygettext -d driconf driconf.py

%.po: driconf.pot
	if [ -f $@ ]; then \
		mv $@ $@~; \
		msgmerge -o $@ $@~ driconf.pot; \
	else \
		msginit -o $@~ --locale=$*; \
		sed -e 's/charset=.*\\n/charset=UTF-8\\n/' $@~ > $@; \
	fi

%/LC_MESSAGES/driconf.mo: %.po
	mkdir -p $(dir $@)
	msgfmt -o $@ $<
