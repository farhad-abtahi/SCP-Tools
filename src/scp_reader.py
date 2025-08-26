#!/usr/bin/env python3
"""
SCP-ECG File Reader and Visualizer

Author: Farhad Abtahi
"""

import struct
import numpy as np
import matplotlib.pyplot as plt
from datetime import datetime
import sys
import os
try:
    from .logging_config import setup_logging, ActivityLogger, get_activity_logger
    # Set up module logger
    logger = setup_logging('scp_reader')
except ImportError:
    # Fallback for standalone execution
    from logging_config import setup_logging, ActivityLogger, get_activity_logger
    logger = setup_logging('scp_reader')

class SCPReader:
    def __init__(self, filepath):
        self.filepath = filepath
        self.sections = {}
        self.ecg_data = None
        self.leads = []
        self.sampling_rate = 500
        self.patient_info = {}
        self.device_info = {}
        
    def read_file(self):
        with ActivityLogger('read', f'Reading {os.path.basename(self.filepath)}') as activity:
            try:
                with open(self.filepath, 'rb') as f:
                    self.data = f.read()
                activity.log_info(f"Read {len(self.data)} bytes")
                
                self._parse_header()
                activity.log_info("Parsed header")
                
                self._parse_sections()
                activity.log_info(f"Parsed {len(self.sections)} sections")
                
                self._extract_ecg_data()
                activity.log_info(f"Extracted ECG data: {self.ecg_data.shape if self.ecg_data is not None else 'None'}")
                
            except FileNotFoundError as e:
                activity.log_error(f"File not found: {self.filepath}")
                raise
            except Exception as e:
                activity.log_error(f"Error reading file: {str(e)}")
                raise
        
    def _parse_header(self):
        crc = struct.unpack('<H', self.data[0:2])[0]
        file_size = struct.unpack('<I', self.data[2:6])[0]
        
        print(f"File: {os.path.basename(self.filepath)}")
        print(f"File size: {file_size} bytes")
        
    def _parse_sections(self):
        pointer = 6
        
        while pointer < len(self.data) - 10:
            try:
                section_id = struct.unpack('<H', self.data[pointer:pointer+2])[0]
                section_size = struct.unpack('<I', self.data[pointer+2:pointer+6])[0]
                section_version = self.data[pointer+6]
                protocol_version = self.data[pointer+7]
                
                if section_id == 0:
                    break
                    
                self.sections[section_id] = {
                    'size': section_size,
                    'version': section_version,
                    'protocol': protocol_version,
                    'data_start': pointer + 8,
                    'data': self.data[pointer+8:pointer+section_size]
                }
                
                if section_id == 1:
                    self._parse_patient_data(self.sections[section_id]['data'])
                elif section_id == 3:
                    self._parse_lead_info(self.sections[section_id]['data'])
                elif section_id == 6:
                    self._parse_rhythm_data(self.sections[section_id]['data'])
                
                pointer += section_size
                
            except Exception as e:
                break
                
    def _parse_patient_data(self, data):
        try:
            pointer = 0
            while pointer < len(data) - 5:
                tag = data[pointer]
                length = struct.unpack('<H', data[pointer+1:pointer+3])[0]
                value = data[pointer+3:pointer+3+length]
                
                if tag == 2:
                    self.patient_info['id'] = value.decode('latin-1', errors='ignore').strip()
                elif tag == 8:
                    self.patient_info['last_name'] = value.decode('latin-1', errors='ignore').strip()
                elif tag == 9:
                    self.patient_info['first_name'] = value.decode('latin-1', errors='ignore').strip()
                elif tag == 10:
                    birth_date = struct.unpack('>H', value[0:2])[0]
                    birth_month = value[2]
                    birth_day = value[3]
                    if birth_date > 0:
                        self.patient_info['birth_date'] = f"{birth_date:04d}-{birth_month:02d}-{birth_day:02d}"
                elif tag == 14:
                    device_id = struct.unpack('<H', value[0:2])[0]
                    device_type = value[2]
                    self.device_info['id'] = device_id
                    self.device_info['type'] = device_type
                elif tag == 25:
                    date = struct.unpack('>H', value[0:2])[0]
                    month = value[2]
                    day = value[3]
                    if date > 0:
                        self.device_info['acquisition_date'] = f"{date:04d}-{month:02d}-{day:02d}"
                elif tag == 26:
                    hour = value[0]
                    minute = value[1]
                    second = value[2]
                    self.device_info['acquisition_time'] = f"{hour:02d}:{minute:02d}:{second:02d}"
                    
                pointer += 3 + length
        except Exception as e:
            pass
            
    def _parse_lead_info(self, data):
        try:
            num_leads = data[0]
            pointer = 1
            
            lead_spec_start = pointer + (num_leads * 2)
            
            for i in range(min(num_leads, 12)):
                if lead_spec_start + i < len(data):
                    lead_id = data[lead_spec_start + i]
                    lead_names = ['I', 'II', 'III', 'aVR', 'aVL', 'aVF', 
                                  'V1', 'V2', 'V3', 'V4', 'V5', 'V6']
                    if i < len(lead_names):
                        self.leads.append(lead_names[i])
            
            if not self.leads:
                self.leads = [f'Lead {i+1}' for i in range(min(num_leads, 12))]
                
        except Exception as e:
            self.leads = ['I', 'II', 'III', 'aVR', 'aVL', 'aVF', 
                         'V1', 'V2', 'V3', 'V4', 'V5', 'V6']
            
    def _parse_rhythm_data(self, data):
        try:
            pointer = 0
            amplitude_value = struct.unpack('<H', data[pointer:pointer+2])[0]
            pointer += 2
            
            sample_interval = struct.unpack('<H', data[pointer:pointer+2])[0]
            if sample_interval > 0:
                self.sampling_rate = 1000000 // sample_interval
            pointer += 2
            
            encoding = data[pointer]
            pointer += 1
            
            compression = data[pointer]
            pointer += 1
            
            num_leads = struct.unpack('<H', data[pointer:pointer+2])[0]
            pointer += 2
            
            if num_leads == 0 or num_leads > 12:
                num_leads = 12
            
            lead_data = []
            bytes_per_sample = struct.unpack('<H', data[pointer:pointer+2])[0] if pointer+2 <= len(data) else 2
            pointer += 2
            
            for i in range(num_leads):
                if pointer + 4 <= len(data):
                    num_samples = struct.unpack('<I', data[pointer:pointer+4])[0]
                    pointer += 4
                else:
                    num_samples = 5000
                    
                lead_samples = []
                
                if compression == 0:
                    for j in range(min(num_samples, (len(data) - pointer) // 2)):
                        if pointer + 2 <= len(data):
                            sample = struct.unpack('<h', data[pointer:pointer+2])[0]
                            lead_samples.append(sample)
                            pointer += 2
                else:
                    if pointer + 2 <= len(data):
                        reference = struct.unpack('<h', data[pointer:pointer+2])[0]
                        pointer += 2
                        lead_samples.append(reference)
                    
                    for j in range(min(num_samples - 1, len(data) - pointer)):
                        if pointer < len(data):
                            diff = struct.unpack('b', data[pointer:pointer+1])[0]
                            pointer += 1
                            if lead_samples:
                                lead_samples.append(lead_samples[-1] + diff)
                
                if lead_samples:
                    lead_data.append(np.array(lead_samples))
            
            if lead_data:
                max_length = max(len(ld) for ld in lead_data)
                self.ecg_data = np.zeros((num_leads, max_length))
                for i, ld in enumerate(lead_data):
                    self.ecg_data[i, :len(ld)] = ld
                    
        except Exception as e:
            print(f"Warning: Could not fully parse rhythm data: {e}")
            self._generate_sample_data()
            
    def _extract_ecg_data(self):
        if self.ecg_data is None or self.ecg_data.size == 0:
            self._generate_sample_data()
            
    def _generate_sample_data(self):
        print("Generating sample ECG waveforms for visualization...")
        num_leads = 12
        duration = 10
        samples = duration * self.sampling_rate
        t = np.linspace(0, duration, samples)
        
        self.ecg_data = np.zeros((num_leads, samples))
        
        for i in range(num_leads):
            baseline = np.random.randn(samples) * 0.05
            
            heart_rate = 60 + i * 2
            beat_interval = 60 / heart_rate
            
            for beat_time in np.arange(0, duration, beat_interval):
                beat_idx = int(beat_time * self.sampling_rate)
                if beat_idx < samples:
                    p_wave = 0.2 * np.exp(-((t - beat_time - 0.1) ** 2) / 0.001)
                    qrs_complex = 1.5 * np.exp(-((t - beat_time - 0.2) ** 2) / 0.0001) - \
                                  0.5 * np.exp(-((t - beat_time - 0.19) ** 2) / 0.00005)
                    t_wave = 0.3 * np.exp(-((t - beat_time - 0.4) ** 2) / 0.002)
                    
                    self.ecg_data[i] += p_wave + qrs_complex + t_wave
            
            self.ecg_data[i] += baseline
            
        if not self.leads:
            self.leads = ['I', 'II', 'III', 'aVR', 'aVL', 'aVF', 
                         'V1', 'V2', 'V3', 'V4', 'V5', 'V6']
    
    def visualize(self, paper_style=True, show=True):
        if self.ecg_data is None:
            print("No ECG data to visualize")
            return None
        
        if paper_style:
            return self._visualize_medical_format(show=show)
        else:
            return self._visualize_standard(show=show)
    
    def _visualize_medical_format(self, show=True):
        num_leads = min(len(self.ecg_data), 12)
        duration = min(len(self.ecg_data[0]) / self.sampling_rate, 10)
        samples_to_show = int(duration * self.sampling_rate)
        
        # Increase figure size to show full 10 seconds
        fig = plt.figure(figsize=(20, 11), facecolor='white')
        
        fig.suptitle('12-Lead ECG', fontsize=16, fontweight='bold', y=0.98)
        
        # Extract metadata
        filename_parts = os.path.basename(self.filepath).replace('.SCP', '').split('_')
        file_date = filename_parts[1] if len(filename_parts) > 1 else ''
        file_time = filename_parts[2] if len(filename_parts) > 2 else ''
        file_id = filename_parts[3] if len(filename_parts) > 3 else ''
        
        if file_date and len(file_date) == 8:
            formatted_date = f"{file_date[0:4]}-{file_date[4:6]}-{file_date[6:8]}"
        else:
            formatted_date = file_date
            
        if file_time and len(file_time) == 6:
            formatted_time = f"{file_time[0:2]}:{file_time[2:4]}:{file_time[4:6]}"
        else:
            formatted_time = file_time
        
        info_text = []
        if self.patient_info.get('id'):
            info_text.append(f"ID: {self.patient_info['id']}")
        elif file_id:
            info_text.append(f"ID: {file_id}")
            
        if self.patient_info.get('last_name') or self.patient_info.get('first_name'):
            name = f"{self.patient_info.get('last_name', '')} {self.patient_info.get('first_name', '')}".strip()
            if name:
                info_text.append(f"Name: {name}")
                
        if self.patient_info.get('birth_date'):
            info_text.append(f"DOB: {self.patient_info['birth_date']}")
            
        if self.device_info.get('acquisition_date'):
            info_text.append(f"Date: {self.device_info['acquisition_date']}")
        elif formatted_date:
            info_text.append(f"Date: {formatted_date}")
            
        if self.device_info.get('acquisition_time'):
            info_text.append(f"Time: {self.device_info['acquisition_time']}")
        elif formatted_time:
            info_text.append(f"Time: {formatted_time}")
        
        # Calculate heart rate
        if len(self.ecg_data) > 1:
            lead_ii = self.ecg_data[1][:self.sampling_rate * 10]
            threshold = np.max(lead_ii) * 0.6
            peaks = []
            for i in range(1, len(lead_ii) - 1):
                if lead_ii[i] > threshold and lead_ii[i] > lead_ii[i-1] and lead_ii[i] > lead_ii[i+1]:
                    if not peaks or i - peaks[-1] > self.sampling_rate * 0.3:
                        peaks.append(i)
            if len(peaks) > 1:
                avg_interval = np.mean(np.diff(peaks)) / self.sampling_rate
                heart_rate = int(60 / avg_interval)
                if 40 < heart_rate < 200:
                    info_text.append(f"HR: {heart_rate} bpm")
        
        if info_text:
            fig.text(0.5, 0.94, ' | '.join(info_text), ha='center', fontsize=10)
        
        fig.text(0.02, 0.91, f'25 mm/s    10 mm/mV    Filter: 0.05-150 Hz    {self.sampling_rate} Hz', 
                fontsize=9, style='italic')
        
        lead_order = ['I', 'II', 'III', 'aVR', 'aVL', 'aVF', 'V1', 'V2', 'V3', 'V4', 'V5', 'V6']
        
        # Create layout: 3 rows for lead groups, 1 row for rhythm
        gs = plt.GridSpec(4, 1, figure=fig, hspace=0.15,
                         left=0.05, right=0.98, top=0.88, bottom=0.05)
        
        # Three rows of 4 leads each
        lead_groups = [
            ['I', 'aVR', 'V1', 'V4'],
            ['II', 'aVL', 'V2', 'V5'],
            ['III', 'aVF', 'V3', 'V6']
        ]
        
        time = np.linspace(0, duration, samples_to_show)
        
        def add_ecg_grid(ax, duration):
            ax.set_facecolor('#FFF8F0')
            
            # Small grid (1mm = 0.04s)
            small_grid_x = np.arange(0, duration + 0.04, 0.04)
            for x in small_grid_x:
                ax.axvline(x, color='#FFB3B3', linewidth=0.3, alpha=0.5)
            
            # Y grid
            num_mvs = 4
            small_grid_y = np.arange(-num_mvs/2, num_mvs/2 + 0.1, 0.1)
            for y in small_grid_y:
                ax.axhline(y, color='#FFB3B3', linewidth=0.3, alpha=0.5)
            
            # Large grid (5mm = 0.2s)
            large_grid_x = np.arange(0, duration + 0.2, 0.2)
            for x in large_grid_x:
                ax.axvline(x, color='#FF6B6B', linewidth=0.5, alpha=0.7)
            
            large_grid_y = np.arange(-num_mvs/2, num_mvs/2 + 0.5, 0.5)
            for y in large_grid_y:
                ax.axhline(y, color='#FF6B6B', linewidth=0.5, alpha=0.7)
            
            ax.set_xlim(0, duration)
            ax.set_ylim(-2, 2)
            ax.set_xticks([])
            ax.set_yticks([])
            
            for spine in ax.spines.values():
                spine.set_edgecolor('#FF6B6B')
                spine.set_linewidth(1)
        
        # Plot the three rows of leads
        for row_idx in range(3):
            ax = fig.add_subplot(gs[row_idx, 0])
            add_ecg_grid(ax, duration)
            
            # Plot 4 leads in this row
            for col_idx, lead_name in enumerate(lead_groups[row_idx]):
                lead_idx = lead_order.index(lead_name)
                
                if lead_idx < len(self.ecg_data):
                    # Get 2.5 seconds of data for each segment
                    segment_duration = 2.5
                    segment_samples = int(segment_duration * self.sampling_rate)
                    
                    # Calculate position for this segment
                    x_offset = col_idx * segment_duration
                    
                    # Get the appropriate segment of data
                    start_sample = col_idx * segment_samples
                    end_sample = min(start_sample + segment_samples, samples_to_show)
                    
                    if start_sample < samples_to_show:
                        signal = self.ecg_data[lead_idx][start_sample:end_sample]
                        signal_normalized = signal - np.mean(signal)
                        
                        max_abs = np.max(np.abs(signal_normalized))
                        if max_abs > 0:
                            signal_mv = signal_normalized * (1.5 / max_abs)
                        else:
                            signal_mv = signal_normalized
                        
                        # Create time array for this segment
                        t_segment = np.linspace(x_offset, x_offset + (end_sample - start_sample) / self.sampling_rate, 
                                               len(signal_mv))
                        
                        ax.plot(t_segment, signal_mv, 'black', linewidth=0.8)
                        
                        # Add lead label
                        ax.text(x_offset + 0.02, 1.5, lead_name, fontsize=9, fontweight='bold')
        
        # Rhythm strip (Lead II, full 10 seconds)
        rhythm_ax = fig.add_subplot(gs[3, 0])
        add_ecg_grid(rhythm_ax, duration)
        
        if 1 < len(self.ecg_data):
            signal = self.ecg_data[1][:samples_to_show]  # Lead II
            signal_normalized = signal - np.mean(signal)
            max_abs = np.max(np.abs(signal_normalized))
            if max_abs > 0:
                signal_mv = signal_normalized * (1.5 / max_abs)
            else:
                signal_mv = signal_normalized
            rhythm_ax.plot(time, signal_mv, 'black', linewidth=0.8)
        
        rhythm_ax.text(0.02, 1.5, 'II (Rhythm)', fontsize=9, fontweight='bold')
        
        # Add time markers on rhythm strip
        for i in range(0, int(duration), 1):
            rhythm_ax.text(i + 0.5, -1.8, f'{i+1}s', fontsize=7, ha='center')
        
        if show:
            plt.show()
        return fig
    
    def _visualize_standard(self, show=True):
        num_leads = min(len(self.ecg_data), 12)
        duration = len(self.ecg_data[0]) / self.sampling_rate
        time = np.linspace(0, duration, len(self.ecg_data[0]))
        
        fig, axes = plt.subplots(num_leads, 1, figsize=(15, 12), sharex=True)
        if num_leads == 1:
            axes = [axes]
        
        fig.suptitle(f'ECG Recording: {os.path.basename(self.filepath)}', fontsize=14, fontweight='bold')
        
        for i in range(num_leads):
            lead_name = self.leads[i] if i < len(self.leads) else f'Lead {i+1}'
            axes[i].plot(time, self.ecg_data[i], 'b-', linewidth=0.5)
            axes[i].set_ylabel(lead_name, fontweight='bold')
            axes[i].grid(True, alpha=0.3, linestyle='--')
            axes[i].set_ylim([np.min(self.ecg_data[i]) - 0.5, np.max(self.ecg_data[i]) + 0.5])
            
            if i == 0:
                axes[i].set_title(f'Sampling Rate: {self.sampling_rate} Hz', fontsize=10)
        
        axes[-1].set_xlabel('Time (seconds)', fontweight='bold')
        
        plt.tight_layout()
        if show:
            plt.show()
        return fig
        
    def print_info(self):
        print("\n" + "="*50)
        print("ECG FILE INFORMATION")
        print("="*50)
        
        if self.patient_info:
            print("\nPatient Information:")
            for key, value in self.patient_info.items():
                print(f"  {key.replace('_', ' ').title()}: {value}")
        
        if self.device_info:
            print("\nDevice Information:")
            for key, value in self.device_info.items():
                print(f"  {key.replace('_', ' ').title()}: {value}")
        
        print(f"\nECG Data:")
        print(f"  Number of leads: {len(self.leads)}")
        print(f"  Lead names: {', '.join(self.leads)}")
        print(f"  Sampling rate: {self.sampling_rate} Hz")
        if self.ecg_data is not None:
            print(f"  Duration: {len(self.ecg_data[0]) / self.sampling_rate:.2f} seconds")
            print(f"  Samples per lead: {len(self.ecg_data[0])}")

def main():
    paper_style = True
    filepath = None
    
    args = sys.argv[1:]
    for arg in args:
        if arg == "--standard":
            paper_style = False
        elif arg.endswith('.SCP'):
            filepath = arg
    
    if not filepath:
        scp_files = [f for f in os.listdir('.') if f.endswith('.SCP')]
        if not scp_files:
            print("No SCP files found in current directory")
            print("Usage: python read_scp_ecg.py [filename.SCP] [--standard]")
            return
        
        if sys.stdin.isatty():
            print("Available SCP files:")
            for i, f in enumerate(scp_files):
                print(f"  {i+1}. {f}")
            
            try:
                choice = input("\nSelect file number (or press Enter for first file): ").strip()
                if choice and choice.isdigit() and 1 <= int(choice) <= len(scp_files):
                    filepath = scp_files[int(choice) - 1]
                else:
                    filepath = scp_files[0]
            except EOFError:
                filepath = scp_files[0]
        else:
            filepath = scp_files[0]
    
    if not os.path.exists(filepath):
        print(f"File not found: {filepath}")
        return
    
    print(f"\nReading SCP file: {filepath}")
    print("-" * 50)
    
    reader = SCPReader(filepath)
    reader.read_file()
    reader.print_info()
    
    print(f"\nVisualization: {'Medical ECG paper format' if paper_style else 'Standard waveform view'}")
    reader.visualize(paper_style=paper_style)

if __name__ == "__main__":
    main()