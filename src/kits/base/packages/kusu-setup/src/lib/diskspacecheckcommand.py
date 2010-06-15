
from command import Command

class DiskSpaceCheckCommand(Command):
    """
    This is the command class for checking requisite amount of diskspace in the system
    """
    def __init__(self, receiver):
        self._receiver = receiver

    def show_partition_list(self, partitions):
        print "\nSelect one of the following mountpoints where kusu should place it's '/depot' folder:"
        count = 1
        for (mountpoint, size) in partitions:
            print "\t %d) \t MountPoint: '%s' FreeSpace: '%sB' " %(count, mountpoint, size)
            count += 1
 
    def execute(self):
        partitions = self._receiver.freeDiskSpace

        if len(partitions) == 1 and partitions[0][0] == '/depot':
            print "\nKusu Setup has found valid '/depot' mountpoint to place it's '/depot' folder."
            self._proceedStatus = True 
            self.depot_partition = partitions[0]
            return
 
        self.show_partition_list(partitions)
        while True:
            try:
                value = int(raw_input("Type the number corresponding to your preferred partition: ")) - 1
                if value in range(0, len(partitions)):
                    self._receiver.prepareDepotFolder(partitions[value])
                    self._proceedStatus = True
                    self.depot_partition = partitions[value]
                    break
                else:
                    value = None
                    self.show_partition_list(partitions)
                    print "Invalid selection. Please select a number that corresponds to a mountpoint in the given list."

            except ValueError:
                #in case non-integer selections or alphabetic chars are entered
                self.show_partition_list(partitions)
                print "Invalid selection. Please select a number that corresponds to a mountpoint in the given list."


