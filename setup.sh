#!/bin/bash

# Script de configuration du projet Django RFID System

echo "🚀 Configuration du projet Django RFID System"

# Création de l'environnement virtuel
echo "📦 Création de l'environnement virtuel..."
python -m venv venv

# Activation de l'environnement virtuel
echo "🔧 Activation de l'environnement virtuel..."
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate  # Windows

# Installation des dépendances
echo "📚 Installation des dépendances..."
pip install -r requirements.txt

# Configuration de la base de données PostgreSQL
echo "🗄️ Configuration de la base de données..."
echo "Assurez-vous que PostgreSQL et PostGIS sont installés et configurés."
echo "Créez une base de données 'rfid_system_db' avec l'extension PostGIS."

# Migrations
echo "🔄 Création et application des migrations..."
python manage.py makemigrations
python manage.py migrate

# Création du superutilisateur
echo "👤 Création du superutilisateur..."
python manage.py createsuperuser

# Collecte des fichiers statiques
echo "📁 Collecte des fichiers statiques..."
python manage.py collectstatic --noinput

echo "✅ Configuration terminée!"
echo "🌐 Lancez le serveur avec: python manage.py runserver"
echo "🔗 Interface admin: http://127.0.0.1:8000/admin/"
