#!/usr/bin/env python3
"""
SCP-ECG Tools - Command Line Interface

Simple CLI for SCP file operations:
- View: Display ECG visualization
- Info: Show file metadata
- Anonymize: Remove patient identifiers
- Batch: Process multiple files

Usage:
    python scp_tools.py view <file.SCP> [--medical|--standard]
    python scp_tools.py info <file.SCP>
    python scp_tools.py anonymize <file.SCP> [output.SCP]
    python scp_tools.py batch <input_dir> <output_dir>
"""

import sys
import os
import argparse
from pathlib import Path

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.scp_reader import SCPReader
from src.scp_anonymizer import SCPAnonymizer


def view_ecg(args):
    """View ECG visualization"""
    if not os.path.exists(args.file):
        print(f"Error: File not found: {args.file}")
        return 1
    
    reader = SCPReader(args.file)
    reader.read_file()
    
    if args.info:
        reader.print_info()
    
    paper_style = not args.standard
    print(f"Displaying {'medical paper' if paper_style else 'standard waveform'} view...")
    reader.visualize(paper_style=paper_style)
    
    if args.save:
        import matplotlib.pyplot as plt
        output_file = args.save if args.save != True else f"output/{Path(args.file).stem}.png"
        os.makedirs(os.path.dirname(output_file) or '.', exist_ok=True)
        plt.savefig(output_file, dpi=150, bbox_inches='tight')
        print(f"Saved to: {output_file}")
    
    return 0


def show_info(args):
    """Show file information"""
    if not os.path.exists(args.file):
        print(f"Error: File not found: {args.file}")
        return 1
    
    reader = SCPReader(args.file)
    reader.read_file()
    reader.print_info()
    
    if args.verbose:
        print("\nDetailed Section Information:")
        for section_id, section_data in sorted(reader.sections.items()):
            print(f"  Section {section_id}: {section_data.get('size', 0)} bytes")
    
    return 0


def anonymize_file(args):
    """Anonymize a single file"""
    if not os.path.exists(args.file):
        print(f"Error: File not found: {args.file}")
        return 1
    
    # Determine output path
    if args.output:
        output_path = args.output
    else:
        output_dir = "data/anonymized"
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, f"anon_{Path(args.file).name}")
    
    # Create anonymizer
    anon_id = args.id if args.id else None
    anonymizer = SCPAnonymizer(args.file, anon_id)
    
    # Perform anonymization
    print(f"Anonymizing: {args.file}")
    output_file = anonymizer.anonymize(output_path)
    
    # Report results
    print(f"Saved to: {output_file}")
    if args.verbose and anonymizer.changes_made:
        print("\nChanges made:")
        for change in anonymizer.changes_made:
            print(f"  - {change}")
    
    return 0


def batch_process(args):
    """Process multiple files"""
    if not os.path.isdir(args.input_dir):
        print(f"Error: Input directory not found: {args.input_dir}")
        return 1
    
    # Create output directory
    os.makedirs(args.output_dir, exist_ok=True)
    
    # Find all SCP files
    scp_files = list(Path(args.input_dir).glob('*.SCP'))
    if not scp_files:
        print(f"No SCP files found in: {args.input_dir}")
        return 1
    
    print(f"Found {len(scp_files)} SCP files")
    
    # Process each file
    results = []
    for i, filepath in enumerate(scp_files, 1):
        print(f"\n[{i}/{len(scp_files)}] Processing: {filepath.name}")
        
        try:
            if args.anonymize:
                # Anonymize file
                anon_id = f"ANON{i:06d}"
                anonymizer = SCPAnonymizer(str(filepath), anon_id)
                output_path = os.path.join(args.output_dir, f"{anon_id}.SCP")
                anonymizer.anonymize(output_path)
                results.append((filepath.name, f"{anon_id}.SCP", "Anonymized"))
            else:
                # Just copy and/or visualize
                reader = SCPReader(str(filepath))
                reader.read_file()
                
                if args.visualize:
                    import matplotlib.pyplot as plt
                    reader.visualize(paper_style=True)
                    output_path = os.path.join(args.output_dir, f"{filepath.stem}.png")
                    plt.savefig(output_path, dpi=150, bbox_inches='tight')
                    plt.close()
                    results.append((filepath.name, f"{filepath.stem}.png", "Visualized"))
                else:
                    results.append((filepath.name, "", "Processed"))
                    
        except Exception as e:
            print(f"  Error: {e}")
            results.append((filepath.name, "", f"Error: {e}"))
    
    # Print summary
    print("\n" + "="*60)
    print("BATCH PROCESSING COMPLETE")
    print("="*60)
    for original, output, status in results:
        if output:
            print(f"{original} -> {output} [{status}]")
        else:
            print(f"{original} [{status}]")
    
    # Save mapping file if anonymizing
    if args.anonymize:
        mapping_file = os.path.join(args.output_dir, "mapping.txt")
        with open(mapping_file, 'w') as f:
            f.write("Original File -> Anonymous ID\n")
            f.write("-"*40 + "\n")
            for original, output, status in results:
                if status == "Anonymized":
                    f.write(f"{original} -> {output}\n")
        print(f"\nMapping saved to: {mapping_file}")
    
    return 0


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='SCP-ECG Tools - Read, visualize, and anonymize ECG files',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  View ECG in medical paper format:
    python scp_tools.py view data/original/ECG.SCP
    
  View ECG in standard format and save:
    python scp_tools.py view ECG.SCP --standard --save output.png
    
  Show file information:
    python scp_tools.py info ECG.SCP --verbose
    
  Anonymize a file:
    python scp_tools.py anonymize ECG.SCP --id STUDY001
    
  Batch anonymize directory:
    python scp_tools.py batch data/original data/anonymized --anonymize
    
  Batch visualize directory:
    python scp_tools.py batch data/original output/images --visualize
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # View command
    view_parser = subparsers.add_parser('view', help='View ECG visualization')
    view_parser.add_argument('file', help='SCP file to view')
    view_parser.add_argument('--standard', action='store_true', 
                           help='Use standard waveform view instead of medical paper')
    view_parser.add_argument('--save', nargs='?', const=True,
                           help='Save visualization to file')
    view_parser.add_argument('--info', action='store_true',
                           help='Also show file information')
    
    # Info command  
    info_parser = subparsers.add_parser('info', help='Show file information')
    info_parser.add_argument('file', help='SCP file to analyze')
    info_parser.add_argument('--verbose', '-v', action='store_true',
                           help='Show detailed information')
    
    # Anonymize command
    anon_parser = subparsers.add_parser('anonymize', help='Anonymize patient data')
    anon_parser.add_argument('file', help='SCP file to anonymize')
    anon_parser.add_argument('output', nargs='?', help='Output file path')
    anon_parser.add_argument('--id', help='Custom anonymous ID')
    anon_parser.add_argument('--verbose', '-v', action='store_true',
                           help='Show detailed changes')
    
    # Batch command
    batch_parser = subparsers.add_parser('batch', help='Process multiple files')
    batch_parser.add_argument('input_dir', help='Input directory')
    batch_parser.add_argument('output_dir', help='Output directory')
    batch_parser.add_argument('--anonymize', action='store_true',
                            help='Anonymize files')
    batch_parser.add_argument('--visualize', action='store_true',
                            help='Generate visualizations')
    
    # Parse arguments
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return 1
    
    # Execute command
    try:
        if args.command == 'view':
            return view_ecg(args)
        elif args.command == 'info':
            return show_info(args)
        elif args.command == 'anonymize':
            return anonymize_file(args)
        elif args.command == 'batch':
            return batch_process(args)
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 1
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == '__main__':
    sys.exit(main())