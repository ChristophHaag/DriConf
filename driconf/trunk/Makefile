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

# Finally run "make" to generate a new binary file for gettext. It
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
POS=de.po es.po it.po ru.po

#
# Don't change anything below, unless you know what you're doing.
#
PYS=driconf.py driconf_commonui.py driconf_complexui.py driconf_simpleui.py
LANGS=$(POS:%.po=%)
MOS=$(POS:%.po=%/LC_MESSAGES/driconf.mo)
POT=driconf.pot

.PHONY: all pot po mo

# Default target. Use this to update your .mo files from the .po files.
all: mo

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

pot: $(POT)

# Extract message catalog from driconf.py.
$(POT): $(PYS)
	xgettext -L python --from-code utf-8 -o $(POT) $(PYS)

# Create or update a .po file for a specific language.
%.po: $(POT)
	@if [ -f $@ ]; then \
		echo "Merging new strings from $(POT) into $@."; \
		mv $@ $@~; \
		msgmerge -o $@ $@~ $(POT); \
	else \
		echo "Initializing $@ from $(POT)."; \
		msginit -i $(POT) -o $@~ --locale=$*; \
		sed -e 's/charset=.*\\n/charset=UTF-8\\n/' $@~ > $@; \
	fi
