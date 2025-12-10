#!/bin/bash

# Flight Tracker - Databricks Deployment Script

echo "🚀 Deploying Flight Tracker to Databricks..."
echo ""

# Check if DATABRICKS_HOST is set
if [ -z "$DATABRICKS_HOST" ]; then
    echo "❌ Error: DATABRICKS_HOST environment variable is not set"
    echo "Please set it with: export DATABRICKS_HOST=https://your-workspace.cloud.databricks.com"
    exit 1
fi

# Parse target from arguments (default to dev)
TARGET="${1:-dev}"

echo "📋 Deployment Configuration:"
echo "   Target: $TARGET"
echo "   Workspace: $DATABRICKS_HOST"
echo ""

# Validate the bundle
echo "✅ Validating Databricks Asset Bundle..."
databricks bundle validate

if [ $? -ne 0 ]; then
    echo "❌ Bundle validation failed!"
    exit 1
fi

echo ""
echo "📦 Deploying to $TARGET environment..."
databricks bundle deploy --target $TARGET

if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Deployment successful!"
    echo "🌐 Access your app in the Databricks workspace under 'Apps'"
else
    echo "❌ Deployment failed!"
    exit 1
fi

