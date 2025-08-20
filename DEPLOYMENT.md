# Deployment Guide

This guide covers deploying the Object Detection Worker to AWS EKS using GitHub Actions.

## Prerequisites

1. **AWS Account** with appropriate permissions
2. **EKS Cluster** already created
3. **ECR Repository** for container images
4. **Redis instance** (ElastiCache recommended)
5. **S3 bucket** for image storage
6. **GitHub repository** with Actions enabled

## Setup Instructions

### 1. AWS Infrastructure Setup

#### Create ECR Repository
```bash
aws ecr create-repository \
    --repository-name object-detection-worker \
    --region us-east-1
```

#### Create EKS Cluster (if not exists)
```bash
eksctl create cluster \
    --name object-detection-cluster \
    --region us-east-1 \
    --node-type t3.medium \
    --nodes 3 \
    --nodes-min 2 \
    --nodes-max 10 \
    --managed
```

#### Create IAM Role for Service Account (IRSA)
```bash
# Create OIDC provider
eksctl utils associate-iam-oidc-provider \
    --cluster object-detection-cluster \
    --approve

# Create IAM role and service account
eksctl create iamserviceaccount \
    --name object-detection-worker \
    --namespace object-detection \
    --cluster object-detection-cluster \
    --attach-policy-arn arn:aws:iam::aws:policy/AmazonS3FullAccess \
    --approve \
    --override-existing-serviceaccounts
```

### 2. GitHub Secrets Configuration

Configure the following secrets in your GitHub repository (Settings → Secrets and variables → Actions):

#### Required Secrets
- `AWS_ACCESS_KEY_ID`: AWS access key for GitHub Actions
- `AWS_SECRET_ACCESS_KEY`: AWS secret key for GitHub Actions

#### Optional Secrets (if not using IRSA)
- `AWS_ACCESS_KEY_ID_WORKER`: For the worker pods
- `AWS_SECRET_ACCESS_KEY_WORKER`: For the worker pods

### 3. Update Configuration

#### Update GitHub Actions workflow
Edit `.github/workflows/deploy.yml`:
- Set `EKS_CLUSTER_NAME` to your cluster name
- Set `ECR_REPOSITORY` to your repository name
- Update `AWS_REGION` if different

#### Update Kubernetes manifests
Edit `k8s/serviceaccount.yml`:
- Replace `ACCOUNT_ID` with your AWS account ID
- Update the IAM role ARN

Edit `k8s/secret.yml`:
- Update `REDIS_URL` with your Redis connection string (base64 encoded)

#### Update ConfigMap
Edit `k8s/configmap.yml`:
- Set correct values for your environment

### 4. Deploy Redis (if needed)

#### Using ElastiCache
```bash
aws elasticache create-cache-cluster \
    --cache-cluster-id object-detection-redis \
    --engine redis \
    --cache-node-type cache.t3.micro \
    --num-cache-nodes 1
```

#### Or deploy in-cluster
```yaml
# Add to k8s/ directory
apiVersion: apps/v1
kind: Deployment
metadata:
  name: redis
  namespace: object-detection
spec:
  selector:
    matchLabels:
      app: redis
  template:
    metadata:
      labels:
        app: redis
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
---
apiVersion: v1
kind: Service
metadata:
  name: redis-service
  namespace: object-detection
spec:
  selector:
    app: redis
  ports:
  - port: 6379
    targetPort: 6379
```

### 5. Initial Deployment

#### Manual deployment (first time)
```bash
# Update kubectl context
aws eks update-kubeconfig --region us-east-1 --name object-detection-cluster

# Create namespace
kubectl apply -f k8s/namespace.yml

# Apply all manifests
kubectl apply -f k8s/
```

#### Build and push initial image
```bash
# Get ECR login
aws ecr get-login-password --region us-east-1 | docker login --username AWS --password-stdin <account-id>.dkr.ecr.us-east-1.amazonaws.com

# Build and push
docker build -t <account-id>.dkr.ecr.us-east-1.amazonaws.com/object-detection-worker:latest .
docker push <account-id>.dkr.ecr.us-east-1.amazonaws.com/object-detection-worker:latest
```

### 6. GitHub Actions Deployment

Once configured, pushes to the `main` branch will automatically:
1. Run tests and security scans
2. Build and push Docker images to ECR
3. Deploy to EKS cluster
4. Verify deployment success

## Monitoring and Maintenance

### View deployment status
```bash
kubectl get pods -n object-detection
kubectl logs -f deployment/object-detection-worker -n object-detection
```

### Scale deployment
```bash
kubectl scale deployment object-detection-worker --replicas=5 -n object-detection
```

### Update configuration
```bash
kubectl edit configmap object-detection-config -n object-detection
kubectl rollout restart deployment/object-detection-worker -n object-detection
```

## Troubleshooting

### Common Issues

1. **Image pull errors**: Verify ECR permissions and repository exists
2. **Pod crashes**: Check logs and resource limits
3. **Network issues**: Verify security groups and network policies
4. **IRSA issues**: Verify service account annotations and IAM role trust policy

### Useful Commands
```bash
# Check events
kubectl get events -n object-detection --sort-by='.lastTimestamp'

# Describe pod
kubectl describe pod <pod-name> -n object-detection

# View logs
kubectl logs <pod-name> -n object-detection -f

# Check HPA status
kubectl get hpa -n object-detection

# Test connectivity
kubectl run test-pod --image=busybox -it --rm -- sh
```

## Security Considerations

- Use IAM roles for service accounts (IRSA) instead of embedding credentials
- Implement network policies to restrict pod-to-pod communication
- Regularly scan images for vulnerabilities
- Use resource limits and quotas
- Enable pod security standards
- Rotate credentials regularly
- Monitor access logs and audit trails