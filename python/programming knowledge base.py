# The `yield` keyword in Python is used to create generators, which are particularly useful for reading files efficiently. Here's how to use it and why it's beneficial:

## Basic File Reading with Yield


def read_file_lines(filename: str) -> Generator[str, None, None]:
    """
    Generator function that yields lines from a file one at a time.
    Memory efficient - doesn't load entire file into memory.
    """
    try:
        with open(filename, 'r', encoding='utf-8') as file:
            for line in file:
                yield line.strip()  # Remove trailing newline
    except FileNotFoundError:
        print(f"File {filename} not found")
        return
    except IOError as e:
        print(f"Error reading file: {e}")
        return

# Usage
for line in read_file_lines('large_file.txt'):
    print(line)
    # Process each line individually - memory efficient


## Advanced File Processing with Yield


from typing import Generator, Dict, Any
import json

def read_json_objects(filename: str) -> Generator[Dict[str, Any], None, None]:
    """
    Read JSON objects from a file line by line (JSONL format).
    Useful for processing large datasets without loading everything into memory.
    """
    with open(filename, 'r', encoding='utf-8') as file:
        for line_number, line in enumerate(file, 1):
            try:
                if line.strip():  # Skip empty lines
                    yield json.loads(line)
            except json.JSONDecodeError as e:
                print(f"Invalid JSON on line {line_number}: {e}")
                continue

def read_csv_chunks(filename: str, chunk_size: int = 1000) -> Generator[List[str], None, None]:
    """
    Read CSV file in chunks - useful for processing large CSV files.
    """
    import csv
    
    with open(filename, 'r', encoding='utf-8') as file:
        reader = csv.reader(file)
        header = next(reader)  # Read header first
        
        chunk = []
        for row in reader:
            chunk.append(row)
            if len(chunk) >= chunk_size:
                yield chunk
                chunk = []
        
        # Yield remaining rows
        if chunk:
            yield chunk


## How Yield Works Internally

# When you use `yield`, Python creates a **generator object** that implements the iterator protocol:


def number_generator():
    print("Starting generator")
    yield 1
    print("After first yield")
    yield 2
    print("After second yield")
    yield 3
    print("Generator finished")

# This creates a generator object, doesn't execute the function yet
gen = number_generator()
print(type(gen))  # <class 'generator'>

# Each next() call executes until the next yield
print(next(gen))  # Prints: "Starting generator" then "1"
print(next(gen))  # Prints: "After first yield" then "2"
print(next(gen))  # Prints: "After second yield" then "3"


## Real-World Use Cases

### 1. Log File Analysis (DevOps/Monitoring)

def parse_nginx_logs(log_file: str) -> Generator[Dict[str, str], None, None]:
    """
    Parse nginx access logs line by line - perfect for analyzing GB-sized log files.
    Memory usage stays constant regardless of file size.
    """
    import re
    
    # Nginx log format pattern
    pattern = r'(\S+) - - \[([^\]]+)\] "(\S+) (\S+) (\S+)" (\d+) (\d+)'
    
    with open(log_file, 'r') as file:
        for line in file:
            match = re.match(pattern, line)
            if match:
                yield {
                    'ip': match.group(1),
                    'timestamp': match.group(2),
                    'method': match.group(3),
                    'url': match.group(4),
                    'status': int(match.group(6)),
                    'size': int(match.group(7))
                }

# Usage - analyze logs without loading entire file
error_ips = set()
for log_entry in parse_nginx_logs('/var/log/nginx/access.log'):
    if log_entry['status'] >= 400:
        error_ips.add(log_entry['ip'])


### 2. Database Export Processing

def process_user_export(export_file: str) -> Generator[Dict[str, Any], None, None]:
    """
    Process user data export - common in GDPR compliance scenarios.
    Yields processed user records one at a time.
    """
    with open(export_file, 'r') as file:
        for line in file:
            try:
                user_data = json.loads(line)
                # Process/sanitize data
                processed_user = {
                    'id': user_data.get('id'),
                    'email': user_data.get('email', '').lower(),
                    'created_at': user_data.get('created_at'),
                    'is_active': user_data.get('status') == 'active'
                }
                yield processed_user
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Skipping invalid record: {e}")
                continue


### 3. API Data Streaming

def stream_api_data(api_responses_file: str) -> Generator[Dict[str, Any], None, None]:
    """
    Stream API responses from a file - useful for testing or replay scenarios.
    """
    with open(api_responses_file, 'r') as file:
        for line in file:
            try:
                response = json.loads(line)
                # Simulate API response processing
                yield {
                    'data': response.get('data', {}),
                    'status': response.get('status', 200),
                    'timestamp': response.get('timestamp')
                }
            except json.JSONDecodeError:
                continue


## Key Benefits of Using Yield for File Reading

# 1. **Memory Efficiency**: Only one line/chunk is in memory at a time
# 2. **Lazy Evaluation**: Data is processed on-demand
# 3. **Composability**: Can chain generators together
# 4. **Early Termination**: Can stop processing anytime with `break`
# 5. **Stateful Processing**: Generator maintains state between yields

## Security Considerations


import os
from pathlib import Path

def secure_file_reader(filename: str, max_file_size: int = 100 * 1024 * 1024) -> Generator[str, None, None]:
    """
    Secure file reader with size limits and path validation.
    Prevents directory traversal and limits memory usage.
    """
    # Validate file path - prevent directory traversal
    file_path = Path(filename).resolve()
    if not str(file_path).startswith(os.getcwd()):
        raise ValueError("Invalid file path - directory traversal detected")
    
    # Check file size before processing
    if file_path.stat().st_size > max_file_size:
        raise ValueError(f"File too large: {file_path.stat().st_size} bytes")
    
    with open(file_path, 'r', encoding='utf-8') as file:
        for line in file:
            yield line.strip()


## Performance Comparison


import time
import psutil

def memory_usage_demo():
    """
    Demonstrates memory difference between reading entire file vs using generator.
    """
    
    # Method 1: Read entire file (high memory usage)
    def read_entire_file(filename: str) -> List[str]:
        with open(filename, 'r') as file:
            return file.readlines()
    
    # Method 2: Generator (low memory usage)
    def read_with_generator(filename: str) -> Generator[str, None, None]:
        with open(filename, 'r') as file:
            for line in file:
                yield line.strip()
    
    # Monitor memory usage
    process = psutil.Process()
    
    print("Memory before:", process.memory_info().rss / 1024 / 1024, "MB")
    
    # Using generator - memory stays low
    for line in read_with_generator('large_file.txt'):
        pass  # Process line
    
    print("Memory after generator:", process.memory_info().rss / 1024 / 1024, "MB")


# The `yield` approach is particularly powerful when working with large files in Django applications, data processing pipelines, or any scenario where memory efficiency is crucial. It's a fundamental pattern for building scalable Python applications.