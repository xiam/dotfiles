all:
	for i in $$(find . -mindepth 1 -maxdepth 1 -name ".*" -printf "%P\n" | grep -v \.git/); do \
		ln -sfn $$PWD/$$i ~/$$i; \
	done
