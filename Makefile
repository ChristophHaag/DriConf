PYTHON=python2.1
PREFIX=/usr/local

SOURCES=dri.py driconf_xpm.py driconf.py
DOCS=COPYING README CHANGELOG TODO
DRICONF=driconf

BYTECODE=$(patsubst %.py,%.pyc,$(SOURCES))

VERSION=0.0.3
DIRNAME=driconf-$(VERSION)
ARCHIVE=driconf-$(VERSION).tar.gz

.PHONY: all clean dist-clean archive install

all:

clean:
	rm -rf *.pyc *.pyo

distclean: clean
	rm -rf $(ARCHIVE) *~

archive: $(ARCHIVE)

install: $(BYTECODE) $(DRICONF)
	@for x in $(BYTECODE); do \
	    echo -n "Installing $$x to $(PREFIX)/lib/$(PYTHON)/site-packages ... "; \
	    install -m 644 $$x $(PREFIX)/lib/$(PYTHON)/site-packages; \
	    echo "done."; \
	done; \
	echo -n "Installing $(DRICONF) to $(PREFIX)/bin ... "; \
	install -m 755 $(DRICONF) $(PREFIX)/bin; \
	echo "done."

$(ARCHIVE): $(DOCS) $(SOURCES) $(DRICONF) Makefile
	@echo -n "Building $(ARCHIVE) ... "
	@rm -rf /tmp/$(DIRNAME)
	@mkdir /tmp/$(DIRNAME)
	@cp $^ /tmp/$(DIRNAME)
	@tar -C /tmp -cf - $(DIRNAME) | gzip -9 > $@
	@rm -rf /tmp/$(DIRNAME)
	@echo "done"

%.pyc: %.py
	@echo -n "Byte compiling $< ... "
	@rm -f $@ $*.pyo
	@echo "import $*" | $(PYTHON)
	@echo "done."
