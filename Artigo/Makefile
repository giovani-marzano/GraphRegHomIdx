
RST2ODT=rst2odt.py

STYLES_DIR=styles
STYLE_ODT=$(STYLES_DIR)/puc_artigo.odt

.PHONY: all

all: artigo.odt

teste.odt: teste.rst $(STYLE_ODT)
	$(RST2ODT) --stylesheet=$(STYLE_ODT) $< $@

artigo.odt: artigo.rst $(STYLE_ODT) bibliografia.rst
	$(RST2ODT) --stylesheet=$(STYLE_ODT) $< $@

