
RST2ODT=rst2odt.py
RST2HTML=rst2html.py
RST2LATEX=rst2latex.py

STYLES_DIR=styles
STYLE_ODT=$(STYLES_DIR)/puc_artigo.odt

OUT_DIR=output

SAIDAS= artigo.html

OUTS = $(SAIDAS:%=$(OUT_DIR)/%)

.PHONY: all

all: $(OUT_DIR)/img $(OUTS)

$(OUT_DIR)/artigo.odt: artigo.rst bibliografia.rst

$(OUT_DIR)/artigo.html: artigo.rst bibliografia.rst

$(OUT_DIR)/artigo.tex: artigo.rst bibliografia.rst

$(OUT_DIR)/%.odt: %.rst $(STYLE_ODT)
	$(RST2ODT) --stylesheet=$(STYLE_ODT) $< $@

$(OUT_DIR)/%.html: %.rst
	$(RST2HTML) $< $@

$(OUT_DIR)/%.tex: %.rst
	$(RST2LATEX) $< $@

$(OUT_DIR)/img:
	ln -s ${PWD}/img $(OUT_DIR)/img

clean:
	rm -vf $(OUTS)
