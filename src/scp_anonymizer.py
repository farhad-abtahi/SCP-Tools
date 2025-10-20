#!/usr/bin/env python3
"""
SCP-ECG File Anonymizer

Author: Farhad Abtahi
"""

import struct
import os
import sys
import hashlib
from datetime import datetime
import shutil
try:
    from .logging_config import setup_logging, ActivityLogger, get_activity_logger
    # Set up module logger
    logger = setup_logging('scp_anonymizer')
except ImportError:
    # Fallback for standalone execution
    from logging_config import setup_logging, ActivityLogger, get_activity_logger
    logger = setup_logging('scp_anonymizer')

class SCPAnonymizer:
    def __init__(self, filepath, anonymous_id=None):
        self.filepath = filepath
        self.data = bytearray()
        self.anonymous_id = anonymous_id or "ANON000000"
        self.changes_made = []

    @staticmethod
    def calculate_crc_ccitt(data):
        """
        Calculate CRC-CCITT checksum for SCP-ECG files.
        Uses polynomial 0x1021 with initial value 0xFFFF.

        Args:
            data: bytes or bytearray to calculate CRC for (excludes the CRC field itself)

        Returns:
            16-bit CRC value
        """
        crc = 0xFFFF
        for byte in data:
            crc ^= (byte << 8)
            for _ in range(8):
                if crc & 0x8000:
                    crc = (crc << 1) ^ 0x1021
                else:
                    crc = crc << 1
                crc &= 0xFFFF
        return crc

    def update_file_size(self):
        """
        Update the file size field in the header.
        The file size is stored at bytes 2-5 (4 bytes, little-endian).
        """
        file_size = len(self.data)
        self.data[2:6] = struct.pack('<I', file_size)
        logger.info(f"Updated file size: {file_size} bytes")

    def update_crc(self):
        """
        Recalculate and update the CRC checksum in the file.
        The CRC is stored in the first 2 bytes (little-endian) and covers
        all data from byte 2 onwards.
        """
        # Calculate CRC on all data except the first 2 bytes (the CRC field itself)
        new_crc = self.calculate_crc_ccitt(self.data[2:])

        # Store CRC in little-endian format at bytes 0-1
        self.data[0:2] = struct.pack('<H', new_crc)

        self.changes_made.append(f"Updated CRC checksum to 0x{new_crc:04X}")
        logger.info(f"Recalculated CRC: 0x{new_crc:04X}")
        
    def read_file(self):
        """Read the SCP file into memory"""
        with open(self.filepath, 'rb') as f:
            self.data = bytearray(f.read())
        print(f"Read {len(self.data)} bytes from {os.path.basename(self.filepath)}")
        
    def anonymize_filename(self, output_dir=None):
        """Generate anonymized filename"""
        # Extract date and time from original filename if present
        basename = os.path.basename(self.filepath)
        parts = basename.replace('.SCP', '').split('_')
        
        # Try to preserve date and time if they exist
        date_part = parts[1] if len(parts) > 1 and len(parts[1]) == 8 else "00000000"
        time_part = parts[2] if len(parts) > 2 and len(parts[2]) == 6 else "000000"
        
        # Create new filename with anonymous ID
        new_filename = f"ECG_{date_part}_{time_part}_{self.anonymous_id}.SCP"
        
        if output_dir:
            return os.path.join(output_dir, new_filename)
        else:
            # Same directory as original
            return os.path.join(os.path.dirname(self.filepath), new_filename)
    
    def find_and_replace_text(self, search_bytes, replace_bytes):
        """Find and replace byte sequences in the file"""
        count = 0
        index = 0
        while True:
            index = self.data.find(search_bytes, index)
            if index == -1:
                break
            # Replace with the new bytes (padded or truncated to same length)
            replace_padded = replace_bytes[:len(search_bytes)]
            if len(replace_padded) < len(search_bytes):
                replace_padded += b'\x00' * (len(search_bytes) - len(replace_padded))
            self.data[index:index+len(search_bytes)] = replace_padded
            count += 1
            index += len(search_bytes)
        return count
    
    def anonymize_patient_data(self):
        """Anonymize patient identifying information in the file"""
        
        # Common patient ID patterns to look for
        # Based on the filenames, the IDs appear to be numeric strings
        original_ids = [
            "197001138994",
            "191010101010", 
            "123456789",
            "1970011389",  # Partial matches
            "1910101010",
            "12345678"
        ]
        
        # Search for and replace patient IDs
        for original_id in original_ids:
            # Try as ASCII text
            count = self.find_and_replace_text(
                original_id.encode('ascii'),
                self.anonymous_id.encode('ascii')
            )
            if count > 0:
                self.changes_made.append(f"Replaced {count} instances of ID '{original_id}'")
            
            # Try as UTF-16 (some medical systems use this)
            count = self.find_and_replace_text(
                original_id.encode('utf-16le'),
                self.anonymous_id.encode('utf-16le')
            )
            if count > 0:
                self.changes_made.append(f"Replaced {count} instances of ID '{original_id}' (UTF-16)")
        
        # Look for common name patterns and replace them
        # Search for "test" which appears in some files
        count = self.find_and_replace_text(b'test', b'ANON')
        if count > 0:
            self.changes_made.append(f"Replaced {count} instances of 'test' with 'ANON'")
        
        # Anonymize section 1 (Patient/Device data) if it exists
        self._anonymize_section_1()
        
    def _anonymize_section_1(self):
        """Specifically handle Section 1 which contains patient demographics"""
        # Try to find section 1 markers
        # Section 1 typically starts after the section pointer table
        
        # Look for the section pointer pattern
        pointer = 6  # Skip CRC and file size
        
        while pointer < len(self.data) - 10:
            try:
                # Try to read section header
                section_id = struct.unpack('<H', self.data[pointer:pointer+2])[0]
                section_size = struct.unpack('<I', self.data[pointer+2:pointer+6])[0]
                
                # Section 1 is patient/device data
                if section_id == 1 and section_size < len(self.data):
                    print(f"Found Section 1 at offset {pointer}")
                    self._anonymize_section_1_tags(pointer + 8, section_size - 8)
                    break
                    
                # Move to next potential section
                if section_size > 0 and section_size < len(self.data):
                    pointer += section_size
                else:
                    pointer += 1
                    
            except:
                pointer += 1
                
    def _anonymize_section_1_tags(self, start_offset, length):
        """Anonymize specific tags in Section 1"""
        pointer = start_offset
        end = min(start_offset + length, len(self.data))
        
        sensitive_tags = {
            2: "Patient ID",
            6: "Last name",
            7: "First name", 
            8: "Last name",
            9: "First name",
            10: "Date of birth"
        }
        
        while pointer < end - 3:
            try:
                tag = self.data[pointer]
                if tag == 255:  # Section terminator
                    break
                    
                tag_length = struct.unpack('<H', self.data[pointer+1:pointer+3])[0]
                
                if tag in sensitive_tags:
                    # Anonymize this field
                    value_start = pointer + 3
                    value_end = min(value_start + tag_length, len(self.data))
                    
                    if tag == 2:  # Patient ID
                        # Replace with anonymous ID
                        anon_bytes = self.anonymous_id.encode('ascii')[:tag_length]
                        anon_bytes += b'\x00' * (tag_length - len(anon_bytes))
                        self.data[value_start:value_end] = anon_bytes
                        self.changes_made.append(f"Anonymized {sensitive_tags[tag]}")
                    elif tag in [6, 7, 8, 9]:  # Names
                        # Replace with REMOVED (properly sized to avoid expanding bytearray)
                        removed_bytes = (b'REMOVED\x00' * (tag_length // 8 + 1))[:tag_length]
                        self.data[value_start:value_end] = removed_bytes
                        self.changes_made.append(f"Anonymized {sensitive_tags[tag]}")
                    elif tag == 10:  # Date of birth
                        # Set to 1900-01-01
                        if tag_length >= 4:
                            self.data[value_start:value_start+2] = struct.pack('>H', 1900)
                            self.data[value_start+2] = 1  # Month
                            self.data[value_start+3] = 1  # Day
                            self.changes_made.append(f"Anonymized {sensitive_tags[tag]}")
                
                pointer += 3 + tag_length
                
            except Exception as e:
                pointer += 1
    
    def save_anonymized(self, output_path=None):
        """Save the anonymized file"""
        if output_path is None:
            output_path = self.anonymize_filename()

        # Update file size and CRC before saving
        self.update_file_size()
        self.update_crc()

        with open(output_path, 'wb') as f:
            f.write(self.data)

        print(f"\nAnonymized file saved as: {output_path}")
        return output_path
    
    def anonymize(self, output_path=None):
        """Main anonymization process"""
        with ActivityLogger('anonymize', f'Anonymizing {os.path.basename(self.filepath)}') as activity:
            print(f"\nAnonymizing: {os.path.basename(self.filepath)}")
            print("-" * 50)
            
            try:
                # Read the file
                self.read_file()
                activity.log_info(f"Read {len(self.data)} bytes")
                
                # Perform anonymization
                self.anonymize_patient_data()
                activity.log_info(f"Anonymization complete: {len(self.changes_made)} changes")
                
                # Save the result
                output_file = self.save_anonymized(output_path)
                activity.log_info(f"Saved to {output_file}")
                
                # Report changes
                if self.changes_made:
                    print("\nChanges made:")
                    for change in self.changes_made:
                        print(f"  - {change}")
                        activity.log_info(f"Change: {change}")
                else:
                    print("\nNo patient identifiers found to anonymize.")
                    print("File copied with anonymized filename.")
                    activity.log_warning("No identifiers found - file copied with new name only")
                
                return output_file
                
            except Exception as e:
                activity.log_error(f"Anonymization failed: {str(e)}")
                raise


def main():
    if len(sys.argv) < 2:
        # Process all SCP files in current directory
        scp_files = [f for f in os.listdir('.') if f.endswith('.SCP') and not 'ANON' in f]
        
        if not scp_files:
            print("No SCP files found to anonymize")
            print("Usage: python anonymize_scp.py [filename.SCP] [anonymous_id]")
            return
        
        print("SCP FILE ANONYMIZER")
        print("=" * 60)
        print(f"Found {len(scp_files)} SCP files to anonymize")
        
        # Create output directory
        output_dir = "anonymized"
        os.makedirs(output_dir, exist_ok=True)
        print(f"\nOutput directory: {output_dir}/")
        
        anonymized_files = []
        
        for i, filepath in enumerate(scp_files, 1):
            # Generate unique anonymous ID for each file
            anon_id = f"ANON{i:06d}"
            
            anonymizer = SCPAnonymizer(filepath, anon_id)
            # Get just the filename, not the full path
            output_filename = os.path.basename(anonymizer.anonymize_filename())
            output_path = os.path.join(output_dir, output_filename)
            output_file = anonymizer.anonymize(output_path)
            anonymized_files.append(output_file)
        
        print("\n" + "=" * 60)
        print(f"ANONYMIZATION COMPLETE")
        print(f"Processed {len(anonymized_files)} files")
        print(f"Anonymized files saved in: {output_dir}/")
        
        # Create a mapping file
        mapping_file = os.path.join(output_dir, "anonymization_mapping.txt")
        with open(mapping_file, 'w') as f:
            f.write("ANONYMIZATION MAPPING\n")
            f.write("=" * 40 + "\n")
            f.write("Original File -> Anonymous ID\n")
            f.write("-" * 40 + "\n")
            for i, original in enumerate(scp_files, 1):
                f.write(f"{original} -> ANON{i:06d}\n")
            f.write("\nNote: This mapping should be kept secure and separate from anonymized data.\n")
        
        print(f"\nMapping file created: {mapping_file}")
        print("(Keep this file secure if you need to re-identify patients later)")
        
    else:
        # Process single file
        filepath = sys.argv[1]
        
        if not os.path.exists(filepath):
            print(f"File not found: {filepath}")
            return
        
        # Use provided anonymous ID or generate one
        anon_id = sys.argv[2] if len(sys.argv) > 2 else None
        
        anonymizer = SCPAnonymizer(filepath, anon_id)
        anonymizer.anonymize()


if __name__ == "__main__":
    main()