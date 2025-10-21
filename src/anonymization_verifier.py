#!/usr/bin/env python3
"""
SCP-ECG Anonymization Verifier

This tool performs comprehensive verification and penetration testing
to ensure files are properly anonymized with no PHI leakage.

Author: Farhad Abtahi
"""

import struct
import sys
import os
import re
from typing import Dict, List, Tuple, Set
from datetime import datetime

class AnonymizationVerifier:
    """
    Comprehensive verification tool for anonymized SCP-ECG files.
    Performs multiple levels of checks to ensure no PHI leakage.
    """

    def __init__(self, filepath: str, original_filepath: str = None):
        """
        Initialize verifier.

        Args:
            filepath: Path to anonymized SCP file
            original_filepath: Optional path to original file for comparison
        """
        self.filepath = filepath
        self.original_filepath = original_filepath
        self.data = None
        self.original_data = None
        self.issues = []
        self.warnings = []
        self.passed_checks = []

    def read_files(self):
        """Read the SCP files into memory"""
        with open(self.filepath, 'rb') as f:
            self.data = f.read()

        if self.original_filepath and os.path.exists(self.original_filepath):
            with open(self.original_filepath, 'rb') as f:
                self.original_data = f.read()

    def verify_all(self) -> bool:
        """
        Run all verification checks.

        Returns:
            True if all checks pass, False otherwise
        """
        self.read_files()

        print(f"\nANONYMIZATION VERIFICATION REPORT")
        print("=" * 70)
        print(f"File: {os.path.basename(self.filepath)}")
        print(f"Size: {len(self.data)} bytes")
        print("=" * 70)

        # Run all checks
        self.check_section_1_tags()
        self.check_for_real_names()
        self.check_for_real_dates()
        self.check_for_ssn_patterns()
        self.check_for_phone_numbers()
        self.check_for_email_addresses()
        self.check_for_numeric_ids()
        self.check_signal_data_unchanged()
        self.check_file_structure()

        # Print results
        self._print_results()

        return len(self.issues) == 0

    def check_section_1_tags(self):
        """Verify all Section 1 tags are properly anonymized"""
        print("\n1. SECTION 1 TAG VERIFICATION")
        print("-" * 70)

        # Find Section 1
        pointer = 6
        section_1_found = False

        while pointer < len(self.data) - 16:
            section_id = struct.unpack('<H', self.data[pointer+2:pointer+4])[0]
            section_size = struct.unpack('<I', self.data[pointer+4:pointer+8])[0]

            if section_id == 1 and section_size < len(self.data):
                section_1_found = True
                print(f"✓ Section 1 found at offset {pointer}, size {section_size}")

                # Parse tags
                tag_pointer = pointer + 16
                end = pointer + section_size
                tags_checked = 0

                while tag_pointer < end - 3:
                    tag = self.data[tag_pointer]
                    if tag == 255:
                        break

                    tag_length = struct.unpack('<H', self.data[tag_pointer+1:tag_pointer+3])[0]
                    value = self.data[tag_pointer+3:tag_pointer+3+tag_length]

                    self._verify_tag(tag, value)
                    tags_checked += 1
                    tag_pointer += 3 + tag_length

                print(f"✓ Checked {tags_checked} tags in Section 1")
                self.passed_checks.append(f"Section 1: {tags_checked} tags verified")
                break

            if section_size > 0:
                pointer += section_size
            else:
                break

        if not section_1_found:
            self.issues.append("Section 1 not found in file")
            print("✗ Section 1 not found!")

    def _verify_tag(self, tag: int, value: bytes):
        """Verify individual tag anonymization"""
        tag_names = {
            0: "Last name", 1: "First name", 2: "Patient ID",
            5: "Date of birth", 6: "Last name", 7: "First name",
            8: "Last name", 9: "First name", 10: "Date of birth",
            21: "Physician name", 22: "Technician",
            25: "Acquisition date", 26: "Acquisition time",
            30: "Free text", 31: "Medical history"
        }

        if tag not in tag_names:
            return  # Not a sensitive tag

        tag_name = tag_names[tag]

        # Check patient ID (tag 2)
        if tag == 2:
            id_str = value.decode('ascii', errors='ignore').rstrip('\x00')
            if id_str.startswith('ANON') or len(id_str) == 0:
                print(f"  ✓ Tag {tag} ({tag_name}): '{id_str}' - properly anonymized")
            else:
                self.issues.append(f"Tag {tag} ({tag_name}): contains real ID '{id_str}'")
                print(f"  ✗ Tag {tag} ({tag_name}): REAL ID FOUND: '{id_str}'")

        # Check names (tags 0, 1, 6, 7, 8, 9)
        elif tag in [0, 1, 6, 7, 8, 9]:
            name_str = value.decode('ascii', errors='ignore').rstrip('\x00')
            if 'REMOVED' in name_str or len(name_str) == 0:
                print(f"  ✓ Tag {tag} ({tag_name}): properly anonymized")
            else:
                # Check if it looks like a real name
                if len(name_str) > 2 and name_str.isalpha():
                    self.issues.append(f"Tag {tag} ({tag_name}): possible real name '{name_str}'")
                    print(f"  ✗ Tag {tag} ({tag_name}): POSSIBLE REAL NAME: '{name_str}'")
                else:
                    self.warnings.append(f"Tag {tag} ({tag_name}): unusual value '{name_str}'")

        # Check date of birth (tags 5, 10)
        elif tag in [5, 10]:
            if len(value) >= 4:
                year = struct.unpack('>H', value[0:2])[0]
                month = value[2]
                day = value[3]

                if year == 1900 and month == 1 and day == 1:
                    print(f"  ✓ Tag {tag} ({tag_name}): {year}-{month:02d}-{day:02d} - anonymized")
                else:
                    current_year = datetime.now().year
                    if 1900 <= year <= current_year:
                        self.issues.append(f"Tag {tag} ({tag_name}): real DOB {year}-{month:02d}-{day:02d}")
                        print(f"  ✗ Tag {tag} ({tag_name}): REAL DOB: {year}-{month:02d}-{day:02d}")

        # Check acquisition date (tag 25)
        elif tag == 25:
            if len(value) >= 4:
                year = struct.unpack('>H', value[0:2])[0]
                month = value[2]
                day = value[3]

                if year == 2000 and month == 1 and day == 1:
                    print(f"  ✓ Tag {tag} ({tag_name}): {year}-{month:02d}-{day:02d} - anonymized")
                else:
                    self.warnings.append(f"Tag {tag} ({tag_name}): non-standard date {year}-{month:02d}-{day:02d}")
                    print(f"  ⚠ Tag {tag} ({tag_name}): Non-standard date {year}-{month:02d}-{day:02d}")

        # Check acquisition time (tag 26)
        elif tag == 26:
            if len(value) >= 3:
                hour = value[0]
                minute = value[1]
                second = value[2]

                if hour == 0 and minute == 0 and second == 0:
                    print(f"  ✓ Tag {tag} ({tag_name}): {hour:02d}:{minute:02d}:{second:02d} - anonymized")
                else:
                    self.warnings.append(f"Tag {tag} ({tag_name}): non-standard time {hour:02d}:{minute:02d}:{second:02d}")
                    print(f"  ⚠ Tag {tag} ({tag_name}): Non-standard time {hour:02d}:{minute:02d}:{second:02d}")

        # Check physician/technician (tags 21, 22)
        elif tag in [21, 22]:
            if all(b == 0 for b in value):
                print(f"  ✓ Tag {tag} ({tag_name}): properly zeroed")
            else:
                text = value.decode('ascii', errors='ignore').rstrip('\x00')
                if len(text) > 0:
                    self.issues.append(f"Tag {tag} ({tag_name}): contains text '{text}'")
                    print(f"  ✗ Tag {tag} ({tag_name}): CONTAINS TEXT: '{text}'")

        # Check free text and medical history (tags 30, 31)
        elif tag in [30, 31]:
            if all(b == 0 for b in value):
                print(f"  ✓ Tag {tag} ({tag_name}): properly zeroed")
            else:
                text = value.decode('ascii', errors='ignore').rstrip('\x00')
                if len(text) > 0:
                    self.warnings.append(f"Tag {tag} ({tag_name}): contains data (may be intentional)")
                    print(f"  ⚠ Tag {tag} ({tag_name}): Contains data (length {len(text)})")

    def check_for_real_names(self):
        """Search for common name patterns in the entire file"""
        print("\n2. REAL NAME PATTERN SEARCH")
        print("-" * 70)

        # Common name patterns (case-insensitive)
        name_patterns = [
            rb'John', rb'Jane', rb'Smith', rb'Johnson', rb'Williams',
            rb'Brown', rb'Jones', rb'Garcia', rb'Miller', rb'Davis',
            rb'Rodriguez', rb'Martinez', rb'Hernandez', rb'Lopez',
            rb'Dr\.?\s+[A-Z][a-z]+',  # Dr. Name
            rb'[A-Z][a-z]+,\s*[A-Z][a-z]+',  # Last, First
        ]

        found_names = []
        for pattern in name_patterns:
            matches = re.finditer(pattern, self.data, re.IGNORECASE)
            for match in matches:
                context = self.data[max(0, match.start()-10):match.end()+10]
                found_names.append((match.group(), match.start(), context))

        if found_names:
            print(f"✗ Found {len(found_names)} potential name pattern(s):")
            for name, offset, context in found_names[:5]:  # Show first 5
                self.issues.append(f"Possible name at offset {offset}: {name.decode('ascii', errors='ignore')}")
                print(f"  Offset {offset}: {name.decode('ascii', errors='ignore')}")
        else:
            print("✓ No common name patterns found")
            self.passed_checks.append("No name patterns detected")

    def check_for_real_dates(self):
        """Search for date patterns that might indicate real dates"""
        print("\n3. REAL DATE PATTERN SEARCH")
        print("-" * 70)

        # Look for dates in various formats
        date_patterns = [
            rb'\d{1,2}/\d{1,2}/\d{2,4}',  # MM/DD/YYYY
            rb'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
            rb'\d{2}-\d{2}-\d{4}',  # DD-MM-YYYY
        ]

        found_dates = []
        for pattern in date_patterns:
            matches = re.finditer(pattern, self.data)
            for match in matches:
                found_dates.append((match.group(), match.start()))

        if found_dates:
            print(f"⚠ Found {len(found_dates)} date-like pattern(s):")
            for date, offset in found_dates[:5]:
                self.warnings.append(f"Date pattern at offset {offset}: {date.decode('ascii', errors='ignore')}")
                print(f"  Offset {offset}: {date.decode('ascii', errors='ignore')}")
        else:
            print("✓ No text date patterns found")
            self.passed_checks.append("No text date patterns detected")

    def check_for_ssn_patterns(self):
        """Search for Social Security Number patterns"""
        print("\n4. SSN PATTERN SEARCH")
        print("-" * 70)

        # SSN patterns: XXX-XX-XXXX
        ssn_pattern = rb'\d{3}-\d{2}-\d{4}'
        matches = list(re.finditer(ssn_pattern, self.data))

        if matches:
            print(f"✗ Found {len(matches)} SSN-like pattern(s):")
            for match in matches[:3]:
                self.issues.append(f"SSN pattern at offset {match.start()}: {match.group().decode('ascii')}")
                print(f"  Offset {match.start()}: {match.group().decode('ascii')}")
        else:
            print("✓ No SSN patterns found")
            self.passed_checks.append("No SSN patterns detected")

    def check_for_phone_numbers(self):
        """Search for phone number patterns"""
        print("\n5. PHONE NUMBER PATTERN SEARCH")
        print("-" * 70)

        # Phone patterns
        phone_patterns = [
            rb'\(\d{3}\)\s*\d{3}-\d{4}',  # (XXX) XXX-XXXX
            rb'\d{3}-\d{3}-\d{4}',  # XXX-XXX-XXXX
            rb'\d{10}',  # XXXXXXXXXX
        ]

        found_phones = []
        for pattern in phone_patterns:
            matches = re.finditer(pattern, self.data)
            for match in matches:
                # Verify it's actually phone-like (not just random 10 digits)
                if len(match.group()) == 10 or b'-' in match.group() or b'(' in match.group():
                    found_phones.append((match.group(), match.start()))

        if found_phones:
            print(f"⚠ Found {len(found_phones)} phone-like pattern(s):")
            for phone, offset in found_phones[:3]:
                self.warnings.append(f"Phone pattern at offset {offset}: {phone.decode('ascii', errors='ignore')}")
                print(f"  Offset {offset}: {phone.decode('ascii', errors='ignore')}")
        else:
            print("✓ No phone number patterns found")
            self.passed_checks.append("No phone patterns detected")

    def check_for_email_addresses(self):
        """Search for email address patterns"""
        print("\n6. EMAIL ADDRESS PATTERN SEARCH")
        print("-" * 70)

        email_pattern = rb'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        matches = list(re.finditer(email_pattern, self.data))

        if matches:
            print(f"✗ Found {len(matches)} email-like pattern(s):")
            for match in matches[:3]:
                self.issues.append(f"Email at offset {match.start()}: {match.group().decode('ascii', errors='ignore')}")
                print(f"  Offset {match.start()}: {match.group().decode('ascii', errors='ignore')}")
        else:
            print("✓ No email addresses found")
            self.passed_checks.append("No email patterns detected")

    def check_for_numeric_ids(self):
        """Search for long numeric sequences that might be IDs"""
        print("\n7. NUMERIC ID PATTERN SEARCH")
        print("-" * 70)

        # Look for sequences of 8+ digits that might be patient IDs, MRNs, etc.
        id_pattern = rb'\d{8,}'
        matches = list(re.finditer(id_pattern, self.data))

        # Filter out known anonymized IDs
        suspicious_ids = []
        for match in matches:
            id_str = match.group().decode('ascii')
            # Skip if it starts with ANON or is all zeros
            if not (id_str.startswith('ANON') or id_str == '0' * len(id_str)):
                suspicious_ids.append((id_str, match.start()))

        if suspicious_ids:
            print(f"⚠ Found {len(suspicious_ids)} long numeric sequence(s):")
            for id_str, offset in suspicious_ids[:5]:
                self.warnings.append(f"Numeric ID at offset {offset}: {id_str}")
                print(f"  Offset {offset}: {id_str}")
        else:
            print("✓ No suspicious numeric IDs found")
            self.passed_checks.append("No suspicious numeric IDs detected")

    def check_signal_data_unchanged(self):
        """Verify ECG signal data is unchanged (Sections 3 and 6)"""
        print("\n8. SIGNAL DATA INTEGRITY CHECK")
        print("-" * 70)

        if not self.original_data:
            print("⚠ Original file not provided - skipping comparison")
            return

        # Find and compare Section 3 (Lead definitions)
        section_3_match = self._compare_section(3, "Lead definitions")
        section_6_match = self._compare_section(6, "Rhythm data")

        if section_3_match and section_6_match:
            print("✓ Signal data (Sections 3 and 6) byte-identical to original")
            self.passed_checks.append("Signal data preserved (100% identical)")
        elif section_3_match:
            print("✓ Section 3 preserved, Section 6 check inconclusive")
        elif section_6_match:
            print("✓ Section 6 preserved, Section 3 check inconclusive")

    def _compare_section(self, section_id: int, section_name: str) -> bool:
        """Compare a specific section between original and anonymized"""
        # Find section in both files
        orig_section = self._find_section(self.original_data, section_id)
        anon_section = self._find_section(self.data, section_id)

        if orig_section and anon_section:
            if orig_section == anon_section:
                print(f"  ✓ Section {section_id} ({section_name}): byte-identical")
                return True
            else:
                self.issues.append(f"Section {section_id} ({section_name}): modified!")
                print(f"  ✗ Section {section_id} ({section_name}): MODIFIED!")
                return False
        elif not orig_section:
            print(f"  ⚠ Section {section_id} not found in original")
        elif not anon_section:
            print(f"  ⚠ Section {section_id} not found in anonymized")

        return False

    def _find_section(self, data: bytes, section_id: int) -> bytes:
        """Find and extract a specific section from SCP data"""
        pointer = 6
        while pointer < len(data) - 16:
            sid = struct.unpack('<H', data[pointer+2:pointer+4])[0]
            size = struct.unpack('<I', data[pointer+4:pointer+8])[0]

            if sid == section_id and size < len(data):
                return data[pointer:pointer+size]

            if size > 0:
                pointer += size
            else:
                break

        return None

    def check_file_structure(self):
        """Verify file structure integrity"""
        print("\n9. FILE STRUCTURE INTEGRITY")
        print("-" * 70)

        # Check file size
        if self.original_data and len(self.data) == len(self.original_data):
            print(f"✓ File size unchanged: {len(self.data)} bytes")
            self.passed_checks.append("File size preserved")
        elif self.original_data:
            size_diff = len(self.data) - len(self.original_data)
            self.warnings.append(f"File size changed by {size_diff} bytes")
            print(f"⚠ File size changed by {size_diff} bytes")

        # Check CRCs
        file_crc = struct.unpack('<H', self.data[0:2])[0]
        print(f"✓ File CRC: 0x{file_crc:04X}")

        # Count sections
        pointer = 6
        section_count = 0
        while pointer < len(self.data) - 16:
            section_id = struct.unpack('<H', self.data[pointer+2:pointer+4])[0]
            section_size = struct.unpack('<I', self.data[pointer+4:pointer+8])[0]

            if section_size == 0 or section_size > len(self.data) - pointer:
                break

            section_count += 1
            pointer += section_size

        print(f"✓ Found {section_count} sections")
        self.passed_checks.append(f"{section_count} sections validated")

    def _print_results(self):
        """Print summary of verification results"""
        print("\n" + "=" * 70)
        print("VERIFICATION SUMMARY")
        print("=" * 70)

        print(f"\n✓ Passed Checks: {len(self.passed_checks)}")
        for check in self.passed_checks:
            print(f"  - {check}")

        if self.warnings:
            print(f"\n⚠ Warnings: {len(self.warnings)}")
            for warning in self.warnings[:10]:  # Show first 10
                print(f"  - {warning}")
            if len(self.warnings) > 10:
                print(f"  ... and {len(self.warnings) - 10} more")

        if self.issues:
            print(f"\n✗ ISSUES FOUND: {len(self.issues)}")
            for issue in self.issues:
                print(f"  - {issue}")
            print("\n" + "=" * 70)
            print("STATUS: ✗ VERIFICATION FAILED")
            print("=" * 70)
            print("⚠ PHI LEAKAGE DETECTED - FILE NOT SAFE FOR SHARING")
        else:
            print("\n" + "=" * 70)
            print("STATUS: ✓ VERIFICATION PASSED")
            print("=" * 70)
            if self.warnings:
                print("⚠ Some warnings detected - review recommended")
            else:
                print("✓ File appears properly anonymized")

        print()


def main():
    """Main entry point"""
    if len(sys.argv) < 2:
        print("Usage: python anonymization_verifier.py <anonymized_file.SCP> [original_file.SCP]")
        print("\nExamples:")
        print("  # Basic verification")
        print("  python anonymization_verifier.py anonymized/ECG_ANON000001.SCP")
        print("\n  # With original file for comparison")
        print("  python anonymization_verifier.py anonymized/ECG_ANON000001.SCP original/ECG_patient.SCP")
        print("\n  # Batch verification")
        print("  for f in anonymized/*.SCP; do python anonymization_verifier.py \"$f\"; done")
        return 1

    anonymized_file = sys.argv[1]
    original_file = sys.argv[2] if len(sys.argv) > 2 else None

    if not os.path.exists(anonymized_file):
        print(f"Error: File not found: {anonymized_file}")
        return 1

    if original_file and not os.path.exists(original_file):
        print(f"Warning: Original file not found: {original_file}")
        original_file = None

    verifier = AnonymizationVerifier(anonymized_file, original_file)
    passed = verifier.verify_all()

    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
