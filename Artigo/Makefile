
RST2ODT=rst2odt.py
RST2HTML=rst2html.py
RST2LATEX=rst2latex.py

STYLES_DIR=styles
STYLE_ODT=$(STYLES_DIR)/puc_artigo.odt

IMG_SRC_DIR=img_src
OUT_DIR=output

SAIDAS= Artigo.pdf

OUTS = $(SAIDAS:%=$(OUT_DIR)/%)

.PHONY: all imgs

all: imgs $(OUTS)

$(OUT_DIR)/artigo.odt: artigo.rst bibliografia.rst

$(OUT_DIR)/artigo.html: artigo.rst bibliografia.rst

$(OUT_DIR)/artigo.tex: artigo.rst bibliografia.rst

imgs:
	$(MAKE) -C $(IMG_SRC_DIR)

$(OUT_DIR)/%.odt: %.rst $(STYLE_ODT)
	$(RST2ODT) --stylesheet=$(STYLE_ODT) $< $@

$(OUT_DIR)/%.html: %.rst
	$(RST2HTML) $< $@

$(OUT_DIR)/%.tex: %.rst
	$(RST2LATEX) $< $@

$(OUT_DIR)/%.pdf: %.odt
	libreoffice --invisible --convert-to pdf:writer_pdf_Export --outdir $(OUT_DIR) $<

clean:
	$(MAKE) -C $(IMG_SRC_DIR) clean
	rm -vf $(OUTS)
