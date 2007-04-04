
ifndef VENDOR
VENDOR=None
endif

lang:
	cd po ; msgfmt -o kusuapps.mo en_US.po ; \
	cp kusuapps.mo ../../locale/en/LC_MESSAGES/

mtest:
	echo ${VENDOR}
