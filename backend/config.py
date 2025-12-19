"""
Configuration du système de présence
"""
import os
from dotenv import load_dotenv

load_dotenv()

# MongoDB
MONGODB_URI = os.getenv('MONGODB_URI', 'mongodb://localhost:27017/')
DATABASE_NAME = os.getenv('DATABASE_NAME', 'systeme_presence')
COLLECTION_ETUDIANTS = os.getenv('COLLECTION_ETUDIANTS', 'etudiants')
COLLECTION_PRESENCES = os.getenv('COLLECTION_PRESENCES', 'presences')
COLLECTION_COURS = os.getenv('COLLECTION_COURS', 'cours')

# Caméra
CAMERA_INDEX = int(os.getenv('CAMERA_INDEX', 0))
VIDEO_SOURCE = os.getenv('VIDEO_SOURCE', '')

# Reconnaissance faciale
TOLERANCE = float(os.getenv('TOLERANCE', 0.6))
MODEL = os.getenv('MODEL', 'hog')
FRAME_SKIP = int(os.getenv('FRAME_SKIP', 2))

# Chemins
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
PROJECT_ROOT = os.path.dirname(BASE_DIR)  # Dossier parent (racine du projet)
ENCODAGES_DIR = os.path.join(PROJECT_ROOT, 'encodages')
RAPPORTS_DIR = os.path.join(PROJECT_ROOT, 'rapports')
LOGS_DIR = os.path.join(PROJECT_ROOT, 'logs')

# Logs
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
