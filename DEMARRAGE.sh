#!/bin/bash
# Script de démarrage complet du système de présence
# Pour vidéo LinkedIn - Démarrage propre et professionnel

echo "╔══════════════════════════════════════════════════════════╗"
echo "║   🎓 SYSTÈME DE PRÉSENCE - RECONNAISSANCE FACIALE       ║"
echo "║            Démarrage du Système Complet                 ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""

# Aller dans le dossier du projet
cd /home/nourhen/mon_projet/face_recognition

# 1. Vérifier MongoDB
echo "🔍 Étape 1/3 : Vérification de MongoDB..."
if docker ps | grep -q presence_mongodb; then
    echo "✅ MongoDB est déjà actif"
else
    echo "⚠️  Démarrage de MongoDB..."
    docker start presence_mongodb 2>/dev/null || docker-compose up -d mongodb
    sleep 3
    echo "✅ MongoDB démarré"
fi
echo ""

# 2. Démarrer le Backend
echo "🔧 Étape 2/3 : Démarrage du Backend API (Flask)..."
# Arrêter les anciens processus
pkill -f "python.*api.py" 2>/dev/null
sleep 1

# Activer l'environnement virtuel et démarrer
source env/bin/activate
nohup python backend/api.py > backend_logs.txt 2>&1 &
BACKEND_PID=$!

# Attendre que le backend soit prêt
echo "   Attente du démarrage..."
for i in {1..10}; do
    if curl -s http://localhost:5000/health > /dev/null 2>&1; then
        echo "✅ Backend actif sur http://localhost:5000 (PID: $BACKEND_PID)"
        break
    fi
    sleep 1
done
echo ""

# 3. Démarrer le Frontend
echo "🌐 Étape 3/3 : Démarrage du Frontend Web..."
# Arrêter les anciens serveurs sur le port 8080
pkill -f "http.server 8080" 2>/dev/null
sleep 1

cd frontend
python3 -m http.server 8080 > /dev/null 2>&1 &
FRONTEND_PID=$!
sleep 2
echo "✅ Frontend actif sur http://localhost:8080 (PID: $FRONTEND_PID)"
echo ""

# Affichage final
echo "╔══════════════════════════════════════════════════════════╗"
echo "║         🎉 SYSTÈME DÉMARRÉ AVEC SUCCÈS !                ║"
echo "╚══════════════════════════════════════════════════════════╝"
echo ""
echo "📱 ACCÈS AU SYSTÈME :"
echo "   → Frontend Web : http://localhost:8080"
echo "   → Backend API  : http://localhost:5000"
echo "   → MongoDB      : localhost:27017"
echo ""
echo "🎬 POUR VOTRE VIDÉO LINKEDIN :"
echo "   1. Ouvrez http://localhost:8080 dans votre navigateur"
echo "   2. Testez l'ajout d'un étudiant avec photo"
echo "   3. Démarrez la webcam et testez la reconnaissance"
echo "   4. Montrez l'historique des présences"
echo ""
echo "🛑 POUR ARRÊTER LE SYSTÈME :"
echo "   → Backend  : kill $BACKEND_PID"
echo "   → Frontend : kill $FRONTEND_PID"
echo "   → Ou utilisez : pkill -f 'python.*api.py' && pkill -f 'http.server'"
echo ""
echo "📊 LOGS EN TEMPS RÉEL :"
echo "   → Backend : tail -f ../backend_logs.txt"
echo ""
echo "✨ Bonne chance pour votre vidéo LinkedIn ! 🎥"
echo ""
