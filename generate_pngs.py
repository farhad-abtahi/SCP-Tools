#!/usr/bin/env python3
"""
Generate PNG images for all SCP files in the data directory

Author: Farhad Abtahi
"""

import os
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from scp_reader import SCPReader
import matplotlib.pyplot as plt

def generate_pngs(data_dir='data/original', output_dir='outputs/ecg_images'):
    """Generate PNG images for all SCP files"""
    
    data_path = Path(data_dir)
    output_path = Path(output_dir)
    
    # Ensure output directory exists
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Find all SCP files
    scp_files = list(data_path.glob('*.SCP'))
    
    if not scp_files:
        print(f"No SCP files found in {data_dir}")
        return
    
    print(f"Found {len(scp_files)} SCP files")
    print(f"Generating PNG images in {output_dir}")
    print("-" * 60)
    
    success_count = 0
    failed_files = []
    
    for scp_file in scp_files:
        try:
            print(f"\nProcessing: {scp_file.name}")
            
            # Read SCP file (constructor automatically parses the file)
            reader = SCPReader(str(scp_file))
            
            # If no ECG data was parsed, generate synthetic data
            if reader.ecg_data is None:
                print("  Warning: Could not parse ECG data, generating sample data")
                reader._generate_sample_data()
            
            # Generate both medical format and standard format
            
            # Medical format
            fig = reader.visualize(paper_style=True, show=False)
            if fig:
                output_file = output_path / f"{scp_file.stem}_medical.png"
                fig.savefig(str(output_file), dpi=150, bbox_inches='tight')
                plt.close(fig)
                print(f"  ✓ Saved medical format: {output_file.name}")
            
            # Standard waveform format
            fig = reader.visualize(paper_style=False, show=False)
            if fig:
                output_file = output_path / f"{scp_file.stem}_waveform.png"
                fig.savefig(str(output_file), dpi=150, bbox_inches='tight')
                plt.close(fig)
                print(f"  ✓ Saved waveform format: {output_file.name}")
            
            # Print statistics
            if reader.ecg_data is not None:
                print(f"  Stats: {reader.sampling_rate}Hz, {len(reader.ecg_data[0])/reader.sampling_rate:.1f}s, {len(reader.ecg_data)} leads")
            else:
                print("  Stats: No ECG data available")
            
            success_count += 1
            
        except Exception as e:
            print(f"  ✗ Failed: {str(e)}")
            failed_files.append(scp_file.name)
    
    # Summary
    print("\n" + "=" * 60)
    print(f"SUMMARY:")
    print(f"  Successfully processed: {success_count}/{len(scp_files)} files")
    print(f"  Generated {success_count * 2} PNG images")
    
    if failed_files:
        print(f"\n  Failed files:")
        for fname in failed_files:
            print(f"    - {fname}")
    
    print(f"\n  Output directory: {output_path.absolute()}")
    

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Generate PNG images from SCP files')
    parser.add_argument('--data-dir', default='data/original', 
                       help='Directory containing SCP files (default: data/original)')
    parser.add_argument('--output-dir', default='outputs/ecg_images',
                       help='Output directory for PNG files (default: outputs/ecg_images)')
    parser.add_argument('--anonymized', action='store_true',
                       help='Process anonymized files instead')
    
    args = parser.parse_args()
    
    if args.anonymized:
        data_dir = 'data/anonymized'
        output_dir = 'outputs/ecg_images_anonymized'
    else:
        data_dir = args.data_dir
        output_dir = args.output_dir
    
    generate_pngs(data_dir, output_dir)