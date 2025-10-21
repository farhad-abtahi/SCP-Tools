#!/usr/bin/env python3
"""
Example: Using SCPAnonymizer with Configurable Options

This script demonstrates how to use the SCPAnonymizer with different
anonymization settings.

Author: Farhad Abtahi
"""

from src.scp_anonymizer import SCPAnonymizer
import os

def main():
    # Example file
    input_file = "data/original/ECG_20060620_112352_197001138994.SCP"

    if not os.path.exists(input_file):
        print(f"Example file not found: {input_file}")
        return

    print("SCP-ECG ANONYMIZATION OPTIONS EXAMPLE")
    print("=" * 70)
    print()

    # Option 1: Full anonymization (default)
    # - Anonymizes patient identifiers (ID, names, DOB)
    # - Anonymizes physician/technician names
    # - Anonymizes acquisition date/time
    # - Removes free text and medical history
    print("Option 1: Full Anonymization (Default)")
    print("-" * 70)
    anonymizer1 = SCPAnonymizer(
        input_file,
        anonymous_id="FULL_ANON",
        anonymize_datetime=True,    # Anonymize date/time
        anonymize_freetext=True     # Remove free text
    )
    output1 = "data/original/example_full_anon.SCP"
    anonymizer1.anonymize(output1)
    print()

    # Option 2: Preserve timestamps
    # - Anonymizes patient identifiers (ID, names, DOB)
    # - Anonymizes physician/technician names
    # - PRESERVES acquisition date/time
    # - Removes free text and medical history
    print("\nOption 2: Preserve Timestamps")
    print("-" * 70)
    anonymizer2 = SCPAnonymizer(
        input_file,
        anonymous_id="PRESERVE_TIME",
        anonymize_datetime=False,   # Keep original date/time
        anonymize_freetext=True     # Remove free text
    )
    output2 = "data/original/example_preserve_time.SCP"
    anonymizer2.anonymize(output2)
    print()

    # Option 3: Preserve free text
    # - Anonymizes patient identifiers (ID, names, DOB)
    # - Anonymizes physician/technician names
    # - Anonymizes acquisition date/time
    # - PRESERVES free text and medical history
    print("\nOption 3: Preserve Free Text")
    print("-" * 70)
    anonymizer3 = SCPAnonymizer(
        input_file,
        anonymous_id="PRESERVE_TEXT",
        anonymize_datetime=True,     # Anonymize date/time
        anonymize_freetext=False     # Keep free text
    )
    output3 = "data/original/example_preserve_text.SCP"
    anonymizer3.anonymize(output3)
    print()

    # Option 4: Minimal anonymization
    # - Anonymizes patient identifiers (ID, names, DOB)
    # - Anonymizes physician/technician names
    # - PRESERVES acquisition date/time
    # - PRESERVES free text and medical history
    print("\nOption 4: Minimal Anonymization")
    print("-" * 70)
    anonymizer4 = SCPAnonymizer(
        input_file,
        anonymous_id="MINIMAL_ANON",
        anonymize_datetime=False,    # Keep original date/time
        anonymize_freetext=False     # Keep free text
    )
    output4 = "data/original/example_minimal_anon.SCP"
    anonymizer4.anonymize(output4)
    print()

    print("=" * 70)
    print("SUMMARY OF ANONYMIZATION OPTIONS")
    print("=" * 70)
    print()
    print("Always Anonymized (in all options):")
    print("  - Patient ID (replaced with anonymous ID)")
    print("  - Patient names (first name, last name)")
    print("  - Date of birth (set to 1900-01-01)")
    print("  - Physician/technician names (zeroed out)")
    print()
    print("Configurable Options:")
    print("  - anonymize_datetime: True/False")
    print("    Controls whether acquisition date/time is anonymized")
    print("    Default: True (set to 2000-01-01 00:00:00)")
    print()
    print("  - anonymize_freetext: True/False")
    print("    Controls whether free text and medical history is removed")
    print("    Default: True (zeroed out)")
    print()
    print("Files created:")
    print(f"  {output1}")
    print(f"  {output2}")
    print(f"  {output3}")
    print(f"  {output4}")

if __name__ == "__main__":
    main()
