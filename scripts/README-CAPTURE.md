Capture request/response to PNG + HAR
=====================================

1) Install requirements (recommended in a virtualenv):

   pip install -r scripts/requirements-capture.txt

2) Run the script to capture the request and response as a PNG + HAR file:

   python scripts/capture_request_response.py --url http://localhost:8000/login --method GET --output evidence.png

3) The script will output two files:
   - `evidence.png` - visual screenshot of request/response
   - `evidence.har` - HAR file (HTTP Archive format) for security scanners and dev tools

Output files
------------
Both files contain the same request/response data:
- **PNG** – Easy to attach to reports and view inline
- **HAR** – Importable into Postman, browser DevTools, or security scanners like OWASP ZAP

Notes
-----
- The script sends a real HTTP request to the provided URL. Make sure your backend is running and accessible.
- Use `--data` for POST/PUT bodies: `--data '{"key":"value"}'`
- Files are saved in the workspace root by default
