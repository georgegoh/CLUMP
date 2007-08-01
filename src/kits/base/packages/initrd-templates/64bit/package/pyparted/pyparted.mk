#############################################################
#
# parted
#
#############################################################

PYPARTED_VERSION=1.8.7

# Don't alter below this line unless you (think) you know
# what you are doing! Danger, Danger!

PYPARTED_SOURCE=pyparted-$(PYPARTED_VERSION).tar.bz2
PYPARTED_CAT:=$(ZCAT)
PYPARTED_SITE=http://people.redhat.com/dcantrel/pyparted
PYPARTED_DIR=$(BUILD_DIR)/${shell basename $(PYPARTED_SOURCE) .tar.bz2}
PYPARTED_WORKDIR=$(BUILD_DIR)/pyparted-$(PYPARTED_VERSION)
BZ_OPTIONS=-jxf

$(DL_DIR)/$(PYPARTED_SOURCE):
	$(WGET) -P $(DL_DIR) $(PYPARTED_SITE)/$(PYPARTED_SOURCE)

$(PYPARTED_DIR)/.unpacked:	$(DL_DIR)/$(PYPARTED_SOURCE)
	tar $(BZ_OPTIONS) $(DL_DIR)/$(PYPARTED_SOURCE) -C $(BUILD_DIR)
	toolchain/patch-kernel.sh $(PYPARTED_DIR) package/pyparted/ pyparted\*.patch
	touch $(PYPARTED_DIR)/.unpacked


$(PYPARTED_WORKDIR)/.configured:	$(PYPARTED_DIR)/.unpacked
	(cd $(PYPARTED_WORKDIR); rm -rf config.cache; \
		$(TARGET_CONFIGURE_OPTS) \
		CFLAGS="$(TARGET_CFLAGS)" \
		LDFLAGS="$(TARGET_LDFLAGS)" ) ; 
	touch $(PYPARTED_WORKDIR)/.configured


$(PYPARTED_WORKDIR)/partedmodule.so:	$(PYPARTED_DIR)/.configured
	$(MAKE) CC=$(TARGET_CC) CFLAGS="$(TARGET_CFLAGS) -I$(STAGING_DIR)/include/python2.4" -C $(PYPARTED_WORKDIR)
	( \
		cd $(PYPARTED_WORKDIR) ; \
		$(STRIP) partedmodule.so ; \
	)


$(PYPARTED_WORKDIR)/.installed: 	$(PYPARTED_WORKDIR)/partedmodule.so
	cp -f $(PYPARTED_WORKDIR)/partedmodule.so $(TARGET_DIR)/usr/lib/python2.4/site-packages/
	$(STRIP) --strip-all $(TARGET_DIR)/usr/lib/python2.4/site-packages/partedmodule.so
	touch $(PYPARTED_WORKDIR)/.installed

pyparted:	uclibc $(PYPARTED_WORKDIR)/.installed

pyparted-source: $(DL_DIR)/$(PYPARTED_SOURCE)

pyparted-clean:
	@if [ -d $(PYPARTED_WORKDIR)/Makefile ] ; then \
		$(MAKE) -C $(PYPARTED_WORKDIR) clean ; \
	fi;

pyparted-dirclean:
	#rm -rf $(PYPARTED_DIR) $(PYPARTED_WORKDIR)
	echo "*************************  Running pyparted-dirclean"

#############################################################
#
# Toplevel Makefile options
#
#############################################################
ifeq ($(strip $(BR2_PACKAGE_PYPARTED)),y)
TARGETS+=pyparted
endif
