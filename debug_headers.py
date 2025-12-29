#!/usr/bin/env python3
"""
Debug Headers Script
Creates a simple Flask app to see exactly what headers nginx is sending
"""

from flask import Flask, request, jsonify
import os

app = Flask(__name__)

@app.route('/debug-headers', methods=['GET', 'POST'])
def debug_headers():
    """Debug endpoint to see all headers exactly as received"""
    
    headers_dict = {}
    for header_name, header_value in request.headers:
        headers_dict[header_name] = repr(header_value)  # Use repr to see exact formatting
    
    auth_header = request.headers.get('Authorization', 'NOT_FOUND')
    
    return jsonify({
        'all_headers': headers_dict,
        'authorization_header': repr(auth_header),
        'authorization_length': len(auth_header) if auth_header != 'NOT_FOUND' else 0,
        'authorization_ends_with_space': auth_header.endswith(' ') if auth_header != 'NOT_FOUND' else False,
        'authorization_raw_bytes': [ord(c) for c in auth_header] if auth_header != 'NOT_FOUND' else [],
        'request_method': request.method,
        'remote_addr': request.remote_addr,
        'x_forwarded_for': request.headers.get('X-Forwarded-For', 'NOT_FOUND')
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=True)