import json
import time
import urllib.error
import urllib.request
from datetime import datetime

import boto3

s3 = boto3.client("s3")

WEBSITES = [
    "https://www.google.com",
    "https://www.amazon.com",
]

S3_BUCKET = "your-s3-bucket-name"
S3_PREFIX = "website-health-checks"


def check_website(url, timeout=5):
    start = time.time()
    result = {
        "url": url,
        "available": False,
        "status_code": None,
        "response_time_ms": None,
        "error": None
    }
    try:
        req = urllib.request.Request(url, method="GET")
        with urllib.request.urlopen(req, timeout=timeout) as response:
            result["status_code"] = response.getcode()
            result["available"] = 200 <= response.getcode() < 400
    except urllib.error.HTTPError as e:
        result["status_code"] = e.code
        result["error"] = str(e)
    except urllib.error.URLError as e:
        result["error"] = str(e.reason)
    except Exception as e:
        result["error"] = str(e)
    finally:
        result["response_time_ms"] = int((time.time() - start) * 1000)
    return result


def lambda_handler(event, context):
    results = []
    timestamp = datetime.utcnow().isoformat()
    for site in WEBSITES:
        results.append(check_website(site))
    payload = {
        "timestamp": timestamp,
        "checks": results
    }
    time_suffix = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
    key = f"{S3_PREFIX}/healthcheck-{time_suffix}.json"
    s3.put_object(
        Bucket=S3_BUCKET,
        Key=key,
        Body=json.dumps(payload, indent=2),
        ContentType="application/json"
    )
    return {
        "statusCode": 200,
        "body": json.dumps({
            "message": "Health check completed",
            "s3_key": key,
            "results": results
        })
    }
