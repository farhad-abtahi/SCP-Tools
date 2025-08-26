#!/usr/bin/env python3
"""
Log Viewer for SCP-ECG Tools

Author: Farhad Abtahi

View and analyze logs with filtering and summary statistics.
"""

import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
import argparse
from collections import defaultdict


def parse_log_line(line):
    """Parse a log line to extract timestamp, level, and message"""
    try:
        parts = line.split(' | ')
        if len(parts) >= 3:
            timestamp = parts[0].strip()
            level = parts[1].strip()
            message = ' | '.join(parts[2:]).strip()
            return {
                'timestamp': timestamp,
                'level': level,
                'message': message
            }
    except:
        pass
    return None


def read_logs(log_dir='logs', days_back=7, activity_filter=None, level_filter=None):
    """Read log files from the specified directory"""
    log_path = Path(log_dir)
    if not log_path.exists():
        print(f"Log directory not found: {log_dir}")
        return []
    
    logs = []
    cutoff_date = datetime.now() - timedelta(days=days_back)
    
    # Read activity logs
    activity_dir = log_path / 'activities'
    if activity_dir.exists():
        for log_file in activity_dir.glob('*.log'):
            # Filter by activity if specified
            if activity_filter and activity_filter not in log_file.stem:
                continue
            
            # Check file date
            file_date_str = log_file.stem.split('_')[-1]
            try:
                if len(file_date_str) == 8:  # YYYYMMDD format
                    file_date = datetime.strptime(file_date_str, '%Y%m%d')
                    if file_date < cutoff_date:
                        continue
            except:
                pass
            
            # Read file
            with open(log_file, 'r') as f:
                for line in f:
                    parsed = parse_log_line(line)
                    if parsed:
                        if level_filter and parsed['level'] != level_filter.upper():
                            continue
                        parsed['file'] = log_file.name
                        parsed['activity'] = log_file.stem.split('_')[0]
                        logs.append(parsed)
    
    # Read main logs
    for log_file in log_path.glob('scp_tools_*.log'):
        file_date_str = log_file.stem.split('_')[-1]
        try:
            if len(file_date_str) == 8:
                file_date = datetime.strptime(file_date_str, '%Y%m%d')
                if file_date < cutoff_date:
                    continue
        except:
            pass
        
        with open(log_file, 'r') as f:
            for line in f:
                parsed = parse_log_line(line)
                if parsed:
                    if level_filter and parsed['level'] != level_filter.upper():
                        continue
                    parsed['file'] = log_file.name
                    parsed['activity'] = 'main'
                    logs.append(parsed)
    
    return logs


def generate_summary(logs):
    """Generate summary statistics from logs"""
    summary = {
        'total': len(logs),
        'by_level': defaultdict(int),
        'by_activity': defaultdict(int),
        'success_count': 0,
        'failure_count': 0,
        'errors': [],
        'warnings': []
    }
    
    for log in logs:
        summary['by_level'][log['level']] += 1
        summary['by_activity'][log['activity']] += 1
        
        if 'SUCCESS:' in log['message']:
            summary['success_count'] += 1
        elif 'FAILED:' in log['message']:
            summary['failure_count'] += 1
        
        if log['level'] == 'ERROR':
            summary['errors'].append(log)
        elif log['level'] == 'WARNING':
            summary['warnings'].append(log)
    
    return summary


def display_logs(logs, verbose=False):
    """Display logs in a formatted way"""
    if not logs:
        print("No logs found matching criteria")
        return
    
    print(f"\nFound {len(logs)} log entries")
    print("="*80)
    
    if verbose:
        # Show all logs
        for log in logs:
            print(f"{log['timestamp']} | {log['level']:8} | {log['activity']:10} | {log['message']}")
    else:
        # Show summary
        summary = generate_summary(logs)
        
        print("\nSUMMARY")
        print("-"*40)
        print(f"Total entries: {summary['total']}")
        print(f"Successful operations: {summary['success_count']}")
        print(f"Failed operations: {summary['failure_count']}")
        
        print("\nBy Level:")
        for level, count in summary['by_level'].items():
            print(f"  {level:8}: {count}")
        
        print("\nBy Activity:")
        for activity, count in summary['by_activity'].items():
            print(f"  {activity:10}: {count}")
        
        if summary['errors']:
            print(f"\nRecent Errors ({len(summary['errors'])} total):")
            for error in summary['errors'][-5:]:  # Show last 5 errors
                print(f"  {error['timestamp']} - {error['message'][:60]}...")
        
        if summary['warnings']:
            print(f"\nRecent Warnings ({len(summary['warnings'])} total):")
            for warning in summary['warnings'][-5:]:  # Show last 5 warnings
                print(f"  {warning['timestamp']} - {warning['message'][:60]}...")
        
        # Calculate success rate
        total_ops = summary['success_count'] + summary['failure_count']
        if total_ops > 0:
            success_rate = (summary['success_count'] / total_ops) * 100
            print(f"\nSuccess Rate: {success_rate:.1f}%")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description='View and analyze SCP-ECG Tools logs',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  View summary of all logs from last 7 days:
    python view_logs.py
    
  View all logs from today:
    python view_logs.py --days 1 --verbose
    
  View only errors:
    python view_logs.py --level error --verbose
    
  View anonymization activities:
    python view_logs.py --activity anonymize
    
  View detailed logs from last 30 days:
    python view_logs.py --days 30 --verbose
        """
    )
    
    parser.add_argument('--days', type=int, default=7,
                       help='Number of days back to look (default: 7)')
    parser.add_argument('--activity', choices=['read', 'anonymize', 'visualize', 'main'],
                       help='Filter by activity type')
    parser.add_argument('--level', choices=['info', 'warning', 'error'],
                       help='Filter by log level')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Show detailed logs instead of summary')
    parser.add_argument('--log-dir', default='logs',
                       help='Log directory path (default: logs)')
    
    args = parser.parse_args()
    
    # Read logs
    logs = read_logs(
        log_dir=args.log_dir,
        days_back=args.days,
        activity_filter=args.activity,
        level_filter=args.level
    )
    
    # Display
    display_logs(logs, verbose=args.verbose)


if __name__ == '__main__':
    main()