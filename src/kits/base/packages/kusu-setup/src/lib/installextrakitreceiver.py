import os
import sys
from path import path
from primitive.support import osfamily
from primitive.support.util import pollCommand

KITOPS_ADD_COMMAND = 'kusu-kitops -am '

class InstallExtraKitReceiver:
    """
    This class prompts for, and installs additional kits
    """
    def __init__(self):
        pass

    def verify_if_file_exists(self, file_path):
        file_path = path(file_path)
        if file_path.exists():
            return True
        return False

    def prompt_for_kit(self):
        kit_iso = raw_input("Please provide path to kit location : ")
        return kit_iso

    def prompt_for_additional_kit(self):
        while True:
            user_input = raw_input("Add extra kit? [y/n] ")
            if not user_input.lower() in ['y', 'yes']:
                break
            
            kit_iso = self.prompt_user_for_kit_location()
            self.install_extra_kit(kit_iso)      

    def prompt_user_for_kit_location(self):
        while True:
            kit_iso = self.prompt_for_kit()
            if kit_iso and \
               self.verify_if_file_exists(kit_iso):
                return kit_iso

    def install_extra_kit(self, kit_iso):
        if kit_iso:
            cmd = KITOPS_ADD_COMMAND + ' %s' % kit_iso
            out, err = pollCommand(cmd)
            if err:
                print err[0]
        else:
            print "Kit installation is unsuccessful."
