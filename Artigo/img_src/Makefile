
DOT_CMD=dot
INKSCAPE=inkscape

OUT_DIR=../output/img

DOT_SRCS= exemploGrafo.dot
DOT_PNG = $(DOT_SRCS:%.dot=$(OUT_DIR)/%.png)

SVG_SRCS= esquemaRegIdxAresta.svg esquemaRegIdxGrafo.svg exemploGrafo.svg \
          exemploHomomorfismo.svg exemploMorfismoCheio.svg \
          exemploMorfismoRegular.svg

SVG_EPS= $(SVG_SRCS:%.svg=$(OUT_DIR)/%.eps)

.PHONY: all

all: $(OUT_DIR) $(SVG_EPS)

$(OUT_DIR)/%.png: %.png
	cp -v $< $@

$(OUT_DIR)/%.png: %.dot
	$(DOT_CMD) -Tpng $< -o$@

$(OUT_DIR)/%.eps: %.svg
	$(INKSCAPE) -z -T --export-eps=$@ $<

$(OUT_DIR):
	mkdir $(OUT_DIR)

clean:
	rm -rf $(OUT_DIR)
