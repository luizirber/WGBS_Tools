"""
Tests bsseeker module
"""

from wgbs_tools import bsseeker
from wgbs_tools import utilities
import os
import subprocess


def test_bowtie():
    """Makes sure bowtie is present"""
    assert utilities.which('bowtie'), 'Could not find bowtie in path.'


def test_bsseeker2(bs2_path):
    """Makes sure BS-Seeker2 is in path as defined by info.yaml"""
    assert os.path.isfile(bs2_path), \
        'Could not find BS-Seeker2 at {}. If this is an incorrect location, ' \
        'Please change info.yaml accordingly.'.format(bs2_path)


def test_align_bs2_noadap(bs2_path, fasta, bs2_index, noadap_fastq, working_dir,
                          correct_noadapsam):
    """
    Tests function align_bs2 from bsseeker using reads without adapter
    contamination trimmed out.
    """
    params = '-m 3 -f bam'
    bam_out = os.path.join(working_dir, 'noadap_test_out.bam')
    out_sam = os.path.join(working_dir, 'noadap_test_out.sam')
    bsseeker.align_bs2(bs2_path, params, fasta, bs2_index, noadap_fastq,
                       bam_out)
    command = 'samtools view -o {} {}'.format(out_sam, bam_out)
    subprocess.check_call(command, shell = True)
    # command = 'cp {} {}'.format(out_sam, correct_noadapsam)
    # subprocess.check_call(command, shell = True)
    with open(out_sam, 'r') as content_file:
        testcontent = content_file.read()
        assert testcontent == correct_noadapsam, 'Full alignment error.'


def test_align_bs2_adaptrim(bs2_path, fasta, bs2_index, trimmed_fastq,
                            working_dir, correct_trimmedsam):
    """
    Tests function align_bs2 from bsseeker using reads with adapter
    contamination trimmed out of the reads, as well as 10bp chewed back.
    """
    params = '-m 2 -f bam'
    bam_out = os.path.join(working_dir, 'trimmed_test_out.bam')
    out_sam = os.path.join(working_dir, 'trimmed_test_out.sam')
    bsseeker.align_bs2(bs2_path, params, fasta, bs2_index, trimmed_fastq,
                       bam_out)
    command = 'samtools view -o {} {}'.format(out_sam, bam_out)
    subprocess.check_call(command, shell = True)
    # command = 'mv {} {}'.format(out_sam, correct_trimmedsam)
    # subprocess.check_call(command, shell = True)
    with open(out_sam, 'r') as content_file:
        testcontent = content_file.read()
        assert testcontent == correct_trimmedsam, 'Trimmed alignment error.'
