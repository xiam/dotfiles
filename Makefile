install: submodules
	@ \
	for FILE in $$(find config -mindepth 1 -maxdepth 1); do \
		export BASENAME=$$(basename $$FILE); \
		ln -sfn $$PWD/$$FILE $$HOME/$$BASENAME; \
	done

submodules:
	git submodule init && \
	git submodule update
