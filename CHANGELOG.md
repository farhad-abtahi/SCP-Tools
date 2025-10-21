# Changelog

All notable changes to the SCP-ECG Tools project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-10-21

### Added - Comprehensive Configurable Anonymization

**IMPORTANT NOTE:** Acquisition date/time tags (25, 26) are NEVER removed, only replaced with dummy data or preserved. This is required by Idoven API which validates that these tags exist in Section 1.

#### New Features
- **Configurable anonymization options** with two new parameters:
  - `anonymize_datetime` (bool, default: True) - Controls acquisition date/time anonymization
  - `anonymize_freetext` (bool, default: True) - Controls free text and medical history removal
- **Expanded tag coverage** in Section 1 anonymization:
  - Tags 0, 1: Patient names (now included)
  - Tag 5: Date of birth (duplicate of tag 10)
  - Tags 21, 22: Physician/technician names
  - Tag 30: Free text field (configurable)
  - Tag 31: Medical history codes (configurable)
- **Dual-level CRC validation**:
  - File-level CRC-CCITT checksum (polynomial 0x1021, initial 0xFFFF)
  - Section-level CRCs using PhysioNet parsescp.c algorithm
  - All 10+ sections validated and updated
- **Example script**: `example_anonymization_options.py` demonstrating 4 anonymization scenarios
- **Comprehensive documentation** in README with use cases and compatibility notes

#### Technical Improvements
- `update_section_crcs()` method implementing parsescp.c CRC algorithm
- `calculate_scp_section_crc()` static method for section CRC calculation
- `update_file_size()` method to ensure correct file size header
- Enhanced `_anonymize_section_1_tags()` with configurable logic
- Proper handling of bytearray slicing to prevent file expansion

#### Compatibility
- ✅ **ECG Toolkit** (SourceForge C# library) - Files open successfully
- ✅ **Idoven API** - Files accepted and processed
- ✅ **PhysioNet tools** - Compatible with standard parsers
- ✅ **Custom SCP readers** - Standards-compliant output

#### Documentation
- Updated README.md with:
  - Quick Start section at top
  - Comprehensive anonymization guide
  - CRC validation documentation
  - Compatibility & validation section
  - Enhanced HIPAA compliance documentation
  - Use case examples
  - Updated flowcharts
- New CHANGELOG.md tracking version history
- Enhanced API documentation with new parameters

### Fixed

#### Critical Fixes
- **File size mismatch** - Files were 5 bytes larger than original
  - Root cause: Bytearray expansion in name anonymization
  - Fixed by pre-sizing replacement bytes before assignment
- **Missing section CRCs** - Only file-level CRC was being updated
  - Implemented complete section CRC recalculation
  - Added PhysioNet parsescp.c algorithm
  - All sections now have valid CRCs
- **Missing file-level CRC** - Original implementation didn't update CRC
  - Added CRC-CCITT calculation
  - CRC updated after all modifications

#### Validation Fixes
- Files now pass validation in ECG Toolkit (previously failed to open)
- Files accepted by Idoven API (previously rejected for missing sections)
- Sections 3 and 6 remain 100% byte-identical to original
- Pointer table (Section 0) preserved perfectly

### Changed

#### Breaking Changes
- `SCPAnonymizer.__init__()` signature updated:
  ```python
  # Old
  SCPAnonymizer(filepath, anonymous_id=None)

  # New
  SCPAnonymizer(filepath, anonymous_id=None,
                anonymize_datetime=True, anonymize_freetext=True)
  ```
- Default behavior now anonymizes MORE fields (dates, times, free text)
  - To preserve old behavior, use: `anonymize_datetime=False, anonymize_freetext=False`

#### Non-Breaking Changes
- `save_anonymized()` now calls CRC updates in correct order:
  1. `update_file_size()`
  2. `update_section_crcs()`
  3. `update_crc()`
- Enhanced logging with section-by-section CRC updates
- More comprehensive `changes_made` tracking

### Security

#### HIPAA Compliance Improvements
- **7 categories of PHI now removed** (up from 3):
  1. Patient names (all name fields)
  2. Patient ID (replaced with anonymous ID)
  3. Date of birth (set to 1900-01-01)
  4. Acquisition date/time (configurable, default: anonymized)
  5. Physician/technician names (zeroed out)
  6. Free text fields (configurable, default: removed)
  7. Medical history codes (configurable, default: removed)

#### Data Integrity
- 100% preservation of ECG signal data (sections 3 and 6)
- Valid CRCs guarantee file integrity
- No byte expansion ensures file size consistency
- Pointer table integrity maintained

## [1.0.0] - 2025-10-20

### Initial Release

#### Features
- SCP-ECG file reading and parsing
- ECG visualization in two formats:
  - Medical paper format (mimics ECG paper)
  - Standard waveform view
- Basic patient data anonymization
- PNG export for ECG visualizations
- Activity logging system
- Comprehensive test suite (19 tests)

#### Supported Sections
- Section 1: Patient/Device data
- Section 3: Lead definitions
- Section 6: Rhythm data
- Section 7: Global measurements

#### Known Issues
- Files fail to open in ECG Toolkit (CRC errors)
- Idoven API rejects files (missing sections)
- File size mismatch after anonymization
- Section CRCs not validated

---

## Version Numbering

This project follows [Semantic Versioning](https://semver.org/):
- **Major version** (X.0.0): Breaking changes, major new features
- **Minor version** (0.X.0): New features, backward compatible
- **Patch version** (0.0.X): Bug fixes, backward compatible

## Upgrade Notes

### From 1.0.0 to 2.0.0

**If you were using basic anonymization:**
```python
# Old code (1.0.0)
anonymizer = SCPAnonymizer('file.SCP', 'ANON001')
anonymizer.anonymize()

# New code (2.0.0) - same behavior as before
anonymizer = SCPAnonymizer('file.SCP', 'ANON001',
                          anonymize_datetime=False,
                          anonymize_freetext=False)
anonymizer.anonymize()

# Or use new default (recommended for maximum privacy)
anonymizer = SCPAnonymizer('file.SCP', 'ANON001')
anonymizer.anonymize()  # Now anonymizes dates and free text too
```

**Benefits of upgrading:**
- ✅ Files now work with ECG Toolkit and Idoven API
- ✅ Valid CRCs at file and section level
- ✅ More comprehensive anonymization (HIPAA-compliant)
- ✅ Configurable privacy levels for different use cases
- ✅ Better documentation and examples

**Testing after upgrade:**
```bash
# Verify all tests pass
python -m pytest tests/ -v

# Test anonymization on a sample file
python src/scp_anonymizer.py data/original/sample.SCP TEST001

# Verify with example script
python example_anonymization_options.py
```

---

**Author:** Farhad Abtahi
**Project:** SCP-ECG Tools
**Repository:** https://github.com/yourusername/scp-ecg-tools
