import math

def partition_sector_comparator(p1, p2):
    if p1.start_sector>p2.start_sector:
        return 1
    elif p1.start_sector==p2.start_sector:
        return 0
    else: # p1.start_sector<p2.start_sector
        return -1


def free_space_comparator(t1, t2):
    s1 = int(t1[1]) - int(t1[0])
    s2 = int(t2[1]) - int(t2[0])
    return s1-s2


def getAlignedSectors(start_sector, end_sector, sectors_per_cylinder):
    """
    This function returns the given start_sector and end_sector after
    aligning them to cylinder boundaries calculated using the 
    sectors_per_cylinder parameter.
    """
    # if start sector is not the first sector of the cylinder, then
    # calculate size starting from start of next cylinder.
    cyl_bounds = getCylinderBoundariesForSector(start_sector,
                                         sectors_per_cylinder)
    if start_sector != cyl_bounds[0]:
        start_sector = cyl_bounds[1] + 1

    # if end sector is not the last sector of the cylinder, then
    # calculate size ending with the previous cylinder.
    cyl_bounds = getCylinderBoundariesForSector(end_sector,
                                         sectors_per_cylinder)
    if end_sector != cyl_bounds[1]:
        end_sector = cyl_bounds[0] - 1

    return (start_sector, end_sector)


def getCylinderBoundariesForSector(sector, sectors_per_cylinder):
    """
    'A well-known claim says that partitions should start and end at
     cylinder boundaries.'
       -(http://tldp.org/HOWTO/Large-Disk-HOWTO-6.html#ss6.2)

    While the kernel may have no problems with partitions that break this
    claim, we can never fully guarantee that the user's tools won't flag
    this as a (non-)error. So let's keep everybody happy.

    A disk cylinder is made up of sectors. Given a sector, and the number of
    sectors that make up a cylinder, return the first and last sectors within
    the cylinder (cylinder_first_sector, cylinder_last_sector)
    """
    cylinder = int(math.floor((float(sector) / sectors_per_cylinder)))

    # first sector in the cylinder.
    first_sector = (sectors_per_cylinder * cylinder) + 1

    # last sector in the cylinder.
    last_sector = (sectors_per_cylinder * cylinder) + sectors_per_cylinder

    return (first_sector, last_sector)


def getUnusedSpacesInRange(start_sector, end_sector, min_size, part_list):
    """
    For a given range with start_sector and end_sector, return a list of tuples in
    the format (start_of_free_range, end_of_free_range).

    part_list contains the list of known partitions in the given range.
    This function relies on the accuracy of part_list to report free
    spaces.

    min_size is the filter where the algorithm will ignore free spaces
    which are less than min_size. min_size is a byte value.
    """
    start_of_free_space = 1
    free_spaces = []
    for p in part_list:
        # if the leading space is less than the minimum size requested,
        # then skip to next partition.
        # leading space is the space from the end of the previous partition
        # to the start of the current partition
        leading_space = (p.start_sector - start_sector) * p.disk.sector_size
        if leading_space < min_size:
            cylinder_boundaries = getCylinderBoundariesForSector(p.end_sector,
                                                   p.disk.sectors_per_cylinder)
            start_of_free_space = cylinder_boundaries[1] + 1
            continue

        # leading space is large enough, so we round down to the free end sector
        # to the cylinder boundary that is free and nearest to the start of
        # the current partition.
        cylinder_boundaries = getCylinderBoundariesForSector(p.start_sector,
                                                  p.disk.sectors_per_cylinder)
        end_of_free_space = cylinder_boundaries[0] - 1
        free_spaces.append((start_of_free_space, end_of_free_space))

        # the end of the current partition is the start of the leading space
        # for the next partition.
        cylinder_boundaries = getCylinderBoundariesForSector(p.end_sector,
                                                p.disk.sectors_per_cylinder)
        start_of_free_space = cylinder_boundaries[1] + 1

    if part_list:
        # at this point we have found all the leading spaces. However, if the last
        # partition in the given part_list does not end on the given end of range,
        # then there may still be space suitable for use.
        trailing_space = (end_sector - part_list[-1].end_sector) * p.disk.sector_size
        if trailing_space > min_size:
            cylinder_boundaries = getCylinderBoundariesForSector(part_list[-1].end_sector,
                                                               p.disk.sectors_per_cylinder)
            start_of_free_space = cylinder_boundaries[1] + 1
        
            (end_cylinder_start, end_cylinder_end) = getCylinderBoundariesForSector(end_sector,
                                                           p.disk.sectors_per_cylinder)
            free_spaces.append((start_of_free_space, end_cylinder_end - 1))
    else:
        free_spaces.append((start_sector, end_sector))

    return free_spaces


def getSpacesAvailable(disk, min_size=1048576, first_usable_sector=63):
    """
    Search for unpartitioned spaces on disk and return them as an array of sizes.
    Possible states where this might not work as expected:
        *(where PriN represents primary partitions, ExtN represents extended 
          partitions, and LogN represents Logical Partitions)

        1. State:
            Disk: { Pri1 |     Pri2    | Pri3 |      Pri4      |   Free Space   }
           Reason:
            A disk cannot contain more than 4 primary/extended partitions. So in this
            situation, even though there is free space on the disk, we are
            unable to use it.
        2. State:
            Disk: { Pri1 |   Pri2  | Pri3 |   Free Space  |        Ext4           }
                                                          |   Log1  | Log2 | Log3 |
           Reason:
            Similar to state 1. A disk cannot contain more than 4 primary/extended
            partitions. Usually, we can create any number of logical partitions on
            an extended partition, but in this case:
                a. there is no more free space on Ext4
                b. a new primary partition cannot be created
            So no space will be available.
    """
    # disk is not partitioned, all space is available.
    if not disk.partition_dict:
        return [(disk.sectors, disk.length)]

    # filter out the disk's partitions.
    primary = []
    extended = None
    logical = []
    for partition in disk.partition_dict.values():
        if partition.type == 'primary':
            primary.append(partition)
        elif partition.type == 'extended':
            extended = partition
        else:
            logical.append(partition)

    # only continue if number of primary partitions plus extended
    # partition is less than 3.
    # See documentation above for the states which do not work.
    no_of_primary_and_extended_partitions = len(primary)
    free_spaces = []
    if extended:
        no_of_primary_and_extended_partitions += 1
    if no_of_primary_and_extended_partitions < 4:
        partition_list = primary
        if extended:
            partition_list.append(extended)
        partition_list.sort(partition_sector_comparator)
        free_spaces = getUnusedSpacesInRange(first_usable_sector, disk.length, min_size, partition_list)

    # if extended partition exists, then look for spaces between logical partitions.
    if extended:
        logical.sort(partition_sector_comparator)
        free_spaces += getUnusedSpacesInRange(extended.start_sector, extended.end_sector, min_size, logical)

    return free_spaces
