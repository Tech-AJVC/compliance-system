#!/bin/bash
set -e

# Deployment script for Compliance Reminder Cron Job
# Uses your existing EKS cluster and ECR registry

echo "🚀 Deploying Compliance Reminder Cron Job to EKS"
echo "================================================="

# Configuration for your AWS setup
AWS_REGION="ap-south-1"
AWS_ACCOUNT_ID="148761677341"
ECR_REGISTRY="${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"
IMAGE_NAME="compliance-reminder"
TAG="${1:-latest}"
NAMESPACE="default"

echo "📦 Building Docker image..."
docker build -t ${ECR_REGISTRY}/${IMAGE_NAME}:${TAG} .

echo "🔐 Logging into ECR..."
aws ecr get-login-password --region ${AWS_REGION} | docker login --username AWS --password-stdin ${ECR_REGISTRY}

echo "📤 Pushing Docker image to ECR..."
# Create repository if it doesn't exist
aws ecr describe-repositories --repository-names ${IMAGE_NAME} --region ${AWS_REGION} || \
aws ecr create-repository --repository-name ${IMAGE_NAME} --region ${AWS_REGION}

docker push ${ECR_REGISTRY}/${IMAGE_NAME}:${TAG}

echo "⚙️  Updating Kubernetes CronJob configuration..."
# Update the image tag in the CronJob configuration
sed -i.bak "s|image: .*|image: ${ECR_REGISTRY}/${IMAGE_NAME}:${TAG}|g" k8s-cronjob.yaml

echo "🔑 Setting up kubectl context for EKS..."
aws eks update-kubeconfig --region ${AWS_REGION} --name compliance-cluster

echo "🚀 Applying Kubernetes configuration..."
kubectl apply -f k8s-cronjob.yaml -n ${NAMESPACE}

echo "✅ Deployment completed successfully!"
echo ""
echo "📋 Useful commands:"
echo "  View CronJob: kubectl get cronjobs -n ${NAMESPACE}"
echo "  View Jobs: kubectl get jobs -n ${NAMESPACE} | grep compliance-reminder"
echo "  View latest job logs: kubectl logs \$(kubectl get jobs -n ${NAMESPACE} -l app=compliance-reminder-service --sort-by=.metadata.creationTimestamp -o jsonpath='{.items[-1].metadata.name}') -n ${NAMESPACE}"
echo "  Delete CronJob: kubectl delete cronjob compliance-reminder-service -n ${NAMESPACE}"
echo ""
echo "⏰ The cron job is scheduled to run daily at 3:30 AM IST (22:00 UTC)"
echo "🎯 Database: compliance-db.c10u466skyz9.ap-south-1.rds.amazonaws.com"
echo "📧 Gmail: Using existing service account credentials"