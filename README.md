
# Emotion Detection with Streamlit + AWS Backend

## Overview

This system captures webcam input via Streamlit Cloud and detects facial emotions using AWS Rekognition. Emotion logs are stored in DynamoDB, and alerts are triggered via SNS when specific thresholds are met (e.g., repeated “SAD” detections).

---

## Table of Contents

- [Frontend: Streamlit App](#frontend-streamlit-app)
- [Backend: AWS Architecture](#backend-aws-architecture)
- [Deployment Guide](#deployment-guide)
- [Alerting and Notifications](#alerting-and-notifications)
- [Optional Enhancements](#optional-enhancements)

---

## Frontend: Streamlit App

### Purpose

- Captures webcam frames automatically using `streamlit-webrtc`
- Sends images to S3 and invokes a Lambda function
- Displays emotion in real time

### Required Secrets

```toml
[aws]
aws_access_key_id = "YOUR_KEY"
aws_secret_access_key = "YOUR_SECRET"
region_name = "ap-southeast-1"
s3_bucket = "your-s3-bucket"
lambda_name = "DetectEmotionFromFace"
```

### Key Features

- Auto webcam capture every ~5 seconds
- Logs emotion results tied to `user_id`
- Visual display of top emotion and confidence

---

## Backend: AWS Architecture

| Service      | Purpose                                                                 |
|--------------|-------------------------------------------------------------------------|
| Lambda       | Calls Rekognition, logs emotion, sends alerts                           |
| S3           | Stores uploaded face images                                             |
| Rekognition  | Detects emotions in facial expressions                                  |
| DynamoDB     | Logs each emotion per user (`user_id`, `timestamp`, `emotion`)          |
| SNS          | Sends alert if threshold met (≥3 SAD detections in 1 day)               |
| IAM Role     | Lambda execution role with all necessary permissions                    |
| IAM User     | Used by Streamlit app for S3, Lambda, SNS access                        |

---

## Deployment Guide

### Step 1: Prepare the Project Repository

```bash
git init
git remote add origin https://github.com/YOUR_USERNAME/emotion-detector-updated.git
git add .
git commit -m "Initial commit"
git push -u origin main
```

### Step 2: Deploy AWS Infrastructure via CloudFormation

Save the full CloudFormation YAML as `rekognition-emotion.yaml`, then run:

```bash
aws cloudformation deploy \
  --template-file rekognition-emotion.yaml \
  --stack-name EmotionDetectionStack \
  --capabilities CAPABILITY_NAMED_IAM
```

This creates Lambda, IAM roles, S3 permissions, DynamoDB, SNS, and the IAM user.

### Step 3: Subscribe to SNS Email Alerts

- In AWS Console, go to **SNS > Topics > EmotionAlertTopic**
- Click **Create subscription**
- Choose **Protocol**: `email`, and enter the email address
- Confirm the subscription from your inbox

### Step 4: Configure IAM Credentials for Streamlit

- Go to IAM > Users > `streamlit-app-user`
- Create **Access Key** (programmatic access)
- Copy the Access Key ID and Secret Access Key

### Step 5: Deploy the Streamlit App to Streamlit Cloud

- Go to https://streamlit.io/cloud
- Click **New app** and connect your GitHub repo
- Set:
  - **Main file**: `app.py`
  - **Branch**: `main`
- Add secrets under **App settings > Secrets**:

```toml
[aws]
aws_access_key_id = "YOUR_ACCESS_KEY"
aws_secret_access_key = "YOUR_SECRET_KEY"
region_name = "ap-southeast-1"
s3_bucket = "your-s3-bucket"
lambda_name = "DetectEmotionFromFace"
```

### Step 6: Test the App

- Enter a `user_id` on the UI
- Webcam auto-captures a frame every ~5 seconds
- Emotion result is shown live
- If `"SAD"` appears 3+ times per day → SNS email alert triggered

---

## Alerting and Notifications

- SNS topic: `EmotionAlertTopic`
- Automatically triggers when:
  - Same user triggers `SAD` emotion ≥ 3 times today
- Sends email notification
- You can subscribe via:
  - Email
  - SMS (optional)
  - Lambda/Slack integrations (advanced)

---

## Optional Enhancements

- CloudWatch dashboard for emotion trends
- Notification logs in DynamoDB
- API Gateway for mobile integration
- Slack, SMS, or EventBridge integrations
