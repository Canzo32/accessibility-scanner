import boto3
import urllib.request
import json
import os
import re
from datetime import datetime

def check_accessibility(html, url):
    issues = []

    # Check for images missing alt text
    img_tags = re.findall(r'<img[^>]*>', html, re.IGNORECASE)
    for img in img_tags:
        if 'alt=' not in img.lower():
            issues.append(f"Image missing alt text: {img[:80]}")

    # Check for empty links
    empty_links = re.findall(r'<a[^>]*>\s*</a>', html, re.IGNORECASE)
    for link in empty_links:
        issues.append(f"Empty link found: {link[:80]}")

    # Check for missing page title
    if '<title>' not in html.lower():
        issues.append("Page is missing a <title> tag")

    # Check for missing language attribute
    if '<html' in html.lower() and 'lang=' not in html.lower():
        issues.append("HTML tag is missing lang attribute")

    return issues

def lambda_handler(event, context):
    # URL to scan - can be passed in event or use default
    url = event.get('url', 'https://example.com')
    scan_time = datetime.utcnow().isoformat()

    print(f"Scanning URL: {url}")

    # Fetch the webpage
    try:
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'Mozilla/5.0 AccessibilityScanner/1.0'}
        )
        with urllib.request.urlopen(req, timeout=10) as response:
            html = response.read().decode('utf-8', errors='ignore')
        status = 'success'
    except Exception as e:
        html = ''
        status = f'fetch_error: {str(e)}'
        print(f"Error fetching URL: {e}")

    # Run accessibility checks
    issues = check_accessibility(html, url) if html else ['Could not fetch page']

    # Build report
    report = {
        'url': url,
        'scanTime': scan_time,
        'status': status,
        'issueCount': len(issues),
        'issues': issues
    }

    # Save full report to S3
    s3 = boto3.client('s3')
    s3_key = f"reports/{scan_time[:10]}/{url.replace('https://','').replace('http://','').replace('/','_')}.json"
    s3.put_object(
        Bucket=os.environ['S3_BUCKET'],
        Key=s3_key,
        Body=json.dumps(report, indent=2),
        ContentType='application/json'
    )
    print(f"Report saved to S3: {s3_key}")

    # Save summary to DynamoDB
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])
    table.put_item(Item={
        'url': url,
        'scanTime': scan_time,
        'status': status,
        'issueCount': str(len(issues)),
        'issues': issues
    })
    print("Results saved to DynamoDB")

    # Send email summary via SNS
    sns = boto3.client('sns')
    subject = f"Accessibility Scan: {len(issues)} issue(s) found on {url[:50]}"
    message = f"""
Accessibility Scan Report
=========================
URL: {url}
Scan Time: {scan_time}
Status: {status}
Issues Found: {len(issues)}

Issues:
"""
    for i, issue in enumerate(issues, 1):
        message += f"{i}. {issue}\n"

    message += f"\nFull report saved to S3: {s3_key}"

    sns.publish(
        TopicArn=os.environ['SNS_TOPIC_ARN'],
        Subject=subject,
        Message=message
    )
    print("Email summary sent via SNS")

    return {
        'statusCode': 200,
        'body': json.dumps(report)
    }
