
DOT_CMD=dot

OUT_DIR=../output/img

DOT_SRCS= exemploGrafo.dot

DOT_PNG = $(DOT_SRCS:%.dot=$(OUT_DIR)/%.png)

.PHONY: all

all: $(OUT_DIR) $(DOT_PNG)

$(OUT_DIR)/%.png: %.png
	cp -v $< $@

$(OUT_DIR)/%.png: %.dot
	$(DOT_CMD) -Tpng $< -o$@

$(OUT_DIR):
	mkdir $(OUT_DIR)

clean:
	rm -rf $(OUT_DIR)
