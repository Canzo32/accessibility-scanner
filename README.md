# Serverless Accessibility Scanner

## Problem
Websites often have accessibility issues that go unnoticed.
This tool automatically scans a webpage daily and reports issues.

## Architecture
EventBridge Scheduler → Lambda → DynamoDB + S3 + SNS

## Services and Why I Chose Them
- EventBridge Scheduler: serverless scheduling, no EC2 needed
- Lambda (Python 3.12): run code without managing servers
- DynamoDB: fast NoSQL storage for per-URL scan results
- S3: cheap object storage for full JSON reports
- SNS: simple email notifications for scan summaries
- IAM: least-privilege role for Lambda

## What It Checks
- Images missing alt text
- Empty anchor links
- Missing page title tag
- Missing HTML lang attribute

## Cost
Runs entirely within AWS Free Tier at one scan per day.

## What I Would Improve
- Add WCAG 2.1 AA checks
- Accept multiple URLs via API Gateway
- Build a CloudWatch dashboard
- Add CloudFormation template for one-click deploy
