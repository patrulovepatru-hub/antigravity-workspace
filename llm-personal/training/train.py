#!/usr/bin/env python3
"""
Vertex AI Fine-tuning Script
Uploads data and starts fine-tuning job for Llama 3
"""

import os
import subprocess
from google.cloud import storage
from google.cloud import aiplatform
from pathlib import Path

# Configuration
PROJECT_ID = "gen-lang-client-0988614926"
LOCATION = "us-central1"
BUCKET_NAME = "antigravity-llm-data"

# Paths
SCRIPT_DIR = Path(__file__).parent
DATA_DIR = SCRIPT_DIR.parent / "data"
TRAINING_DATA = DATA_DIR / "training_data.jsonl"

# Set credentials
CREDENTIALS_PATH = SCRIPT_DIR.parent.parent / "pipeline" / "keys" / "service-account.json"
os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = str(CREDENTIALS_PATH)

def create_bucket_if_not_exists():
    """Create GCS bucket for training data"""
    client = storage.Client(project=PROJECT_ID)
    
    try:
        bucket = client.get_bucket(BUCKET_NAME)
        print(f"✓ Bucket {BUCKET_NAME} exists")
    except:
        bucket = client.create_bucket(BUCKET_NAME, location=LOCATION)
        print(f"✓ Created bucket {BUCKET_NAME}")
    
    return bucket

def upload_training_data(bucket):
    """Upload training data to GCS"""
    blob = bucket.blob("training_data.jsonl")
    blob.upload_from_filename(str(TRAINING_DATA))
    
    gcs_uri = f"gs://{BUCKET_NAME}/training_data.jsonl"
    print(f"✓ Uploaded training data to {gcs_uri}")
    return gcs_uri

def start_finetuning(gcs_uri):
    """Start fine-tuning job on Vertex AI"""
    aiplatform.init(project=PROJECT_ID, location=LOCATION)
    
    # For Gemini/Llama fine-tuning, we use the tuning API
    print("\n🚀 Starting fine-tuning job...")
    print(f"   Base model: meta/llama3-8b-instruct")
    print(f"   Training data: {gcs_uri}")
    print(f"   Location: {LOCATION}")
    
    # Note: Actual fine-tuning requires specific API calls
    # This is a placeholder for the actual implementation
    print("\n⚠️  Fine-tuning requires Vertex AI Generative AI API")
    print("   Run this command in Cloud Shell with proper permissions:")
    print(f"""
    gcloud ai models tune \\
        --project={PROJECT_ID} \\
        --region={LOCATION} \\
        --base-model=meta/llama3-8b-instruct \\
        --training-data={gcs_uri} \\
        --tuned-model-display-name=antigravity-personal-v1
    """)

def main():
    print("=" * 60)
    print("VERTEX AI FINE-TUNING SETUP")
    print("=" * 60)
    
    # Check training data exists
    if not TRAINING_DATA.exists():
        print(f"❌ Training data not found: {TRAINING_DATA}")
        print("   Run collect_data.py first")
        return
    
    # Get file stats
    size_mb = TRAINING_DATA.stat().st_size / (1024 * 1024)
    with open(TRAINING_DATA) as f:
        num_samples = sum(1 for _ in f)
    
    print(f"\n📦 Training data:")
    print(f"   File: {TRAINING_DATA}")
    print(f"   Size: {size_mb:.2f} MB")
    print(f"   Samples: {num_samples}")
    
    # Create bucket and upload
    print("\n☁️  Uploading to Google Cloud Storage...")
    bucket = create_bucket_if_not_exists()
    gcs_uri = upload_training_data(bucket)
    
    # Start fine-tuning
    start_finetuning(gcs_uri)
    
    print("\n" + "=" * 60)
    print("✅ Setup complete!")
    print("=" * 60)

if __name__ == "__main__":
    main()
