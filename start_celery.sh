#!/bin/bash

# Script pour démarrer Celery Worker et Beat

echo "🚀 Démarrage des services Celery"

# Démarrage du worker Celery en arrière-plan
echo "📦 Démarrage du Celery Worker..."
celery -A rfid_system worker --loglevel=info --detach

# Démarrage du scheduler Celery Beat en arrière-plan
echo "⏰ Démarrage du Celery Beat..."
celery -A rfid_system beat --loglevel=info --detach

# Démarrage de Flower pour le monitoring (optionnel)
echo "🌸 Démarrage de Flower (monitoring)..."
celery -A rfid_system flower --detach

echo "✅ Services Celery démarrés!"
echo "🌐 Flower disponible sur: http://localhost:5555"
echo "📊 Monitoring des tâches: celery -A rfid_system events"
echo "🛑 Arrêter les services: pkill -f celery"
