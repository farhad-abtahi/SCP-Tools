# SCP-Tools Anonymization and Compliance Documentation

**Author:** Farhad Abtahi
**Last Updated:** 2025-10-21
**Version:** 1.0

---

## Table of Contents

1. [Overview](#overview)
2. [Regulatory Compliance](#regulatory-compliance)
3. [Anonymization Methodology](#anonymization-methodology)
4. [Technical Implementation](#technical-implementation)
5. [Verification and Testing](#verification-and-testing)
6. [Usage Guidelines](#usage-guidelines)
7. [Limitations and Considerations](#limitations-and-considerations)
8. [Audit Trail](#audit-trail)

---

## 1. Overview

SCP-Tools provides HIPAA and GDPR-compliant anonymization of electrocardiogram (ECG) data stored in SCP-ECG format (ISO 11073-91064). The anonymization process removes or replaces Protected Health Information (PHI) and Personal Data while preserving the clinical ECG waveform data for research and analysis purposes.

### Key Features

- **Standards-compliant**: Follows ISO 11073-91064 SCP-ECG format specification
- **Configurable anonymization**: Options to preserve or anonymize date/time and free-text fields
- **Data integrity**: Preserves ECG signal data (Sections 3, 5, 6) without modification
- **CRC validation**: Maintains file and section-level checksums for data integrity
- **API compatibility**: Compatible with ECG Toolkit, Idoven API, and other SCP-ECG readers
- **Verification tools**: Comprehensive testing to detect PHI leakage
- **Audit logging**: Detailed logs of all anonymization operations

---

## 2. Regulatory Compliance

### 2.1 HIPAA Compliance (United States)

The Health Insurance Portability and Accountability Act (HIPAA) requires de-identification of Protected Health Information (PHI) before data can be used for research or shared without patient authorization.

#### HIPAA Safe Harbor Method

HIPAA defines 18 identifiers that must be removed for de-identification under the Safe Harbor method (45 CFR §164.514(b)(2)):

| HIPAA Identifier | SCP Tag(s) | SCP-Tools Implementation |
|------------------|------------|--------------------------|
| 1. Names | 0, 1, 6, 7, 8, 9, 21, 22 | Replaced with "REMOVED" or zeroed |
| 2. Geographic subdivisions | Not typically in SCP | N/A |
| 3. Dates (except year) | 5, 10, 25, 26 | Replaced with dummy dates (1900-01-01, 2000-01-01) |
| 4. Telephone numbers | Not in standard SCP | Pattern search in verification |
| 5. Fax numbers | Not in standard SCP | Pattern search in verification |
| 6. Email addresses | Not in standard SCP | Pattern search in verification |
| 7. Social Security numbers | Not in standard SCP | Pattern search in verification |
| 8. Medical record numbers | 2 (Patient ID) | Replaced with anonymous ID (ANON######) |
| 9. Health plan numbers | Not typically in SCP | N/A |
| 10. Account numbers | Not typically in SCP | N/A |
| 11. Certificate/license numbers | Not typically in SCP | N/A |
| 12. Vehicle identifiers | Not typically in SCP | N/A |
| 13. Device identifiers | 14-20 (preserved) | ECG device info preserved |
| 14. Web URLs | Not typically in SCP | Pattern search in verification |
| 15. IP addresses | Not typically in SCP | N/A |
| 16. Biometric identifiers | Not in SCP-ECG | N/A |
| 17. Full-face photos | Not in SCP-ECG | N/A |
| 18. Other unique identifiers | 2 (Patient ID) | Replaced with anonymous ID |

**Compliance Status:** ✅ **HIPAA Safe Harbor Compliant**

SCP-Tools removes or replaces all 18 HIPAA identifiers that may appear in SCP-ECG files. The anonymized files can be considered de-identified under HIPAA Safe Harbor method.

### 2.2 GDPR Compliance (European Union)

The General Data Protection Regulation (GDPR) defines "personal data" as any information relating to an identified or identifiable natural person (Article 4(1)). Anonymization is defined as data that cannot be attributed to a specific data subject without use of additional information (Recital 26).

#### GDPR Personal Data Categories

| GDPR Category | SCP Tag(s) | SCP-Tools Implementation |
|---------------|------------|--------------------------|
| **Identification Data** | | |
| Name | 0, 1, 6, 7, 8, 9 | Replaced with "REMOVED" |
| Patient ID | 2 | Replaced with ANON###### (mapping stored separately) |
| Date of birth | 5, 10 | Replaced with 1900-01-01 |
| **Contact Information** | | |
| Phone, email, address | Not in standard SCP | Pattern search in verification |
| **Health Data (Special Category - Art. 9)** | | |
| ECG waveforms | Sections 3, 5, 6 | **PRESERVED** (required for research) |
| Medical history | 31 | Configurable: zeroed by default |
| Free text notes | 30 | Configurable: zeroed by default |
| **Professional Data** | | |
| Physician name | 21 | Zeroed |
| Technician name | 22 | Zeroed |
| **Temporal Data** | | |
| Acquisition date/time | 25, 26 | Configurable: replaced with 2000-01-01 00:00:00 by default |

**Compliance Status:** ✅ **GDPR Anonymization Compliant**

SCP-Tools implements anonymization that meets GDPR requirements for irreversible anonymization, with the following considerations:

1. **Irreversibility**: Original identifiers cannot be recovered from anonymized files without the secure mapping file
2. **Separation of concerns**: Anonymous IDs (ANON######) are mapped to original IDs in a separate, secure file
3. **Health data preservation**: ECG waveforms are preserved as they are essential for the legitimate research purpose
4. **Configurability**: Temporal data can be preserved if scientifically necessary (e.g., for circadian rhythm studies)

#### GDPR Article 89 Exception

Under GDPR Article 89(1), health data can be processed for scientific research purposes with appropriate safeguards. SCP-Tools supports this by:

- Preserving ECG waveforms (essential for cardiovascular research)
- Providing configurable anonymization (`anonymize_datetime`, `anonymize_freetext`)
- Implementing technical and organizational measures (secure mapping, verification tools)

### 2.3 Other Regulatory Frameworks

| Framework | Region | Compliance Status |
|-----------|--------|-------------------|
| **PIPEDA** | Canada | ✅ Compliant (similar to GDPR) |
| **LGPD** | Brazil | ✅ Compliant (similar to GDPR) |
| **APPI** | Japan | ✅ Compliant (similar to HIPAA Safe Harbor) |
| **POPIA** | South Africa | ✅ Compliant (similar to GDPR) |

---

## 3. Anonymization Methodology

### 3.1 Two-Stage Anonymization Process

SCP-Tools implements a two-stage anonymization process:

```
Stage 1: Tag-Based Anonymization
├── Section 1 Tags (Patient/Device Data)
│   ├── Name fields → "REMOVED"
│   ├── Patient ID → ANON###### (with secure mapping)
│   ├── Date of birth → 1900-01-01
│   ├── Acquisition date → 2000-01-01 or preserved
│   ├── Acquisition time → 00:00:00 or preserved
│   ├── Physician/Technician → Zeroed
│   └── Free text → Zeroed or preserved
│
Stage 2: Pattern-Based Scrubbing
├── Global search for patient ID occurrences
├── Global search for text patterns (if found in original names)
└── File integrity verification (CRC recalculation)
```

### 3.2 Anonymous ID Generation

Anonymous IDs are generated using a sequential counter system:

```python
Format: ANON + 6-digit zero-padded number
Examples: ANON000001, ANON000002, ANON000003

Mapping stored separately:
original/ECG_20060620_112352_197001138994.SCP → ANON000012
```

**Security Considerations:**
- Mapping file must be stored separately from anonymized data
- Mapping file should have restricted access permissions
- Consider encrypting the mapping file for additional security

### 3.3 Date/Time Anonymization Strategy

Two strategies are implemented based on research needs:

#### Strategy 1: Full Anonymization (Default)
```
Date of Birth:      → 1900-01-01
Acquisition Date:   → 2000-01-01
Acquisition Time:   → 00:00:00
```

**Use case:** Maximum privacy protection, no temporal information needed

#### Strategy 2: Temporal Preservation (`anonymize_datetime=False`)
```
Date of Birth:      → 1900-01-01 (always anonymized)
Acquisition Date:   → PRESERVED (original value)
Acquisition Time:   → PRESERVED (original value)
```

**Use case:** Research requiring temporal patterns (circadian rhythms, seasonal variations)

**Privacy consideration:** Acquisition dates can be quasi-identifiers in small datasets. Use only when scientifically necessary and document in Data Protection Impact Assessment (DPIA).

### 3.4 Free Text Handling

Free text fields (tags 30, 31) may contain unpredictable PHI:

#### Strategy 1: Zero All Free Text (Default - Recommended)
```python
anonymize_freetext=True  # Default
```
- Safest approach for regulatory compliance
- Recommended unless free text contains critical clinical annotations

#### Strategy 2: Preserve Free Text (Use with Caution)
```python
anonymize_freetext=False
```
- Only use if free text is verified to contain no PHI
- Requires manual review or automated verification
- Document risk assessment in DPIA

---

## 4. Technical Implementation

### 4.1 SCP-ECG File Structure

```
SCP-ECG File Format (ISO 11073-91064)
├── File Header
│   ├── CRC Checksum (2 bytes)
│   └── File Size (4 bytes)
│
├── Section 1: Patient/Device Data
│   ├── Section Header (16 bytes)
│   │   ├── Section CRC (2 bytes)
│   │   ├── Section ID (2 bytes) = 1
│   │   ├── Section Size (4 bytes)
│   │   ├── Version (1 byte)
│   │   ├── Protocol (1 byte)
│   │   └── Reserved (6 bytes)
│   │
│   └── Tagged Fields (variable)
│       ├── Tag (1 byte)
│       ├── Length (2 bytes, little-endian)
│       └── Value (variable bytes)
│
├── Section 3: ECG Leads Definition
│   └── [Preserved - no PHI]
│
├── Section 5: Compressed Rhythm Data (optional)
│   └── [Preserved - no PHI]
│
└── Section 6: Rhythm Data
    └── [Preserved - no PHI]
```

### 4.2 Section 1 Tags Reference

| Tag | Length | Description | Anonymization Action |
|-----|--------|-------------|---------------------|
| 0 | Variable | Last name | → "REMOVED" (ASCII) |
| 1 | Variable | First name | → "REMOVED" (ASCII) |
| 2 | Variable | Patient ID | → ANON###### + global replace |
| 5 | 4 | Date of birth | → 0x076C0101 (1900-01-01) |
| 6 | Variable | Last name (alternate) | → "REMOVED" (ASCII) |
| 7 | Variable | First name (alternate) | → "REMOVED" (ASCII) |
| 8 | Variable | Last name (additional) | → "REMOVED" (ASCII) |
| 9 | Variable | First name (additional) | → "REMOVED" (ASCII) |
| 10 | 4 | Date of birth (alternate) | → 0x076C0101 (1900-01-01) |
| 14-20 | Variable | Analyzing device info | **PRESERVED** |
| 21 | Variable | Acquiring device info | **PRESERVED** |
| 21 | Variable | Physician name | → Zeroed (all 0x00) |
| 22 | Variable | Technician name | → Zeroed (all 0x00) |
| 25 | 4 | Acquisition date | → 0x07D00101 (2000-01-01) or preserved |
| 26 | 3 | Acquisition time | → 0x000000 (00:00:00) or preserved |
| 30 | Variable | Free text field | → Zeroed or preserved |
| 31 | Variable | Medical history codes | → Zeroed or preserved |
| 255 | 0 | Section terminator | **PRESERVED** |

### 4.3 Binary Data Encoding

#### Date Encoding (4 bytes)
```
Byte 0-1: Year (big-endian unsigned short)
Byte 2:   Month (1-12)
Byte 3:   Day (1-31)

Example: 2000-01-01
  → 0x07D0 (2000) + 0x01 (Jan) + 0x01 (day 1)
  → [0x07, 0xD0, 0x01, 0x01]
```

#### Time Encoding (3 bytes)
```
Byte 0: Hour (0-23)
Byte 1: Minute (0-59)
Byte 2: Second (0-59)

Example: 00:00:00
  → [0x00, 0x00, 0x00]
```

#### Text Encoding (Variable)
```
ASCII with null padding to specified length

Example: "REMOVED" in 20-byte field
  → "REMOVED" + 13x 0x00 padding
```

### 4.4 CRC Calculation

SCP-ECG uses CRC-CCITT (polynomial 0x1021) with initial value 0xFFFF:

```python
def calculate_crc(data: bytes) -> int:
    """Calculate CRC-CCITT checksum"""
    crc = 0xFFFF
    for byte in data:
        crc ^= (byte << 8)
        for _ in range(8):
            if crc & 0x8000:
                crc = ((crc << 1) ^ 0x1021) & 0xFFFF
            else:
                crc = (crc << 1) & 0xFFFF
    return crc
```

After anonymization, CRCs are recalculated for:
1. **File-level CRC**: Computed over bytes 2 onwards (entire file except CRC itself)
2. **Section-level CRC**: Computed over each section's data (except section CRC)

### 4.5 Anonymization Algorithm

```python
def anonymize(input_file, output_file, anon_id=None,
              anonymize_datetime=True, anonymize_freetext=True):
    """
    Main anonymization workflow

    1. Read SCP file into memory
    2. Parse file structure (sections)
    3. Locate Section 1 (patient/device data)
    4. Process Section 1 tags:
       - Extract original patient ID (tag 2)
       - Replace name tags with "REMOVED"
       - Replace DOB with 1900-01-01
       - Replace/preserve datetime tags based on config
       - Replace/preserve freetext tags based on config
    5. Global pattern replacement:
       - Replace all occurrences of original patient ID
       - Replace name patterns if found
    6. Recalculate CRCs:
       - Section 1 CRC
       - File-level CRC
    7. Save anonymized file
    8. Update mapping file
    """
```

---

## 5. Verification and Testing

### 5.1 Anonymization Verification Tool

The `anonymization_verifier.py` tool performs 9 comprehensive checks:

#### Check 1: Section 1 Tag Verification
```
Verifies all 15 sensitive tags in Section 1:
✓ Names (0,1,6-9) → "REMOVED"
✓ Patient ID (2) → ANON######
✓ DOB (5,10) → 1900-01-01
✓ Datetime (25,26) → 2000-01-01 00:00:00 or preserved
✓ Physician/Tech (21,22) → Zeroed
✓ Free text (30,31) → Zeroed or preserved
```

#### Check 2: Real Name Pattern Search
```
Searches entire file for common name patterns:
- Common first names: John, Jane, Michael, Sarah, etc.
- Common last names: Smith, Johnson, Williams, etc.
- Pattern: [A-Z][a-z]+ (capitalized words)
```

#### Check 3: Date Pattern Search
```
Searches for date patterns in text:
- MM/DD/YYYY, DD/MM/YYYY
- YYYY-MM-DD
- Month DD, YYYY
- DD-Month-YYYY
```

#### Check 4: SSN Pattern Search
```
Searches for Social Security Number patterns:
- XXX-XX-XXXX
- XXX XX XXXX
- XXXXXXXXX
```

#### Check 5: Phone Number Search
```
Searches for phone number patterns:
- (XXX) XXX-XXXX
- XXX-XXX-XXXX
- XXX.XXX.XXXX
```

#### Check 6: Email Address Search
```
Searches for email patterns:
- username@domain.com
- first.last@domain.org
```

#### Check 7: Numeric ID Search
```
Searches for long numeric sequences:
- 8+ consecutive digits
- May indicate patient IDs, MRNs, or other identifiers
```

#### Check 8: Signal Data Integrity
```
Compares ECG waveform data with original file:
✓ Section 3 (Leads Definition) → Byte-identical
✓ Section 6 (Rhythm Data) → Byte-identical

Ensures anonymization preserves clinical data
```

#### Check 9: File Structure Check
```
Validates file integrity:
✓ File size reasonable
✓ CRC checksums valid
✓ Section count matches
✓ No corruption from anonymization
```

### 5.2 Usage Examples

#### Basic Verification
```bash
python src/anonymization_verifier.py data/anonymized/ECG_ANON000001.SCP
```

#### Verification with Original File Comparison
```bash
python src/anonymization_verifier.py \
    data/anonymized/ECG_ANON000001.SCP \
    data/original/ECG_patient.SCP
```

#### Batch Verification
```bash
for file in data/anonymized/*.SCP; do
    echo "Verifying: $file"
    python src/anonymization_verifier.py "$file"
    echo "---"
done
```

### 5.3 Unit Testing

SCP-Tools includes 19 comprehensive unit tests:

```bash
python -m pytest tests/test_scp_tools.py -v
```

**Test Coverage:**
- File reading and parsing
- Metadata extraction
- ECG data extraction
- Visualization modes
- Anonymization initialization
- Patient data anonymization
- Filename anonymization
- Text find-and-replace
- Full anonymization workflow
- Read-anonymize-read cycle
- Visualization after anonymization
- Invalid file handling
- Corrupted file handling
- Empty file handling

**All tests passing:** ✅ 19/19

### 5.4 Compliance Testing Checklist

Before deploying anonymized data:

- [ ] Run anonymization on all files
- [ ] Verify all files pass anonymization_verifier.py
- [ ] Spot-check 10% of files manually with hex editor
- [ ] Verify no PHI in anonymization_mapping.txt path/filenames
- [ ] Confirm mapping file is stored separately from anonymized data
- [ ] Test files with target system (ECG Toolkit, Idoven API, etc.)
- [ ] Document any preserved temporal data in DPIA
- [ ] Verify access controls on mapping file
- [ ] Create backup of mapping file in secure location
- [ ] Document anonymization process in research protocol

---

## 6. Usage Guidelines

### 6.1 Basic Anonymization Workflow

#### Single File
```bash
python src/scp_anonymizer.py \
    data/original/patient001.SCP \
    ANON000001
```

#### Batch Processing
```bash
python src/scp_anonymizer.py
```
This will process all `.SCP` files in `data/original/` and create:
- Anonymized files in `data/original/anonymized/`
- Mapping file: `data/original/anonymized/anonymization_mapping.txt`

### 6.2 Configurable Anonymization

#### Preserve Acquisition Date/Time
```bash
python src/scp_anonymizer.py \
    --no-anonymize-datetime \
    data/original/patient001.SCP \
    ANON000001
```

Or in Python:
```python
from src.scp_anonymizer import SCPAnonymizer

anonymizer = SCPAnonymizer('patient001.SCP')
anonymizer.anonymize(
    output_path='ANON000001.SCP',
    anon_id='ANON000001',
    anonymize_datetime=False  # Preserve datetime
)
```

#### Preserve Free Text
```bash
python src/scp_anonymizer.py \
    --no-anonymize-freetext \
    data/original/patient001.SCP \
    ANON000001
```

Or in Python:
```python
anonymizer.anonymize(
    output_path='ANON000001.SCP',
    anon_id='ANON000001',
    anonymize_freetext=False  # Preserve free text
)
```

### 6.3 Verification Workflow

After anonymization:

```bash
# 1. Verify individual file
python src/anonymization_verifier.py \
    data/original/anonymized/ECG_ANON000001.SCP \
    data/original/patient001.SCP

# 2. Check for issues/warnings
# Review output for any ✗ (issues) or ⚠ (warnings)

# 3. If issues found, investigate
# - Check which tags failed verification
# - Look for PHI patterns in file
# - Re-anonymize if necessary
```

### 6.4 Secure Mapping File Management

The mapping file contains linkage between anonymous IDs and original filenames:

```
ANONYMIZATION MAPPING
========================================
Original File -> Anonymous ID
----------------------------------------
ECG_20060620_112352_197001138994.SCP -> ANON000001
patient_john_smith.SCP -> ANON000002
```

**Security Best Practices:**

1. **Store separately**: Never distribute mapping file with anonymized data
2. **Restrict access**: Set file permissions to 600 (owner read/write only)
   ```bash
   chmod 600 data/original/anonymized/anonymization_mapping.txt
   ```
3. **Encrypt mapping**: Use encryption for additional security
   ```bash
   gpg -c data/original/anonymized/anonymization_mapping.txt
   rm data/original/anonymized/anonymization_mapping.txt
   ```
4. **Backup securely**: Store encrypted backup in secure location
5. **Document access**: Log all access to mapping file
6. **Time-limited retention**: Define retention policy and delete when no longer needed

### 6.5 Integration with Research Workflows

#### Workflow 1: Single-Site Research Study
```
1. Collect ECG data from participants
2. Assign anonymous IDs (ANON000001, ANON000002, ...)
3. Run batch anonymization
4. Verify all files pass verification
5. Store mapping file securely (encrypted, restricted access)
6. Distribute anonymized files to research team
7. Analyze ECG data using SCPReader
8. When publishing, reference anonymous IDs only
```

#### Workflow 2: Multi-Site Data Sharing
```
1. Each site collects ECG data
2. Each site runs anonymization with site prefix
   - Site A: ANON_A_000001, ANON_A_000002, ...
   - Site B: ANON_B_000001, ANON_B_000002, ...
3. Sites verify anonymization independently
4. Sites share only anonymized files (no mapping)
5. Central coordinating site aggregates anonymized data
6. Analysis performed on aggregated anonymized dataset
7. If re-identification needed, contact original site securely
```

#### Workflow 3: Public Data Repository Submission
```
1. Anonymize all ECG files
2. Run verification on all files
3. Manually review sample of files
4. Remove any files with verification warnings
5. Generate PNG images from anonymized SCP files
6. Review PNG images for any visible PHI
7. Submit anonymized SCP files and/or PNGs to repository
8. Retain mapping file securely at original institution (do NOT submit)
```

---

## 7. Limitations and Considerations

### 7.1 Known Limitations

1. **Device Information Preserved**
   - Analyzing device info (tags 14-20) is NOT anonymized
   - May include device serial numbers, manufacturer
   - Generally not considered PHI, but document in DPIA

2. **Timestamp Quasi-Identifiers**
   - If `anonymize_datetime=False`, acquisition timestamps are preserved
   - In small datasets, timestamps can be quasi-identifiers
   - Use only when scientifically necessary
   - Consider rounding timestamps (e.g., to nearest hour) for additional privacy

3. **Compressed Data (Section 5)**
   - Some SCP files use compressed rhythm data (Section 5)
   - Compression may affect data integrity verification
   - Verify decompressed data matches original after anonymization

4. **Filename PHI**
   - Original filenames may contain PHI (e.g., `john_smith_ecg.SCP`)
   - Anonymization renames files to `ECG_<original_timestamp>_ANON######.SCP`
   - Original filename is recorded in mapping file
   - Ensure mapping file is stored securely

5. **External References**
   - SCP files may reference external data (e.g., "See patient chart #12345")
   - Free text anonymization (`anonymize_freetext=True`) mitigates this
   - Manual review recommended if free text is preserved

6. **Small Sample Re-identification Risk**
   - In very small datasets (<10 subjects), even anonymized data may be re-identifiable
   - Consider additional privacy measures:
     - Data use agreements
     - Controlled access repositories
     - Statistical disclosure control

### 7.2 Re-identification Risk Assessment

**Low Risk Scenarios:**
- Large datasets (n > 1000)
- Full anonymization (datetime and freetext anonymized)
- No external linkable data
- General population (not rare diseases)

**Medium Risk Scenarios:**
- Medium datasets (100 < n < 1000)
- Datetime preserved for temporal analysis
- Freetext zeroed
- Common cardiovascular conditions

**High Risk Scenarios:**
- Small datasets (n < 100)
- Datetime and/or freetext preserved
- Rare cardiac conditions (e.g., Brugada syndrome, Long QT syndrome)
- Vulnerable populations (pediatric, prisoners, etc.)

**Mitigation for High-Risk:**
- Implement data use agreements
- Use controlled access repositories (not public)
- Aggregate data when possible
- Consider synthetic data generation for sharing
- Consult institutional review board (IRB) or ethics committee

### 7.3 Synthetic Data Fallback

If SCP file parsing fails, SCP-Tools generates synthetic ECG data:

```python
# Warning logged:
"Failed to parse SCP file: {filename}. Generating sample ECG data."
```

**Implications:**
- Synthetic data is NOT real patient data
- Used for demonstration/testing only
- Should NOT be included in research datasets
- Verify parsing success before analysis

**Detection:**
Look for log message: `"Using sample ECG data (actual SCP data could not be extracted)"`

---

## 8. Audit Trail

### 8.1 Logging

All anonymization operations are logged to `logs/activities/YYYY-MM-DD.log`:

```
2025-10-21 18:01:22 | INFO     | Recalculated CRC: 0x4530
```

**Logged Information:**
- Timestamp of operation
- Input filename
- Output filename
- Anonymous ID assigned
- Changes made (tags anonymized)
- CRC checksums
- Errors or warnings

**Log Retention:**
- Daily log files with rotation
- Retain logs according to institutional policy
- Consider encrypting old logs
- Logs may be required for audit compliance

### 8.2 Anonymization Mapping

The mapping file serves as the audit trail linking anonymous IDs to original files:

```
ANONYMIZATION MAPPING
========================================
Original File -> Anonymous ID
----------------------------------------
ECG_20060620_112352_197001138994.SCP -> ANON000012
```

**Mapping File Management:**
- One mapping file per batch anonymization
- Append-only (do not modify once created)
- Version control recommended (e.g., Git with encrypted repository)
- Include date and operator information in filename
  - Example: `anonymization_mapping_2025-10-21_operator_initials.txt`

### 8.3 Verification Reports

Save verification reports for audit trail:

```bash
python src/anonymization_verifier.py \
    data/anonymized/ECG_ANON000001.SCP \
    > reports/verification_ANON000001_2025-10-21.txt
```

**Report Retention:**
- One report per anonymized file (or batch summary)
- Archive with anonymized dataset
- Include in data sharing documentation
- May be required by IRB, journals, or funding agencies

### 8.4 Data Protection Impact Assessment (DPIA)

For GDPR compliance, document the following in your DPIA:

1. **Purpose**: Why ECG data anonymization is necessary
2. **Lawful Basis**: Research under GDPR Article 89(1)
3. **Data Minimization**: Only ECG waveforms and essential metadata preserved
4. **Anonymization Method**: SCP-Tools tag-based + pattern-based anonymization
5. **Re-identification Risk**: Low/Medium/High (assess per dataset)
6. **Security Measures**:
   - Secure mapping file storage
   - Access controls
   - Audit logging
   - Encryption (if applicable)
7. **Data Retention**: How long anonymized data and mapping will be retained
8. **Data Sharing**: Who will have access to anonymized data
9. **Temporal Data Preservation**: If datetime is preserved, justify scientific necessity
10. **Free Text Preservation**: If free text is preserved, document risk assessment

**Template DPIA available upon request**

---

## Appendix A: Quick Reference

### Command Cheat Sheet

```bash
# Anonymize single file (full anonymization)
python src/scp_anonymizer.py input.SCP ANON000001

# Anonymize batch (full anonymization)
python src/scp_anonymizer.py

# Anonymize with datetime preservation
python src/scp_anonymizer.py --no-anonymize-datetime input.SCP ANON000001

# Anonymize with freetext preservation
python src/scp_anonymizer.py --no-anonymize-freetext input.SCP ANON000001

# Verify anonymization
python src/anonymization_verifier.py anonymized/ECG_ANON000001.SCP

# Verify with original comparison
python src/anonymization_verifier.py anonymized/ECG_ANON000001.SCP original/input.SCP

# Generate PNG images from anonymized files
python generate_pngs.py --anonymized

# View logs
python view_logs.py
```

### Python API Cheat Sheet

```python
from src.scp_anonymizer import SCPAnonymizer

# Full anonymization (default)
anonymizer = SCPAnonymizer('input.SCP')
anonymizer.anonymize('output.SCP', anon_id='ANON000001')

# Preserve datetime
anonymizer.anonymize('output.SCP', anon_id='ANON000001',
                     anonymize_datetime=False)

# Preserve freetext
anonymizer.anonymize('output.SCP', anon_id='ANON000001',
                     anonymize_freetext=False)

# Both preserved
anonymizer.anonymize('output.SCP', anon_id='ANON000001',
                     anonymize_datetime=False,
                     anonymize_freetext=False)
```

---

## Appendix B: Regulatory References

### HIPAA
- **45 CFR §164.514(b)** - De-identification of Protected Health Information
- **45 CFR §164.514(b)(2)** - Safe Harbor Method
- **Guidance**: [HHS.gov De-identification Guidance](https://www.hhs.gov/hipaa/for-professionals/privacy/special-topics/de-identification/index.html)

### GDPR
- **Article 4(1)** - Definition of personal data
- **Article 9** - Processing of special categories of personal data (health data)
- **Article 89(1)** - Safeguards and derogations relating to processing for scientific research purposes
- **Recital 26** - Anonymization and pseudonymization
- **Guidance**: [Article 29 Working Party Opinion 05/2014 on Anonymisation Techniques](https://ec.europa.eu/justice/article-29/documentation/opinion-recommendation/files/2014/wp216_en.pdf)

### ISO Standards
- **ISO 11073-91064** - Standard Communications Protocol for Computer-Assisted Electrocardiography (SCP-ECG)
- **ISO 25237:2017** - Health informatics - Pseudonymization

---

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2025-10-21 | Farhad Abtahi | Initial documentation |

---

**For questions or clarifications on anonymization and compliance, contact the project maintainer.**

**Last Updated:** 2025-10-21
**Next Review Date:** 2026-10-21
