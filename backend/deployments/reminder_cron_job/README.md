# Compliance Reminder Cron Job

This deployment contains a Kubernetes CronJob that runs daily to send automated reminders for compliance activities.

## Features

### 1. Capital Call Reminders
- **Trigger**: Runs on the 7th of each quarter (January, April, July, October)
- **Recipient**: Fund Manager (aviral@ajuniorvc.com)
- **Content**: 
  - List of active funds requiring attention
  - Quarter information (e.g., Q1'25, Q2'25)
  - Link to compliance dashboard
- **Purpose**: Reminds to initiate quarterly drawdowns

### 2. Task Due Date Reminders
- **Trigger**: Runs daily, sends reminders 3 days before task due dates
- **Recipient**: Task assignees (currently routed to Fund Manager)
- **Content**:
  - List of upcoming tasks with details
  - Priority levels and current status
  - Link to task management dashboard
- **Purpose**: Ensures tasks are completed on time

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Kubernetes    │    │   Reminder       │    │   Compliance    │
│   CronJob       │───▶│   Service        │───▶│   Database      │
│   (Daily 9AM)   │    │   Container      │    │                 │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
                       ┌──────────────────┐
                       │   Gmail API      │
                       │   (Send Emails)  │
                       └──────────────────┘
```

## Files Structure

```
reminder_cron_job/
├── reminder_service.py      # Main Python script with reminder logic
├── requirements.txt         # Python dependencies
├── Dockerfile              # Container configuration
├── k8s-cronjob.yaml        # Kubernetes CronJob configuration
├── deploy.sh               # Deployment script
└── README.md               # This documentation
```

## Installation & Deployment

### Prerequisites

1. **Kubernetes cluster** with CronJob support
2. **Docker registry** access for pushing images
3. **Database access** to compliance system database
4. **Gmail service account** credentials for sending emails

### Step 1: Prepare Secrets

Create the required Kubernetes secrets:

```bash
# Database connection secret
kubectl create secret generic compliance-secrets \
  --from-literal=database-url='postgresql://user:password@host:port/database' \
  -n default

# Gmail credentials secret (download service account JSON from Google Cloud Console)
kubectl create secret generic gmail-credentials \
  --from-file=credentials.json=path/to/gmail-service-account.json \
  -n default
```

### Step 2: Configure Docker Registry

Update the `deploy.sh` script with your Docker registry:

```bash
# Edit deploy.sh
DOCKER_REGISTRY="your-registry.com/compliance"  # Replace with your registry
```

### Step 3: Deploy

```bash
cd backend/deployments/reminder_cron_job
./deploy.sh latest
```

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | PostgreSQL connection string | From secret |
| `GMAIL_CREDENTIALS_PATH` | Path to Gmail service account JSON | `/app/secrets/gmail-credentials.json` |
| `ENVIRONMENT` | Application environment | `production` |
| `LOG_LEVEL` | Logging level | `INFO` |

### Schedule Configuration

The CronJob is configured to run daily at 9:00 AM UTC. To change this, modify the `schedule` field in `k8s-cronjob.yaml`:

```yaml
spec:
  schedule: "0 9 * * *"  # Daily at 9:00 AM UTC
  # schedule: "0 */6 * * *"  # Every 6 hours
  # schedule: "0 9 * * 1"    # Weekly on Mondays at 9:00 AM
```

### Email Recipients

Currently configured to send all emails to `aviral@ajuniorvc.com`. To customize:

1. **Capital Call Reminders**: Update the `to_email` parameter in `capital_call_reminder()` function
2. **Task Reminders**: Enhance the assignee lookup logic in `task_due_date_reminder()` function

## Monitoring & Troubleshooting

### View CronJob Status

```bash
# List all CronJobs
kubectl get cronjobs

# Get detailed information about the reminder CronJob
kubectl describe cronjob compliance-reminder-service

# View recent jobs
kubectl get jobs | grep compliance-reminder
```

### View Logs

```bash
# Get the latest job name
JOB_NAME=$(kubectl get jobs -l app=compliance-reminder-service --sort-by=.metadata.creationTimestamp -o jsonpath='{.items[-1].metadata.name}')

# View job logs
kubectl logs job/$JOB_NAME

# Follow live logs (if job is running)
kubectl logs job/$JOB_NAME -f
```

### Manual Execution

To test the reminder service manually:

```bash
# Create a one-time job from the CronJob
kubectl create job manual-reminder-test --from=cronjob/compliance-reminder-service

# View the manual job logs
kubectl logs job/manual-reminder-test
```

### Common Issues

1. **Secret not found**: Ensure `compliance-secrets` and `gmail-credentials` secrets exist
2. **Database connection failed**: Verify the database URL in the secret
3. **Gmail API errors**: Check the service account credentials and permissions
4. **Image pull errors**: Verify the Docker registry URL and authentication

## Email Templates

### Capital Call Reminder Email

**Subject**: `Capital Call Reminder - Q1'25`

**Content**:
- Quarter information
- List of active funds
- Action items
- Dashboard link: https://compliance-system.netlify.app/dashboard

### Task Reminder Email

**Subject**: `Task Reminder - 3 tasks due on 2025-08-15`

**Content**:
- List of upcoming tasks with priorities
- Task details and descriptions
- Dashboard link: https://compliance-system.netlify.app/dashboard/task

## Development

### Local Testing

To test the reminder service locally:

```bash
cd backend/deployments/reminder_cron_job

# Install dependencies
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://localhost/compliance"
export GMAIL_CREDENTIALS_PATH="/path/to/credentials.json"

# Run the service
python reminder_service.py
```

### Adding New Reminder Types

1. Create a new function in `reminder_service.py`
2. Add the function call to `run_daily_reminders()`
3. Update email templates as needed
4. Test locally before deploying

## Resource Usage

- **CPU Request**: 100m (0.1 CPU core)
- **Memory Request**: 256Mi
- **CPU Limit**: 500m (0.5 CPU core)  
- **Memory Limit**: 512Mi

The service typically runs for 1-3 minutes and then terminates until the next scheduled execution.

## Security

- Runs as non-root user (`appuser`)
- Uses Kubernetes secrets for sensitive data
- Read-only access to Gmail credentials
- Database access through secure connection string
- Container filesystem is not writable except for logs

## Backup & Recovery

The reminder service is stateless - it only reads from the database and sends emails. No backup is required for the service itself. Ensure that:

1. Database backups include the `compliance_tasks` and `fund_details` tables
2. Gmail service account credentials are backed up securely
3. Kubernetes secret definitions are version controlled