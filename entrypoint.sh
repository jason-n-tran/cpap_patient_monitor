#!/bin/bash
set -e

echo "Starting Sleep Lab Monitoring System..."

# Execute the command passed to the container
exec "$@"
