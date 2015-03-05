
RST2ODT=rst2odt.py

STYLES_DIR=styles
STYLE_ODT=$(STYLES_DIR)/puc_artigo.odt

OUT_DIR=output

.PHONY: all

all: $(OUT_DIR)/artigo.odt

$(OUT_DIR)/teste.odt: teste.rst $(STYLE_ODT)
	$(RST2ODT) --stylesheet=$(STYLE_ODT) $< $@

$(OUT_DIR)/artigo.odt: artigo.rst $(STYLE_ODT) bibliografia.rst
	$(RST2ODT) --stylesheet=$(STYLE_ODT) $< $@

