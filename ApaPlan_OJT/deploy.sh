#!/bin/bash
# Exit immediately if a command exits with a non-zero status.
set -e

# Define the image name
IMAGE_NAME="europe-west1-docker.pkg.dev/apaplan-6a422/apaplan-repo/apaplan"

# 1. Build the Docker image
echo "Building Docker image..."
docker build --platform linux/amd64 -t $IMAGE_NAME .

# 2. Push the Docker image to Google Artifact Registry
echo "Pushing Docker image to Artifact Registry..."
docker push $IMAGE_NAME

# 3. Deploy the new image to Cloud Run
echo "Deploying to Cloud Run..."
gcloud run deploy auth \
  --image $IMAGE_NAME \
  --region europe-west1 \
  --platform managed \
  --allow-unauthenticated \
  --cpu 1 \
  --memory 1Gi \
  --service-account firebase-adminsdk-fbsvc@apaplan-6a422.iam.gserviceaccount.com \
  --set-secrets=FIREBASE_WEB_API_KEY=FIREBASE_WEB_API_KEY:latest,SECRET_KEY=SECRET_KEY:latest,AUTH_DOMAIN=AUTH_DOMAIN:latest,PROJECT_ID=PROJECT_ID:latest,STORAGE_BUCKET=STORAGE_BUCKET:latest,MESSAGING_SENDER_ID=MESSAGING_SENDER_ID:latest,APP_ID=APP_ID:latest,MEASUREMENT_ID=MEASUREMENT_ID:latest,GOOGLE_MAPS_API_KEY=GOOGLE_MAPS_API_KEY:latest,GOOGLE_MAP_ID=GOOGLE_MAP_ID:latest

echo "Deployment successful!"
