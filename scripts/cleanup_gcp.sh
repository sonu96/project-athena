#!/bin/bash

# Script to list and optionally delete GCP projects

echo "🧹 GCP Project Cleanup"
echo "====================="
echo

# List all projects
echo "Your Google Cloud projects:"
echo
gcloud projects list --format="table(projectId,name,createTime)"

echo
echo "To delete a project, run:"
echo "  gcloud projects delete PROJECT_ID"
echo
echo "To delete multiple projects, you can use:"
echo "  gcloud projects delete PROJECT_ID1 PROJECT_ID2 PROJECT_ID3"
echo

# Optional: Interactive deletion
read -p "Do you want to delete a project now? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    read -p "Enter project ID to delete: " PROJECT_TO_DELETE
    
    if [ ! -z "$PROJECT_TO_DELETE" ]; then
        echo "⚠️  WARNING: This will permanently delete project: $PROJECT_TO_DELETE"
        read -p "Are you sure? Type 'DELETE' to confirm: " CONFIRM
        
        if [ "$CONFIRM" == "DELETE" ]; then
            gcloud projects delete $PROJECT_TO_DELETE
            echo "✅ Project deletion initiated"
        else
            echo "❌ Deletion cancelled"
        fi
    fi
fi