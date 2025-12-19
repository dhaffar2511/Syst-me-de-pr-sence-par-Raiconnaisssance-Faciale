"""
Gestionnaire de base de données MongoDB
"""
from pymongo import MongoClient, DESCENDING
from datetime import datetime
import config
import logging

logging.basicConfig(level=config.LOG_LEVEL)
logger = logging.getLogger(__name__)


class DatabaseManager:
    """Gère toutes les interactions avec MongoDB"""
    
    def __init__(self):
        """Initialise la connexion à MongoDB"""
        try:
            self.client = MongoClient(config.MONGODB_URI)
            self.db = self.client[config.DATABASE_NAME]
            self.etudiants = self.db[config.COLLECTION_ETUDIANTS]
            self.presences = self.db[config.COLLECTION_PRESENCES]
            self.cours = self.db[config.COLLECTION_COURS]
            
            # Créer les index
            self._creer_index()
            logger.info(" Connexion MongoDB établie")
            
        except Exception as e:
            logger.error(f" Erreur connexion MongoDB: {e}")
            raise
    
    def _creer_index(self):
        """Crée les index pour optimiser les requêtes"""
        self.etudiants.create_index("numero_etudiant", unique=True)
        self.etudiants.create_index("nom")
        self.presences.create_index([("date", DESCENDING), ("cours_id", 1)])
        self.presences.create_index("etudiant_id")
        self.cours.create_index("code_cours", unique=True)
    
    # ÉTUDIANTS 
    def ajouter_etudiant(self, numero, nom, prenom, email, photo_path=None):
        """Ajoute un nouvel étudiant"""
        try:
            etudiant = {
                "numero_etudiant": numero,
                "nom": nom,
                "prenom": prenom,
                "email": email,
                "photo_path": photo_path,
                "date_inscription": datetime.now(),
                "actif": True
            }
            
            result = self.etudiants.insert_one(etudiant)
            logger.info(f" Étudiant ajouté: {nom} {prenom}")
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f" Erreur ajout étudiant: {e}")
            return None
    
    def obtenir_etudiant(self, numero):
        """Récupère un étudiant par son numéro"""
        return self.etudiants.find_one({"numero_etudiant": numero})
    
    def obtenir_tous_etudiants(self, actifs_seulement=True):
        """Récupère tous les étudiants"""
        filtre = {"actif": True} if actifs_seulement else {}
        return list(self.etudiants.find(filtre).sort("nom", 1))
    
    def modifier_etudiant(self, numero, modifications):
        """Modifie les informations d'un étudiant"""
        try:
            result = self.etudiants.update_one(
                {"numero_etudiant": numero},
                {"$set": modifications}
            )
            if result.modified_count > 0:
                logger.info(f" Étudiant {numero} modifié")
                return True
            return False
        except Exception as e:
            logger.error(f" Erreur modification: {e}")
            return False
    
    def supprimer_etudiant(self, numero):
        """Supprime définitivement un étudiant"""
        try:
            result = self.etudiants.delete_one({"numero_etudiant": numero})
            if result.deleted_count > 0:
                logger.info(f"✅ Étudiant {numero} supprimé")
                return True
            logger.warning(f"⚠️ Étudiant {numero} introuvable")
            return False
        except Exception as e:
            logger.error(f"❌ Erreur suppression étudiant: {e}")
            return False
    
    # COURS 
    
    def ajouter_cours(self, code, nom, professeur, salle=None, email_professeur=None):
        """Ajoute un nouveau cours"""
        try:
            cours = {
                "code_cours": code,
                "nom": nom,
                "professeur": professeur,
                "email_professeur": email_professeur,
                "salle": salle,
                "date_creation": datetime.now(),
                "actif": True
            }
            
            result = self.cours.insert_one(cours)
            logger.info(f" Cours ajouté: {code} - {nom}")
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f" Erreur ajout cours: {e}")
            return None
    
    def obtenir_cours(self, code):
        """Récupère un cours par son code"""
        return self.cours.find_one({"code_cours": code})
    
    def obtenir_tous_cours(self, actifs_seulement=True):
        """Récupère tous les cours"""
        filtre = {"actif": True} if actifs_seulement else {}
        return list(self.cours.find(filtre).sort("code_cours", 1))
    
    def supprimer_cours(self, code):
        """Supprime définitivement un cours"""
        try:
            result = self.cours.delete_one({"code_cours": code})
            if result.deleted_count > 0:
                logger.info(f"✅ Cours {code} supprimé")
                return True
            logger.warning(f"⚠️ Cours {code} introuvable")
            return False
        except Exception as e:
            logger.error(f"❌ Erreur suppression cours: {e}")
            return False
    
    # PRÉSENCES 
    
    def obtenir_toutes_presences(self):
        """Récupère toutes les présences enregistrées"""
        return list(self.presences.find().sort("date", DESCENDING))
    
    def ajouter_presence(self, code_cours, liste_etudiants, date_presence=None):
        """
        Enregistre la présence de plusieurs étudiants pour un cours
        
        Args:
            code_cours: Code du cours
            liste_etudiants: Liste des IDs des étudiants présents
            date_presence: Date de la présence (par défaut: maintenant)
        
        Returns:
            ID de la présence enregistrée
        """
        try:
            if date_presence is None:
                date_presence = datetime.now()
            
            cours = self.obtenir_cours(code_cours)
            if not cours:
                logger.warning(f" Cours introuvable: {code_cours}")
                return None
            
            # Enregistrer chaque étudiant individuellement
            presence_ids = []
            for etudiant_id in liste_etudiants:
                presence_id = self.enregistrer_presence(etudiant_id, code_cours, confiance=0.9)
                if presence_id:
                    presence_ids.append(presence_id)
            
            logger.info(f" {len(presence_ids)} présence(s) enregistrée(s) pour {code_cours}")
            
            # Retourner le premier ID (pour compatibilité)
            return presence_ids[0] if presence_ids else None
            
        except Exception as e:
            logger.error(f" Erreur ajouter_presence: {e}")
            return None
    
    def enregistrer_presence(self, numero_etudiant, code_cours, confiance=None):
        """Enregistre la présence d'un étudiant à un cours"""
        try:
            etudiant = self.obtenir_etudiant(numero_etudiant)
            cours = self.obtenir_cours(code_cours)
            
            if not etudiant or not cours:
                logger.warning(f"  Étudiant ou cours introuvable")
                return None
            
            # Vérifier si déjà présent aujourd'hui pour ce cours
            aujourd_hui = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
            existe = self.presences.find_one({
                "etudiant_id": etudiant["_id"],
                "cours_id": cours["_id"],
                "date": {"$gte": aujourd_hui}
            })
            
            if existe:
                logger.info(f" {etudiant['nom']} déjà marqué présent pour {code_cours}")
                return str(existe["_id"])
            
            # Enregistrer la présence
            presence = {
                "etudiant_id": etudiant["_id"],
                "etudiant_numero": numero_etudiant,
                "etudiant_nom": f"{etudiant['nom']} {etudiant['prenom']}",
                "cours_id": cours["_id"],
                "cours_code": code_cours,
                "cours_nom": cours["nom"],
                "date": datetime.now(),
                "confiance": confiance,
                "methode": "automatique"
            }
            
            result = self.presences.insert_one(presence)
            logger.info(f" Présence enregistrée: {etudiant['nom']} - {code_cours}")
            return str(result.inserted_id)
            
        except Exception as e:
            logger.error(f"Erreur enregistrement présence: {e}")
            return None
    
    def obtenir_presences_cours(self, code_cours, date=None):
        """Récupère les présences pour un cours à une date donnée"""
        if date is None:
            date = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        
        cours = self.obtenir_cours(code_cours)
        if not cours:
            return []
        
        return list(self.presences.find({
            "cours_id": cours["_id"],
            "date": {"$gte": date}
        }).sort("date", DESCENDING))
    
    def obtenir_presences_etudiant(self, numero_etudiant, date_debut=None, date_fin=None):
        """Récupère toutes les présences d'un étudiant"""
        etudiant = self.obtenir_etudiant(numero_etudiant)
        if not etudiant:
            return []
        
        filtre = {"etudiant_id": etudiant["_id"]}
        
        if date_debut or date_fin:
            filtre["date"] = {}
            if date_debut:
                filtre["date"]["$gte"] = date_debut
            if date_fin:
                filtre["date"]["$lte"] = date_fin
        
        return list(self.presences.find(filtre).sort("date", DESCENDING))
    
    def statistiques_presence_etudiant(self, numero_etudiant):
        """Calcule les statistiques de présence d'un étudiant"""
        presences = self.obtenir_presences_etudiant(numero_etudiant)
        
        if not presences:
            return {
                "total_presences": 0,
                "cours_differents": 0,
                "taux_presence": 0
            }
        
        cours_differents = set(p["cours_code"] for p in presences)
        
        return {
            "total_presences": len(presences),
            "cours_differents": len(cours_differents),
            "derniere_presence": presences[0]["date"] if presences else None,
            "cours_frequentes": list(cours_differents)
        }
    
    def statistiques_cours(self, code_cours, date_debut=None, date_fin=None):
        """Calcule les statistiques de présence pour un cours"""
        cours = self.obtenir_cours(code_cours)
        if not cours:
            return None
        
        filtre = {"cours_id": cours["_id"]}
        
        if date_debut or date_fin:
            filtre["date"] = {}
            if date_debut:
                filtre["date"]["$gte"] = date_debut
            if date_fin:
                filtre["date"]["$lte"] = date_fin
        
        presences = list(self.presences.find(filtre))
        
        etudiants_uniques = set(p["etudiant_numero"] for p in presences)
        
        return {
            "code_cours": code_cours,
            "nom_cours": cours["nom"],
            "total_presences": len(presences),
            "etudiants_differents": len(etudiants_uniques),
            "moyenne_par_seance": len(presences) / max(1, len(set(p["date"].date() for p in presences)))
        }
    
    def fermer_connexion(self):
        """Ferme la connexion MongoDB"""
        self.client.close()
        logger.info(" Connexion MongoDB fermée")
