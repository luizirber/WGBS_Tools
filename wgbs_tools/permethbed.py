"""
Functions that utilize Percentage Methylated Bed files (aka permeth.bed)

Utilizes pybedtools found at http://daler.github.io/pybedtools/

Note: If you use pybedtools in your work, please cite the pybedtools
manuscript and the BEDTools manuscript:
Dale RK, Pedersen BS, and Quinlan AR. 2011. Pybedtools: a flexible Python
library for manipulating genomic datasets and annotations. Bioinformatics
27(24):3423-3424.
Quinlan AR and Hall IM, 2010. BEDTools: a flexible suite of utilities for
comparing genomic features. Bioinformatics 26(6):841-842.
"""

from pybedtools import BedTool
import logging
import os
from wgbs_tools import utilities
from threading import Thread


def meth_count(feature):
    """
    Returns the number of methylated reads from a permeth BedTools object

    :param feature: feature line of a BedTools object line
    :return: int as the number of methylated reads
    """
    print(feature.name)
    [perc, total] = utilities.show_value(feature.name).split('-')
    return int(float(perc)*float(total)+.5)


def total_count(feature):
    """
    Returns the number of reads from a permeth BedTools object line

    :param feature: feature line of a BedTools object
    :return: int as the total number of reads covered
    """
    total = utilities.show_value(feature.name).split('-')[1]
    return int(total)


def chrom_meth(pm_sample, chrom, roi_chrom, mask, meth_dict):
    """"""
    permeth_name = '{}{}.bed'.format(pm_sample, chrom)
    logging.info('Processing {}.'.format(permeth_name))
    pm_full = BedTool(permeth_name)
    pm_masked = pm_full - mask
    pm = pm_masked.intersect(roi_chrom, u=True)
    for roi_line in roi_chrom:
        start = int(roi_line.start())
        end = int(roi_line.end())
        meth = 0
        total = 0
        for pm_line in pm.all_hits(roi_line):
            meth = meth + int(meth_count(pm_line))
            total = total + int(total_count(pm_line))
        meth_dict[start][end][pm_sample]['meth'] = int(meth)
        meth_dict[start][end][pm_sample]['total'] = int(total)


def roi_meth(in_bed_prefixes, in_sample_list, out_table, mask_file, roi_file,
             min_read_count, min_file_count, out_2col_name, thread_count):
    """Creates a table with the methylation across desired Regions of
    Interest (ROI)
    1) Output file
    2) Input BED or GTF File (needs to have a header line)
    3) Input BED or GTF column for name of ROI (ex: 3 for bed files) (NA for no name)
    4) Minimum Read Threshold
    5) Minimum File Threshold (Files without NA data)
    6,8+) Input Percent Methylation Folder Prefix (exclude \"chr\" from the path)
    7,9+) Input Sample Name (for header of output file)
    """
    outfile = open(out_table, 'wb')
    header_line = 'chrom\tstart\tend\tname'
    for samp in in_sample_list:
        header_line = '{}\t{}'.format(header_line, samp)
    header_line = '{}\n'.format(header_line)
    outfile.write(header_line)
    if out_2col_name != "":
        out_2col = open(out_2col_name, 'wb')
        header_line = 'chrom\tstart\tend\tname'
        for samp in in_sample_list:
            header_line = '{}\t{}_methylated\t{}_total'\
                .format(header_line, samp, samp)
        header_line = '{}\n'.format(header_line)
        out_2col.write(header_line)

    roi = BedTool(roi_file)
    if mask_file != "":
        mask = BedTool(mask_file)
    else:
        mask = BedTool([('chrNONE',0,0)])

    # Get chromosome names in ROI file
    logging.info('Loading chromosomes:')
    chrom_names_tmp = []
    for line in roi:
        chrom = utilities.show_value(line.chrom)
        if chrom not in chrom_names_tmp:
            chrom_names_tmp.append(chrom)
    # Remove chromosome names without accompanying PerMeth file
    chrom_names = []
    for chrom in chrom_names_tmp:
        keepchrom = True
        for pm_sample in in_bed_prefixes:
            permeth_name = '{}{}.bed'.format(pm_sample, chrom)
        if not os.path.exists(permeth_name):
            logging.warning('Cannot access {}, skipping {}!'
                            .format(permeth_name, chrom))
            keepchrom = False
        if keepchrom:
            chrom_names.append(chrom)

    # Loop through, gather information, and print each chrom info
    import ipdb; ipdb.set_trace()
    for chrom in chrom_names:
        # Create methylation dictionary for chromosomal ROI
        roi_chrom = roi.all_hits(BedTool([(chrom, 0, 999999999)])[0])
        meth_dict =  utilities.nested_dict(4, str)
        for feature in roi_chrom:
            meth_dict[feature.start][feature.end]['name'] = feature.name
        proc_list = in_bed_prefixes
        def worker():
            while proc_list:
                pm_prefix = proc_list.pop()
                chrom_meth(pm_prefix, chrom, roi_chrom, mask, meth_dict)
        threads = [Thread(target=worker) for i in range(thread_count)]
        [t.start() for t in threads]
        [t.join() for t in threads]

        # Print information into table
        for start in sorted(meth_dict):
            for end in sorted(meth_dict[start]):
                name = meth_dict[start][end]['name']
                print_line = '{}\t{}\t{}\t{}'.format(chrom, start, end, name)
                out2_col_line = print_line
                file_print_count = 0
                for pm_sample in in_bed_prefixes:
                    meth = meth_dict[start][end][pm_sample]['meth']
                    total = meth_dict[start][end][pm_sample]['total']
                    if total >= min_read_count:
                        meth_perc = float(meth)/float(total)
                        print_line = '{0}\t{1:.3f}'.format(print_line, meth_perc)
                        file_print_count+=1
                    else:
                        print_line = '{0}\tNA'.format(print_line)
                    out2_col_line = '{}\t{}\t{}'\
                        .format(out2_col_line, meth, total)
                if file_print_count >= min_file_count:
                    outfile.write(print_line)
                    if out_2col_name != "":
                        out_2col.write(out2_col_line)


