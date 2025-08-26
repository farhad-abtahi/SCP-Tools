"""
SCP ECG Tools Package

A comprehensive toolkit for working with SCP-ECG (Standard Communications Protocol 
for Computer-Assisted Electrocardiography) files.

Main components:
- SCPReader: Read and visualize SCP-ECG files
- SCPAnonymizer: Remove patient identifiers from SCP files
"""

from .scp_reader import SCPReader
from .scp_anonymizer import SCPAnonymizer

__version__ = "1.0.0"
__author__ = "SCP ECG Tools"
__all__ = ["SCPReader", "SCPAnonymizer"]