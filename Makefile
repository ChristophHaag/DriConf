# Convenient makefile for managing translations.

# The set of supported languages. Add languages as needed.
POS=de.po

# Automatically generated list of mo files.
MOS=$(POS:%.po=%/LC_MESSAGES/driconf.mo)

.PHONY: mo po

# Default target. Use this to update your .mo files from the .po files.
mo:
	@for mo in $(MOS); do \
		lang=$${mo%%/*}; \
		echo "Updating $$mo from $$lang.po."; \
		mkdir -p $(dir $$mo); \
		msgfmt -o $$mo $$lang.po; \
	done

# Use this target to create or update .po files with new messages in
# driconf.py.
po: $(POS)

# Extract message catalog from driconf.py.
driconf.pot: driconf.py
	pygettext -d driconf driconf.py

# Create or update a .po file for a specific language.
%.po: driconf.pot
	if [ -f $@ ]; then \
		mv $@ $@~; \
		msgmerge -o $@ $@~ driconf.pot; \
	else \
		msginit -o $@~ --locale=$*; \
		sed -e 's/charset=.*\\n/charset=UTF-8\\n/' $@~ > $@; \
	fi
