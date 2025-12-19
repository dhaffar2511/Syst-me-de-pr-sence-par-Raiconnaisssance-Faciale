#!/bin/bash
# Script de démarrage complet du système (backend + frontend)

clear
echo "╔════════════════════════════════════════════════════════════╗"
echo "║   🎓 SYSTÈME DE PRÉSENCE - RECONNAISSANCE FACIALE         ║"
echo "║              Démarrage Complet du Système                 ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Couleurs
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Répertoire du projet
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$PROJECT_DIR"

# Fonction d'affichage avec couleur
print_status() {
    local color=$1
    local icon=$2
    local message=$3
    echo -e "${color}${icon} ${message}${NC}"
}

# 1. Vérifier MongoDB
print_status "$BLUE" "🔍" "Vérification de MongoDB..."
if docker ps | grep -q "presence_mongodb"; then
    print_status "$GREEN" "✅" "MongoDB est en cours d'exécution"
else
    print_status "$YELLOW" "⚠️" "MongoDB n'est pas démarré. Démarrage en cours..."
    if docker start presence_mongodb 2>/dev/null; then
        print_status "$GREEN" "✅" "MongoDB démarré avec succès"
    else
        print_status "$YELLOW" "📦" "Création du conteneur MongoDB..."
        docker-compose up -d
        sleep 3
        if docker ps | grep -q "presence_mongodb"; then
            print_status "$GREEN" "✅" "MongoDB créé et démarré"
        else
            print_status "$RED" "❌" "Erreur: Impossible de démarrer MongoDB"
            exit 1
        fi
    fi
fi
echo ""

# 2. Vérifier l'environnement virtuel
print_status "$BLUE" "🔍" "Vérification de l'environnement virtuel..."
if [ ! -d "env" ]; then
    print_status "$RED" "❌" "Environnement virtuel non trouvé!"
    print_status "$YELLOW" "💡" "Exécutez d'abord: ./installer.sh"
    exit 1
fi
print_status "$GREEN" "✅" "Environnement virtuel trouvé"
echo ""

# 3. Vérifier si le backend est déjà lancé
print_status "$BLUE" "🔍" "Vérification du backend..."
if curl -s http://localhost:5000/health > /dev/null 2>&1; then
    print_status "$YELLOW" "⚠️" "Le backend est déjà en cours d'exécution"
    read -p "Voulez-vous le redémarrer? (y/n) " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        pkill -f "python.*api.py" 2>/dev/null
        sleep 2
        print_status "$GREEN" "✅" "Backend arrêté"
    else
        print_status "$BLUE" "➡️" "Conservation du backend existant"
        BACKEND_ALREADY_RUNNING=true
    fi
fi
echo ""

# 4. Démarrer le backend si nécessaire
if [ "$BACKEND_ALREADY_RUNNING" != true ]; then
    print_status "$BLUE" "🚀" "Démarrage du backend API..."
    
    cd "$PROJECT_DIR/backend"
    source ../env/bin/activate
    
    # Démarrer l'API en arrière-plan
    nohup python api.py > ../logs/api.log 2>&1 &
    BACKEND_PID=$!
    
    # Attendre que l'API soit prête
    print_status "$YELLOW" "⏳" "Attente du démarrage de l'API..."
    for i in {1..10}; do
        if curl -s http://localhost:5000/health > /dev/null 2>&1; then
            print_status "$GREEN" "✅" "Backend API démarré (PID: $BACKEND_PID)"
            break
        fi
        sleep 1
        echo -n "."
    done
    echo ""
    
    if ! curl -s http://localhost:5000/health > /dev/null 2>&1; then
        print_status "$RED" "❌" "Erreur: Le backend n'a pas démarré correctement"
        print_status "$YELLOW" "💡" "Consultez les logs: tail -f logs/api.log"
        exit 1
    fi
    echo ""
fi

# 5. Démarrer le frontend
print_status "$BLUE" "🚀" "Démarrage du frontend..."
cd "$PROJECT_DIR/frontend"

# Vérifier si le port 8080 est disponible
if lsof -Pi :8080 -sTCP:LISTEN -t >/dev/null 2>&1; then
    print_status "$YELLOW" "⚠️" "Le port 8080 est déjà utilisé"
    PORT=8081
    print_status "$BLUE" "➡️" "Utilisation du port $PORT à la place"
else
    PORT=8080
fi
echo ""

# Afficher les informations finales
echo "╔════════════════════════════════════════════════════════════╗"
echo "║              🎉 SYSTÈME DÉMARRÉ AVEC SUCCÈS!              ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""
print_status "$GREEN" "🌐" "Frontend Web      : http://localhost:$PORT"
print_status "$GREEN" "🔧" "Backend API       : http://localhost:5000"
print_status "$GREEN" "💾" "MongoDB           : localhost:27017"
echo ""
print_status "$BLUE" "📱" "OUVREZ VOTRE NAVIGATEUR À:"
print_status "$GREEN" "   →" "http://localhost:$PORT"
echo ""
print_status "$YELLOW" "💡" "Pour arrêter le système:"
print_status "$YELLOW" "   →" "Appuyez sur Ctrl+C dans ce terminal"
print_status "$YELLOW" "   →" "Ou exécutez: pkill -f 'python.*api.py'"
echo ""
print_status "$BLUE" "📊" "Logs disponibles:"
print_status "$BLUE" "   →" "Backend: tail -f logs/api.log"
print_status "$BLUE" "   →" "MongoDB: docker logs presence_mongodb"
echo ""
echo "════════════════════════════════════════════════════════════"
echo ""

# Démarrer le serveur frontend
print_status "$GREEN" "🚀" "Serveur frontend en cours d'exécution..."
print_status "$YELLOW" "⚠️" "NE PAS FERMER CE TERMINAL"
echo ""

python3 -m http.server $PORT

# Cleanup au cas où l'utilisateur arrête le frontend
print_status "$YELLOW" "⚠️" "Frontend arrêté"
read -p "Voulez-vous aussi arrêter le backend? (y/n) " -n 1 -r
echo ""
if [[ $REPLY =~ ^[Yy]$ ]]; then
    pkill -f "python.*api.py"
    print_status "$GREEN" "✅" "Backend arrêté"
fi

print_status "$BLUE" "👋" "Au revoir!"
