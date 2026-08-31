#!/usr/bin/env python3
"""Subagent to count all lines in data/*.txt files"""

import subprocess
import os

def main():
    # Find all .txt files in data/ directory
    txt_files = subprocess.run(['find', 'data', '-name', '*.txt'], 
                              capture_output=True, text=True).stdout.split('\n')
    
    total_lines = 0
    for filename in txt_files:
        if filename.strip():
            file_count = subprocess.run(
                ['wc', '-l', filename],
                stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL,
                text=True
            ).stdout.strip()
            total_lines += int(file_count)
    
    print(f"Total lines in {txt_files}: {total_lines}")

if __name__ == "__main__":
    main()
