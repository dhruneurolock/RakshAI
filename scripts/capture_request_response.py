#!/usr/bin/env python3
"""
Send an HTTP request, capture the raw request and response, and render them to a PNG image + HAR file.

Usage:
  python scripts/capture_request_response.py --url http://localhost:8000/login --method GET --output evidence.png

This script requires `requests` and `Pillow`.
Outputs: 
  - evidence.png (visual screenshot)
  - evidence.har (HAR file for dev tools / security scanners)
"""
import argparse
import json
import textwrap
from datetime import datetime
from io import BytesIO

import requests
from PIL import Image, ImageDraw, ImageFont


def build_request_text(prep):
    lines = []
    # use path_url when available to show path+query
    path = getattr(prep, 'path_url', prep.url)
    lines.append(f"{prep.method} {path} HTTP/1.1")
    for k, v in prep.headers.items():
        lines.append(f"{k}: {v}")
    lines.append("")
    body = prep.body or b""
    if isinstance(body, bytes):
        try:
            body_text = body.decode("utf-8")
        except Exception:
            body_text = repr(body)
    else:
        body_text = str(body)
    if body_text:
        lines.append(body_text)
    return "\n".join(lines)


def build_response_text(resp):
    lines = []
    # resp.raw.version may not be present; default to 1.1
    version = '1.1'
    try:
        if hasattr(resp.raw, 'version') and resp.raw.version:
            version = str(resp.raw.version)
    except Exception:
        pass
    lines.append(f"HTTP/{version} {resp.status_code} {resp.reason}")
    for k, v in resp.headers.items():
        lines.append(f"{k}: {v}")
    lines.append("")
    try:
        body_text = resp.text
    except Exception:
        body_text = repr(resp.content)
    if body_text:
        lines.append(body_text)
    return "\n".join(lines)


def build_har_file(prep, resp):
    """Build HAR (HTTP Archive) structure for request/response."""
    req_headers = [{"name": k, "value": v} for k, v in prep.headers.items()]
    resp_headers = [{"name": k, "value": v} for k, v in resp.headers.items()]
    
    # Request body
    req_body = ""
    if prep.body:
        if isinstance(prep.body, bytes):
            try:
                req_body = prep.body.decode("utf-8")
            except Exception:
                req_body = repr(prep.body)
        else:
            req_body = str(prep.body)
    
    # Response body
    resp_body = ""
    try:
        resp_body = resp.text
    except Exception:
        resp_body = repr(resp.content)
    
    # Build HAR structure
    now = datetime.utcnow()
    har = {
        "log": {
            "version": "1.2",
            "creator": {"name": "capture_request_response.py", "version": "1.0"},
            "entries": [
                {
                    "startedDateTime": now.isoformat() + "Z",
                    "time": f"{resp.elapsed.total_seconds():.3f}ms",
                    "request": {
                        "method": prep.method,
                        "url": prep.url,
                        "httpVersion": "HTTP/1.1",
                        "headers": req_headers,
                        "queryString": [],
                        "cookies": [],
                        "headersSize": -1,
                        "bodySize": len(req_body) if req_body else 0,
                        "postData": {
                            "mimeType": "application/x-www-form-urlencoded",
                            "text": req_body
                        } if req_body else None
                    },
                    "response": {
                        "status": resp.status_code,
                        "statusText": resp.reason,
                        "httpVersion": "HTTP/1.1",
                        "headers": resp_headers,
                        "cookies": [],
                        "content": {
                            "size": len(resp_body),
                            "mimeType": resp.headers.get("Content-Type", "application/octet-stream"),
                            "text": resp_body
                        },
                        "redirectURL": "",
                        "headersSize": -1,
                        "bodySize": len(resp_body)
                    },
                    "cache": {},
                    "timings": {
                        "wait": resp.elapsed.total_seconds() * 1000,
                        "receive": 0
                    }
                }
            ]
        }
    }
    return har



def render_text_to_image(title, text, width=1200, bg=(255, 255, 255), fg=(0, 0, 0)):
    font = ImageFont.load_default()
    margin = 12
    max_chars_per_line = 120
    wrapped = []
    for paragraph in text.splitlines():
        if not paragraph:
            wrapped.append("")
            continue
        wrapped.extend(textwrap.wrap(paragraph, max_chars_per_line))

    # compute line height using a temporary drawing context (works for all Pillow font types)
    tmp_img = Image.new("RGB", (10, 10))
    tmp_draw = ImageDraw.Draw(tmp_img)
    try:
        # Pillow >= 8.0
        bbox = tmp_draw.textbbox((0, 0), "A", font=font)
        h = bbox[3] - bbox[1]
    except Exception:
        try:
            # fallback to font.getbbox
            bbox = font.getbbox("A")
            h = bbox[3] - bbox[1]
        except Exception:
            # last resort: try getsize (older Pillow)
            try:
                h = font.getsize("A")[1]
            except Exception:
                h = 14
    line_height = h + 2

    img_h = max(200, (len(wrapped) + 2) * line_height + margin * 2 + 30)
    img = Image.new("RGB", (width, img_h), color=bg)
    draw = ImageDraw.Draw(img)
    y = margin
    draw.text((margin, y), title, fill=fg, font=font)
    y += line_height + 6
    for line in wrapped:
        draw.text((margin, y), line, fill=fg, font=font)
        y += line_height
    return img


def main():
    p = argparse.ArgumentParser(description="Capture request+response and render to PNG + HAR")
    p.add_argument("--url", required=True)
    p.add_argument("--method", default="GET")
    p.add_argument("--data", default=None)
    p.add_argument("--output", default="evidence.png")
    p.add_argument("--width", type=int, default=1200)
    args = p.parse_args()

    session = requests.Session()
    req = requests.Request(method=args.method.upper(), url=args.url, data=args.data)
    prep = session.prepare_request(req)

    request_text = build_request_text(prep)

    # send the request (stream=False so resp.text is available)
    resp = session.send(prep)

    response_text = build_response_text(resp)

    # Generate PNG
    req_img = render_text_to_image("Request", request_text, width=args.width)
    resp_img = render_text_to_image("Response", response_text, width=args.width)

    total_h = req_img.height + resp_img.height
    out = Image.new("RGB", (args.width, total_h + 20), color=(255, 255, 255))
    out.paste(req_img, (0, 0))
    out.paste(resp_img, (0, req_img.height + 10))
    out.save(args.output)
    print(f"✓ Saved PNG evidence to {args.output}")

    # Generate HAR file
    har = build_har_file(prep, resp)
    har_output = args.output.rsplit(".", 1)[0] + ".har"
    with open(har_output, "w") as f:
        json.dump(har, f, indent=2)
    print(f"✓ Saved HAR file to {har_output}")


if __name__ == "__main__":
    main()
