// Script d'initialisation MongoDB
// Crée la base de données et les collections avec index

db = db.getSiblingDB('systeme_presence');

// Créer les collections
db.createCollection('etudiants');
db.createCollection('cours');
db.createCollection('presences');

// Index pour etudiants
db.etudiants.createIndex({ "numero_etudiant": 1 }, { unique: true });
db.etudiants.createIndex({ "nom": 1 });
db.etudiants.createIndex({ "email": 1 });

// Index pour cours
db.cours.createIndex({ "code_cours": 1 }, { unique: true });
db.cours.createIndex({ "professeur": 1 });

// Index pour presences
db.presences.createIndex({ "date": -1, "cours_id": 1 });
db.presences.createIndex({ "etudiant_id": 1 });
db.presences.createIndex({ "cours_code": 1 });
db.presences.createIndex({ "etudiant_numero": 1 });

// Insérer des données de test (optionnel)
db.cours.insertOne({
    "code_cours": "DEMO101",
    "nom": "Cours de Démonstration",
    "professeur": "Prof. Demo",
    "salle": "A-100",
    "date_creation": new Date(),
    "actif": true
});

print('✅ Base de données initialisée avec succès!');
print('✅ Collections créées: etudiants, cours, presences');
print('✅ Index créés pour optimiser les performances');
print('✅ Cours de démonstration créé: DEMO101');
