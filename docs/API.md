# API Documentation

## Table of Contents
- [SCPReader API](#scpreader-api)
- [SCPAnonymizer API](#scpanonymizer-api)
- [Data Structures](#data-structures)
- [Exceptions](#exceptions)
- [Examples](#examples)

## SCPReader API

### Class: `SCPReader`

The main class for reading and visualizing SCP-ECG files.

#### Constructor

```python
SCPReader(filepath: str)
```

**Parameters:**
- `filepath` (str): Path to the SCP file to read

**Example:**
```python
reader = SCPReader('data/original/ECG_20170504_163507_123456789.SCP')
```

#### Methods

##### `read_file() -> None`

Reads and parses the SCP file.

**Raises:**
- `FileNotFoundError`: If the file doesn't exist
- `IOError`: If the file cannot be read

**Example:**
```python
reader.read_file()
```

##### `visualize(paper_style: bool = True) -> None`

Displays the ECG visualization.

**Parameters:**
- `paper_style` (bool, optional): If True, uses medical ECG paper format. If False, uses standard waveform view. Default: True

**Example:**
```python
# Medical paper format
reader.visualize(paper_style=True)

# Standard waveform view
reader.visualize(paper_style=False)
```

##### `print_info() -> None`

Prints comprehensive information about the ECG recording to stdout.

**Example:**
```python
reader.print_info()
```

#### Properties

##### `ecg_data -> numpy.ndarray`

ECG waveform data as a 2D numpy array.

**Shape:** (num_leads, num_samples)
- Standard: (12, 5000) for 10-second recording at 500Hz

**Example:**
```python
data = reader.ecg_data
lead_ii = data[1]  # Get Lead II data
```

##### `leads -> List[str]`

List of lead names.

**Standard leads:** ['I', 'II', 'III', 'aVR', 'aVL', 'aVF', 'V1', 'V2', 'V3', 'V4', 'V5', 'V6']

**Example:**
```python
for i, lead_name in enumerate(reader.leads):
    print(f"Lead {lead_name}: {reader.ecg_data[i]}")
```

##### `sampling_rate -> int`

Sampling frequency in Hz.

**Typical value:** 500 Hz

**Example:**
```python
duration_seconds = len(reader.ecg_data[0]) / reader.sampling_rate
```

##### `patient_info -> Dict[str, Any]`

Dictionary containing patient metadata.

**Possible keys:**
- `id`: Patient identifier
- `first_name`: Patient's first name
- `last_name`: Patient's last name
- `birth_date`: Date of birth (YYYY-MM-DD)

**Example:**
```python
if reader.patient_info.get('id'):
    print(f"Patient ID: {reader.patient_info['id']}")
```

##### `device_info -> Dict[str, Any]`

Dictionary containing device/acquisition metadata.

**Possible keys:**
- `id`: Device identifier
- `type`: Device type code
- `acquisition_date`: Recording date (YYYY-MM-DD)
- `acquisition_time`: Recording time (HH:MM:SS)

**Example:**
```python
recording_time = reader.device_info.get('acquisition_time', 'Unknown')
```

## SCPAnonymizer API

### Class: `SCPAnonymizer`

Class for anonymizing patient data in SCP files.

#### Constructor

```python
SCPAnonymizer(filepath: str, anonymous_id: str = None)
```

**Parameters:**
- `filepath` (str): Path to the SCP file to anonymize
- `anonymous_id` (str, optional): Custom anonymous identifier. Default: auto-generated

**Example:**
```python
# With auto-generated ID
anonymizer = SCPAnonymizer('original.SCP')

# With custom ID
anonymizer = SCPAnonymizer('original.SCP', 'STUDY_001')
```

#### Methods

##### `anonymize(output_path: str = None) -> str`

Main method to perform complete anonymization.

**Parameters:**
- `output_path` (str, optional): Path for the anonymized file. Default: auto-generated

**Returns:**
- `str`: Path to the saved anonymized file

**Example:**
```python
output_file = anonymizer.anonymize('data/anonymized/anon_001.SCP')
```

##### `read_file() -> None`

Reads the SCP file into memory.

**Example:**
```python
anonymizer.read_file()
print(f"Read {len(anonymizer.data)} bytes")
```

##### `anonymize_patient_data() -> None`

Performs the actual anonymization of patient identifiers.

**Example:**
```python
anonymizer.read_file()
anonymizer.anonymize_patient_data()
```

##### `save_anonymized(output_path: str = None) -> str`

Saves the anonymized data to a file.

**Parameters:**
- `output_path` (str, optional): Output file path. Default: auto-generated

**Returns:**
- `str`: Path to the saved file

**Example:**
```python
saved_path = anonymizer.save_anonymized('anonymized.SCP')
```

##### `anonymize_filename(output_dir: str = None) -> str`

Generates an anonymized filename.

**Parameters:**
- `output_dir` (str, optional): Output directory. Default: same as original

**Returns:**
- `str`: Anonymized filename with path

**Example:**
```python
new_name = anonymizer.anonymize_filename('data/anonymized')
```

##### `find_and_replace_text(search_bytes: bytes, replace_bytes: bytes) -> int`

Find and replace byte sequences in the file.

**Parameters:**
- `search_bytes` (bytes): Bytes to search for
- `replace_bytes` (bytes): Replacement bytes

**Returns:**
- `int`: Number of replacements made

**Example:**
```python
count = anonymizer.find_and_replace_text(b'John Doe', b'REMOVED')
```

#### Properties

##### `data -> bytearray`

The file data in memory as a mutable bytearray.

**Example:**
```python
file_size = len(anonymizer.data)
```

##### `changes_made -> List[str]`

List of anonymization changes performed.

**Example:**
```python
for change in anonymizer.changes_made:
    print(f"- {change}")
```

##### `anonymous_id -> str`

The anonymous identifier being used.

**Example:**
```python
print(f"Using anonymous ID: {anonymizer.anonymous_id}")
```

## Data Structures

### ECG Data Array

The ECG data is stored as a 2D numpy array:

```python
# Shape: (num_leads, num_samples)
ecg_data = numpy.ndarray(shape=(12, 5000), dtype=float64)

# Access specific lead
lead_i_data = ecg_data[0]    # Lead I
lead_ii_data = ecg_data[1]   # Lead II
# ... etc

# Access specific time range (e.g., first second at 500Hz)
first_second = ecg_data[:, :500]
```

### Metadata Dictionaries

#### Patient Information
```python
patient_info = {
    'id': '123456789',
    'first_name': 'John',
    'last_name': 'Doe',
    'birth_date': '1970-01-01',
    'sex': 'Male',
    'height': 180,  # cm
    'weight': 75    # kg
}
```

#### Device Information
```python
device_info = {
    'id': 12345,
    'type': 1,
    'acquisition_date': '2023-01-15',
    'acquisition_time': '14:30:00',
    'manufacturer': 'Welch Allyn',
    'model': 'CardioPerfect'
}
```

## Exceptions

### FileNotFoundError
Raised when attempting to read a non-existent file.

```python
try:
    reader = SCPReader('nonexistent.SCP')
    reader.read_file()
except FileNotFoundError as e:
    print(f"File not found: {e}")
```

### ValueError
Raised when invalid parameters are provided.

```python
try:
    reader.visualize(paper_style="invalid")  # Should be bool
except ValueError as e:
    print(f"Invalid parameter: {e}")
```

### IOError
Raised when file I/O operations fail.

```python
try:
    anonymizer.save_anonymized('/invalid/path/file.SCP')
except IOError as e:
    print(f"Cannot save file: {e}")
```

## Examples

### Complete Workflow Example

```python
from src.scp_reader import SCPReader
from src.scp_anonymizer import SCPAnonymizer
import matplotlib.pyplot as plt

# 1. Read original file
original_file = 'data/original/ECG_20170504_163507_123456789.SCP'
reader = SCPReader(original_file)
reader.read_file()

# 2. Display information
print("Original file information:")
reader.print_info()

# 3. Visualize
reader.visualize(paper_style=True)
plt.savefig('output/original_ecg.png')
plt.close()

# 4. Anonymize
anonymizer = SCPAnonymizer(original_file, 'STUDY_001')
anon_file = anonymizer.anonymize('data/anonymized/STUDY_001.SCP')

print(f"\nAnonymized file created: {anon_file}")
print("Changes made:")
for change in anonymizer.changes_made:
    print(f"  - {change}")

# 5. Verify anonymization
anon_reader = SCPReader(anon_file)
anon_reader.read_file()

print("\nAnonymized file information:")
anon_reader.print_info()

# 6. Visualize anonymized
anon_reader.visualize(paper_style=True)
plt.savefig('output/anonymized_ecg.png')
```

### Batch Processing Example

```python
import os
from src.scp_reader import SCPReader
from src.scp_anonymizer import SCPAnonymizer

def process_directory(input_dir, output_dir):
    """Process all SCP files in a directory"""
    
    os.makedirs(output_dir, exist_ok=True)
    results = []
    
    for filename in os.listdir(input_dir):
        if not filename.endswith('.SCP'):
            continue
            
        input_path = os.path.join(input_dir, filename)
        
        try:
            # Read and analyze
            reader = SCPReader(input_path)
            reader.read_file()
            
            # Calculate metrics
            duration = len(reader.ecg_data[0]) / reader.sampling_rate
            
            # Anonymize
            anon_id = f"STUDY_{len(results):04d}"
            anonymizer = SCPAnonymizer(input_path, anon_id)
            output_path = os.path.join(output_dir, f"{anon_id}.SCP")
            anonymizer.anonymize(output_path)
            
            results.append({
                'original': filename,
                'anonymous': anon_id,
                'duration': duration,
                'sampling_rate': reader.sampling_rate,
                'num_leads': len(reader.leads)
            })
            
        except Exception as e:
            print(f"Error processing {filename}: {e}")
            
    return results

# Process all files
results = process_directory('data/original', 'data/anonymized')

# Print summary
print(f"Processed {len(results)} files")
for r in results:
    print(f"  {r['original']} -> {r['anonymous']}.SCP "
          f"({r['duration']}s @ {r['sampling_rate']}Hz)")
```

### Custom Visualization Example

```python
import numpy as np
import matplotlib.pyplot as plt
from src.scp_reader import SCPReader

# Read ECG
reader = SCPReader('data/original/sample.SCP')
reader.read_file()

# Create custom figure
fig, axes = plt.subplots(3, 4, figsize=(16, 10))
axes = axes.flatten()

# Plot each lead
for i, (ax, lead_name) in enumerate(zip(axes, reader.leads)):
    # Get time axis
    time = np.arange(len(reader.ecg_data[i])) / reader.sampling_rate
    
    # Plot
    ax.plot(time, reader.ecg_data[i], 'b-', linewidth=0.5)
    ax.set_title(lead_name)
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Amplitude')
    ax.grid(True, alpha=0.3)
    
    # Zoom to first 2 seconds
    ax.set_xlim(0, 2)

plt.suptitle('12-Lead ECG - First 2 Seconds')
plt.tight_layout()
plt.show()
```

### Heart Rate Analysis Example

```python
import numpy as np
from scipy import signal
from src.scp_reader import SCPReader

def detect_r_peaks(ecg_signal, sampling_rate):
    """Simple R-peak detection"""
    # Bandpass filter
    nyquist = sampling_rate / 2
    low = 5 / nyquist
    high = 15 / nyquist
    b, a = signal.butter(1, [low, high], btype='band')
    filtered = signal.filtfilt(b, a, ecg_signal)
    
    # Square
    squared = filtered ** 2
    
    # Moving average
    window = int(0.15 * sampling_rate)
    averaged = np.convolve(squared, np.ones(window)/window, mode='same')
    
    # Find peaks
    peaks, _ = signal.find_peaks(averaged, 
                                 distance=int(0.3*sampling_rate),
                                 height=np.mean(averaged))
    return peaks

# Read ECG
reader = SCPReader('data/original/sample.SCP')
reader.read_file()

# Detect R-peaks in Lead II
lead_ii = reader.ecg_data[1]
r_peaks = detect_r_peaks(lead_ii, reader.sampling_rate)

# Calculate heart rate
rr_intervals = np.diff(r_peaks) / reader.sampling_rate  # in seconds
heart_rates = 60 / rr_intervals  # in bpm

print(f"Average heart rate: {np.mean(heart_rates):.1f} bpm")
print(f"Min heart rate: {np.min(heart_rates):.1f} bpm")
print(f"Max heart rate: {np.max(heart_rates):.1f} bpm")
print(f"Heart rate variability (std): {np.std(heart_rates):.1f} bpm")
```