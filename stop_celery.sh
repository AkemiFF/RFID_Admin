#!/bin/bash

# Script pour arrêter les services Celery

echo "🛑 Arrêt des services Celery"

# Arrêt de tous les processus Celery
pkill -f "celery worker"
pkill -f "celery beat"
pkill -f "celery flower"

echo "✅ Services Celery arrêtés!"
