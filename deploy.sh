#!/bin/bash
# ============================================================
#  Customer360 MCP — One-shot deploy to AWS App Runner
#  Run this IN AWS CloudShell (already authenticated)
# ============================================================

AWS_REGION="us-east-1"
AWS_ACCOUNT="1374516611241"
REPO_NAME="customer360-mcp"
IMAGE_TAG="latest"

ECR_URI="$AWS_ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com/$REPO_NAME:$IMAGE_TAG"

echo "=== Step 1: Create ECR repository ==="
aws ecr create-repository \
  --repository-name $REPO_NAME \
  --region $AWS_REGION \
  2>/dev/null || echo "(repo already exists, continuing)"

echo "=== Step 2: Login Docker to ECR ==="
aws ecr get-login-password --region $AWS_REGION | \
  docker login --username AWS --password-stdin \
  "$AWS_ACCOUNT.dkr.ecr.$AWS_REGION.amazonaws.com"

echo "=== Step 3: Build Docker image ==="
docker build -t $REPO_NAME .

echo "=== Step 4: Tag image ==="
docker tag $REPO_NAME:latest $ECR_URI

echo "=== Step 5: Push to ECR ==="
docker push $ECR_URI

echo ""
echo "✅ Image pushed: $ECR_URI"
echo ""
echo "=== Next: Create App Runner service ==="
echo "Go to AWS Console → App Runner → Create service"
echo "  Source: Container registry → Amazon ECR"
echo "  Image URI: $ECR_URI"
echo "  Port: 8000"
echo "  CPU: 0.25 vCPU  |  Memory: 0.5 GB"
echo ""
echo "After deploy, copy the App Runner URL and paste it"
echo "into index.html where it says REPLACE_WITH_APP_RUNNER_URL"
