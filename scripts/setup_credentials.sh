#!/bin/bash

# Setup Credentials Script for Ekko
# This script sets up all necessary credentials in Google Secret Manager
# for the Ekko application deployment on Google Cloud Run

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_ID="ekko-468919"
REGION="europe-west1"
SERVICE_NAME="ekko"
ENV_FILE=".env"

# Function to print colored output
print_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to show help
show_help() {
    cat << EOF
Usage: ./scripts/setup_credentials.sh [OPTIONS]

This script sets up Google Secret Manager secrets for the Ekko application.
It reads credentials from a local .env file and creates/updates them in
Google Secret Manager for use with Cloud Run.

OPTIONS:
    -h, --help          Show this help message
    -e, --env FILE      Specify custom .env file (default: .env)
    -p, --project ID    Specify GCP project ID (default: ekko-468919)
    -r, --region REGION Specify GCP region (default: europe-west1)
    -f, --force         Force update existing secrets without confirmation
    -d, --dry-run       Show what would be done without making changes
    --github            Also set up GitHub secrets (requires gh CLI)

PREREQUISITES:
    1. gcloud CLI installed and authenticated
    2. .env file with required credentials
    3. Appropriate GCP permissions (Secret Manager Admin)
    4. Service account key at ./ekko-468919-18b71c68e6b2.json (optional)

ENVIRONMENT VARIABLES REQUIRED IN .env:
    - OPENAI_API_KEY
    - PODCASTINDEX_API_KEY
    - PODCASTINDEX_API_SECRET
    - YOUTUBE_API_KEY (optional)
    - NGROK_URL (optional)
    - AUTH_TOKEN (optional)

EXAMPLE:
    # Basic usage with default settings
    ./scripts/setup_credentials.sh

    # Use custom .env file
    ./scripts/setup_credentials.sh --env .env.production

    # Dry run to see what would be created
    ./scripts/setup_credentials.sh --dry-run

    # Force update and also set GitHub secrets
    ./scripts/setup_credentials.sh --force --github

EOF
}

# Parse command line arguments
FORCE=false
DRY_RUN=false
SETUP_GITHUB=false

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -e|--env)
            ENV_FILE="$2"
            shift 2
            ;;
        -p|--project)
            PROJECT_ID="$2"
            shift 2
            ;;
        -r|--region)
            REGION="$2"
            shift 2
            ;;
        -f|--force)
            FORCE=true
            shift
            ;;
        -d|--dry-run)
            DRY_RUN=true
            shift
            ;;
        --github)
            SETUP_GITHUB=true
            shift
            ;;
        *)
            print_error "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Check if .env file exists
if [ ! -f "$ENV_FILE" ]; then
    print_error "Environment file not found: $ENV_FILE"
    print_info "Please create a .env file with required credentials"
    print_info "You can copy .env.example as a template:"
    print_info "  cp .env.example .env"
    exit 1
fi

# Load environment variables from .env file
print_info "Loading environment variables from $ENV_FILE"
source "$ENV_FILE"

# Check required environment variables
REQUIRED_VARS=(
    "OPENAI_API_KEY"
    "PODCASTINDEX_API_KEY"
    "PODCASTINDEX_API_SECRET"
)

OPTIONAL_VARS=(
    "YOUTUBE_API_KEY"
    "NGROK_URL"
    "AUTH_TOKEN"
)

# Validate required variables
MISSING_VARS=()
for var in "${REQUIRED_VARS[@]}"; do
    if [ -z "${!var}" ]; then
        MISSING_VARS+=("$var")
    fi
done

if [ ${#MISSING_VARS[@]} -ne 0 ]; then
    print_error "Missing required environment variables:"
    for var in "${MISSING_VARS[@]}"; do
        echo "  - $var"
    done
    exit 1
fi

# Check if gcloud is installed and authenticated
if ! command -v gcloud &> /dev/null; then
    print_error "gcloud CLI is not installed"
    print_info "Please install gcloud CLI: https://cloud.google.com/sdk/docs/install"
    exit 1
fi

# Set the project
print_info "Setting GCP project to $PROJECT_ID"
if [ "$DRY_RUN" = false ]; then
    gcloud config set project "$PROJECT_ID" 2>/dev/null || {
        print_error "Failed to set project. Make sure you have access to project: $PROJECT_ID"
        exit 1
    }
fi

# Check authentication
print_info "Checking GCP authentication..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    print_warning "No active GCP account found"
    print_info "Attempting to authenticate with service account key..."

    SERVICE_ACCOUNT_KEY="./ekko-468919-18b71c68e6b2.json"
    if [ -f "$SERVICE_ACCOUNT_KEY" ]; then
        if [ "$DRY_RUN" = false ]; then
            gcloud auth activate-service-account --key-file="$SERVICE_ACCOUNT_KEY"
            print_success "Authenticated with service account"
        else
            print_info "[DRY RUN] Would authenticate with service account key"
        fi
    else
        print_error "Service account key not found: $SERVICE_ACCOUNT_KEY"
        print_info "Please run: gcloud auth login"
        exit 1
    fi
fi

# Enable required APIs
print_info "Enabling required Google Cloud APIs..."
REQUIRED_APIS=(
    "secretmanager.googleapis.com"      # For Secret Manager
    "run.googleapis.com"                # For Cloud Run
    "artifactregistry.googleapis.com"   # For Artifact Registry (Docker images)
    "cloudbuild.googleapis.com"         # For Cloud Build
    "containerregistry.googleapis.com"  # For Container Registry (gcr.io)
    "iamcredentials.googleapis.com"     # For service account impersonation
)

if [ "$DRY_RUN" = false ]; then
    for api in "${REQUIRED_APIS[@]}"; do
        print_info "Enabling API: $api"
        gcloud services enable "$api" --project="$PROJECT_ID" || {
            print_warning "Could not enable $api (may already be enabled)"
        }
    done
    print_success "All required APIs enabled"
else
    print_info "[DRY RUN] Would enable the following APIs:"
    for api in "${REQUIRED_APIS[@]}"; do
        echo "  - $api"
    done
fi

# Function to create or update a secret
create_or_update_secret() {
    local secret_name=$1
    local secret_value=$2

    if [ -z "$secret_value" ]; then
        print_warning "Skipping $secret_name - no value provided"
        return
    fi

    # Check if secret exists
    if gcloud secrets describe "$secret_name" --project="$PROJECT_ID" &>/dev/null; then
        if [ "$FORCE" = true ]; then
            print_info "Updating existing secret: $secret_name"
            if [ "$DRY_RUN" = false ]; then
                echo -n "$secret_value" | gcloud secrets versions add "$secret_name" \
                    --data-file=- \
                    --project="$PROJECT_ID"
            else
                print_info "[DRY RUN] Would update secret: $secret_name"
            fi
        else
            print_warning "Secret already exists: $secret_name (use --force to update)"
        fi
    else
        print_info "Creating new secret: $secret_name"
        if [ "$DRY_RUN" = false ]; then
            echo -n "$secret_value" | gcloud secrets create "$secret_name" \
                --data-file=- \
                --replication-policy="automatic" \
                --project="$PROJECT_ID"
        else
            print_info "[DRY RUN] Would create secret: $secret_name"
        fi
    fi
}

# Create/update secrets in Google Secret Manager
print_info "Setting up Google Secret Manager secrets..."

# Required secrets
create_or_update_secret "openai-api-key" "$OPENAI_API_KEY"
create_or_update_secret "podcastindex-api-key" "$PODCASTINDEX_API_KEY"
create_or_update_secret "podcastindex-api-secret" "$PODCASTINDEX_API_SECRET"

# Optional secrets
create_or_update_secret "youtube-api-key" "$YOUTUBE_API_KEY"
create_or_update_secret "ngrok-url" "$NGROK_URL"
create_or_update_secret "auth-token" "$AUTH_TOKEN"

# Grant Cloud Run service account access to secrets
print_info "Granting Cloud Run service account access to secrets..."

# Determine the service account
DEPLOY_SERVICE_ACCOUNT="ekko-deploy@${PROJECT_ID}.iam.gserviceaccount.com"
SERVICE_ACCOUNT="${SERVICE_NAME}@${PROJECT_ID}.iam.gserviceaccount.com"
COMPUTE_SERVICE_ACCOUNT="${PROJECT_ID}-compute@developer.gserviceaccount.com"

# Check which service account to use
if gcloud iam service-accounts describe "$DEPLOY_SERVICE_ACCOUNT" --project="$PROJECT_ID" &>/dev/null; then
    print_info "Using deployment service account: $DEPLOY_SERVICE_ACCOUNT"
    SERVICE_ACCOUNT="$DEPLOY_SERVICE_ACCOUNT"

    # Check if we need to grant additional permissions to the deployment service account
    # This requires Owner or IAM Admin role on the project
    print_info "Checking deployment service account permissions..."

    CURRENT_ACCOUNT=$(gcloud auth list --filter=status:ACTIVE --format="value(account)")

    # Only attempt to grant permissions if running as a user account (not as the service account itself)
    if [[ "$CURRENT_ACCOUNT" != *"iam.gserviceaccount.com" ]]; then
        print_info "Ensuring deployment service account has necessary permissions..."

        # Required roles for the deployment service account
        REQUIRED_ROLES=(
            "roles/run.admin"                    # Deploy to Cloud Run
            "roles/secretmanager.admin"          # Create and manage secrets
            "roles/artifactregistry.writer"      # Push Docker images
            "roles/storage.admin"                # Access GCS for Container Registry
        )

        if [ "$DRY_RUN" = false ]; then
            for role in "${REQUIRED_ROLES[@]}"; do
                print_info "Granting role: $role"
                gcloud projects add-iam-policy-binding "$PROJECT_ID" \
                    --member="serviceAccount:${DEPLOY_SERVICE_ACCOUNT}" \
                    --role="$role" \
                    --condition=None &>/dev/null || {
                        print_warning "Could not grant $role (may already have it or insufficient permissions)"
                    }
            done
        else
            print_info "[DRY RUN] Would grant the following roles to $DEPLOY_SERVICE_ACCOUNT:"
            for role in "${REQUIRED_ROLES[@]}"; do
                echo "  - $role"
            done
        fi
    else
        print_info "Running as service account, skipping permission grants"
    fi
elif ! gcloud iam service-accounts describe "$SERVICE_ACCOUNT" --project="$PROJECT_ID" &>/dev/null; then
    print_warning "Service account $SERVICE_ACCOUNT not found, using compute service account"
    SERVICE_ACCOUNT="$COMPUTE_SERVICE_ACCOUNT"
fi

# List of all secrets to grant access to
ALL_SECRETS=(
    "openai-api-key"
    "podcastindex-api-key"
    "podcastindex-api-secret"
    "youtube-api-key"
    "ngrok-url"
    "auth-token"
)

# Grant access to each secret
for secret in "${ALL_SECRETS[@]}"; do
    # Only grant access if the secret exists
    if gcloud secrets describe "$secret" --project="$PROJECT_ID" &>/dev/null; then
        print_info "Granting access to secret: $secret"
        if [ "$DRY_RUN" = false ]; then
            gcloud secrets add-iam-policy-binding "$secret" \
                --member="serviceAccount:${SERVICE_ACCOUNT}" \
                --role="roles/secretmanager.secretAccessor" \
                --project="$PROJECT_ID" &>/dev/null || {
                    print_warning "Could not grant access to $secret (may already have access)"
                }
        else
            print_info "[DRY RUN] Would grant access to secret: $secret"
        fi
    fi
done

# Set up GitHub secrets if requested
if [ "$SETUP_GITHUB" = true ]; then
    print_info "Setting up GitHub secrets..."

    if ! command -v gh &> /dev/null; then
        print_error "GitHub CLI (gh) is not installed"
        print_info "Please install gh: https://cli.github.com/"
    else
        if [ "$DRY_RUN" = false ]; then
            # Set GitHub secrets
            gh secret set OPENAI_API_KEY --body "$OPENAI_API_KEY" || print_warning "Failed to set OPENAI_API_KEY"
            gh secret set PODCASTINDEX_API_KEY --body "$PODCASTINDEX_API_KEY" || print_warning "Failed to set PODCASTINDEX_API_KEY"
            gh secret set PODCASTINDEX_API_SECRET --body "$PODCASTINDEX_API_SECRET" || print_warning "Failed to set PODCASTINDEX_API_SECRET"
            [ -n "$YOUTUBE_API_KEY" ] && gh secret set YOUTUBE_API_KEY --body "$YOUTUBE_API_KEY"
            gh secret set GCP_PROJECT_ID --body "$PROJECT_ID" || print_warning "Failed to set GCP_PROJECT_ID"

            # Set service account key if it exists
            if [ -f "./ekko-468919-18b71c68e6b2.json" ]; then
                gh secret set GCP_SA_KEY --body "$(cat ./ekko-468919-18b71c68e6b2.json)" || print_warning "Failed to set GCP_SA_KEY"
            fi

            print_success "GitHub secrets configured"
        else
            print_info "[DRY RUN] Would set GitHub secrets"
        fi
    fi
fi

# Summary
echo
print_success "=== Setup Complete ==="
echo
print_info "Project ID: $PROJECT_ID"
print_info "Region: $REGION"
print_info "Service: $SERVICE_NAME"
echo
print_info "Secrets configured in Google Secret Manager:"
for secret in "${ALL_SECRETS[@]}"; do
    if gcloud secrets describe "$secret" --project="$PROJECT_ID" &>/dev/null; then
        echo "  ✓ $secret"
    fi
done

echo
print_info "Next steps:"
echo "  1. Deploy the application to Cloud Run:"
echo "     gcloud run deploy $SERVICE_NAME \\"
echo "       --image gcr.io/$PROJECT_ID/$SERVICE_NAME:latest \\"
echo "       --region $REGION \\"
echo "       --platform managed \\"
echo "       --allow-unauthenticated \\"
echo "       --set-secrets=OPENAI_API_KEY=openai-api-key:latest \\"
echo "       --set-secrets=PODCASTINDEX_API_KEY=podcastindex-api-key:latest \\"
echo "       --set-secrets=PODCASTINDEX_API_SECRET=podcastindex-api-secret:latest"
echo
echo "  2. Or push code to trigger automatic deployment via GitHub Actions"
echo
print_success "Script completed successfully!"
