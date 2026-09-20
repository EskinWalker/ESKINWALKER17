ESKINWALKER

ESKINWALKER is a Python CLI tool for managing and checking authorized local HTTP endpoints.

Features

- Local endpoint management
- Add and remove endpoints
- Search endpoints
- Count endpoints
- HTTP status checking
- Concurrent scanning
- Scan result reports
- Terminal-based interface
- Local and private IP validation

Requirements

- Python 3
- requests

Installation

pip install -r requirements.txt

Run

python eskinwalker.py

Configuration

Create a file named:

cameras.txt

Add your authorized local endpoints, one per line:

http://192.168.1.10:80
http://192.168.1.20:8080

Commands

1 - List
2 - Count
3 - Search
4 - Scan
5 - Add
6 - Remove
7 - System Info
8 - Help
9 - Clear
0 - Exit

Scan Status

- ONLINE - an HTTP response was received
- OFFLINE - the endpoint did not respond successfully
- SKIPPED - the target is outside the supported local/private scope

ONLINE does not necessarily mean that a camera video stream is available.

Safety

Use ESKINWALKER only with devices, systems, and networks that you own or are explicitly authorized to test.
