# Convenient makefile for managing translations.

# Prerequisites:

# - pygettext from the python distribution
# - GNU gettext

# How to use this:

# To start working on a new translation edit the POS=... line
# below. If you want to add for example a french translation, add
# fr.po.

# Then run "make po" to generate fresh .po files from translatable
# strings in driconf.py. Now you can edit the new .po file (fr.po in
# the example above) to translate the strings. Please make sure that
# your editor encodes the file in UTF-8.

# Finally run "make mo" to generate a new binary file for gettext. It
# will be stored in <lang>/LC_MESSAGES/driconf.mo. You can test the
# new translation by running ./driconf in the current directory
# without reinstalling DRIconf all the time. Of course you need to
# have the correct locale setting in order to see your translation.

# To get your new translation into the next release of DRIconf please
# send me your <lang>.po file.

# More information:

# - info gettext
# - documentation of the gettext python package

# The set of supported languages. Add languages as needed.
POS=de.po es.po

# Automatically generated list of mo files.
MOS=$(POS:%.po=%/LC_MESSAGES/driconf.mo)

.PHONY: mo po

# Default target. Use this to update your .mo files from the .po files.
mo:
	@for mo in $(MOS); do \
		lang=$${mo%%/*}; \
		echo "Updating $$mo from $$lang.po."; \
		mkdir -p $${mo%/*}; \
		msgfmt -o $$mo $$lang.po; \
	done

# Use this target to create or update .po files with new messages in
# driconf.py.
po: $(POS)

# Extract message catalog from driconf.py.
driconf.pot: driconf.py
	xgettext -L python -o driconf.pot driconf.py

# Create or update a .po file for a specific language.
%.po: driconf.pot
	if [ -f $@ ]; then \
		mv $@ $@~; \
		msgmerge -o $@ $@~ driconf.pot; \
	else \
		msginit -o $@~ --locale=$*; \
		sed -e 's/charset=.*\\n/charset=UTF-8\\n/' $@~ > $@; \
	fi
