#############################################################
#
# parted
#
#############################################################

PARTED_VERSION=1.8.7
PARTED_LIBVER1=1.8.so.7
PARTED_LIBVER2=1.8.so.7.0.0

# Don't alter below this line unless you (think) you know
# what you are doing! Danger, Danger!

PARTED_SOURCE=parted-$(PARTED_VERSION).tar.gz
PARTED_CAT:=$(ZCAT)
PARTED_SITE=http://ftp.gnu.org/gnu/parted
PARTED_DIR=$(BUILD_DIR)/${shell basename $(PARTED_SOURCE) .tar.gz}
PARTED_WORKDIR=$(BUILD_DIR)/parted-$(PARTED_VERSION)
EXTRACT_OPTIONS="-zxf"

$(DL_DIR)/$(PARTED_SOURCE):
	$(WGET) -P $(DL_DIR) $(PARTED_SITE)/$(PARTED_SOURCE)

$(PARTED_DIR)/.unpacked:	$(DL_DIR)/$(PARTED_SOURCE)
	tar $(EXTRACT_OPTIONS) $(DL_DIR)/$(PARTED_SOURCE) -C $(BUILD_DIR)
	toolchain/patch-kernel.sh $(PARTED_DIR) package/parted/ parted\*.patch
	touch $(PARTED_DIR)/.unpacked


$(PARTED_WORKDIR)/.configured:	$(PARTED_DIR)/.unpacked
	(cd $(PARTED_WORKDIR)/libparted/ ; \
		sed -i -e 's/SUBDIRS_CHECK = tests/SUBDIRS_CHECK =/g' $(PARTED_WORKDIR)/libparted/Makefile.in ) ;
	(cd $(PARTED_WORKDIR); rm -rf config.cache; \
		$(TARGET_CONFIGURE_OPTS) \
		CFLAGS="$(TARGET_CFLAGS)" \
		LDFLAGS="$(TARGET_LDFLAGS)" \
		./configure \
		--target=$(GNU_TARGET_NAME) \
                --host=$(GNU_TARGET_NAME) \
                --build=$(GNU_HOST_NAME) \
		--without-readline ) ;
	touch $(PARTED_WORKDIR)/.configured


$(PARTED_WORKDIR)/parted/parted:	$(PARTED_DIR)/.configured
	cp $(PARTED_WORKDIR)/../../package/parted/linux.c $(PARTED_WORKDIR)/libparted/arch/
	$(MAKE) CC=$(TARGET_CC) CFLAGS="$(TARGET_CFLAGS)" -C $(PARTED_WORKDIR)

$(PARTED_WORKDIR)/.installed: 	$(PARTED_WORKDIR)/parted/parted
	mkdir -p $(TARGET_DIR)/usr/bin
	mkdir -p $(STAGING_DIR)/include/parted
	cp -v $(PARTED_WORKDIR)/include/parted/*.h $(STAGING_DIR)/include/parted
	cp -f $(PARTED_WORKDIR)/libparted/.libs/libparted*so* $(STAGING_DIR)/lib
	cp -f $(PARTED_WORKDIR)/parted/.libs/parted $(TARGET_DIR)/usr/bin
	cp -f $(PARTED_WORKDIR)/partprobe/.libs/partprobe $(TARGET_DIR)/usr/bin
	cp -f $(PARTED_WORKDIR)/libparted/.libs/libparted.so $(TARGET_DIR)/lib
	(cd $(TARGET_DIR)/lib ;ln -s libparted.so libparted-$(PARTED_LIBVER1))
	(cd $(TARGET_DIR)/lib ;ln -s libparted.so libparted-$(PARTED_LIBVER2))
	$(STRIP) --strip-all $(TARGET_DIR)/usr/bin/parted
	$(STRIP) --strip-all $(TARGET_DIR)/usr/bin/partprobe
	touch $(PARTED_WORKDIR)/.installed

parted:	uclibc $(PARTED_WORKDIR)/.installed

parted-source: $(DL_DIR)/$(PARTED_SOURCE)

parted-clean:
	@if [ -d $(PARTED_WORKDIR)/Makefile ] ; then \
		$(MAKE) -C $(PARTED_WORKDIR) clean ; \
	fi;

parted-dirclean:
	#rm -rf $(PARTED_DIR) $(PARTED_WORKDIR)
	echo "*************************  Running parted-dirclean"

#############################################################
#
# Toplevel Makefile options
#
#############################################################
ifeq ($(strip $(BR2_PACKAGE_PARTED)),y)
TARGETS+=parted
endif
