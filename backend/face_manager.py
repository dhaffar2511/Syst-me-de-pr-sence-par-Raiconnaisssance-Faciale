"""
Gestionnaire de reconnaissance faciale
"""
import os
import pickle
import face_recognition
import logging
import config

logger = logging.getLogger(__name__)


class FaceRecognitionManager:
    """
    Gestionnaire de reconnaissance faciale
    Gère le chargement, la sauvegarde et l'utilisation des encodages de visages
    """
    
    def __init__(self):
        """Initialise le gestionnaire et charge les encodages existants"""
        self.known_encodings = []
        self.known_ids = []
        self.charger_encodages()
    
    def charger_encodages(self):
        """
        Charge tous les encodages depuis le dossier encodages
        Les fichiers sont au format: ETUDIANT_ID.pkl
        """
        self.known_encodings = []
        self.known_ids = []
        
        # Créer le dossier s'il n'existe pas
        if not os.path.exists(config.ENCODAGES_DIR):
            os.makedirs(config.ENCODAGES_DIR)
            logger.warning(f"📁 Dossier encodages créé: {config.ENCODAGES_DIR}")
            return
        
        # Charger tous les fichiers .pkl
        count = 0
        for filename in os.listdir(config.ENCODAGES_DIR):
            if filename.endswith('.pkl'):
                filepath = os.path.join(config.ENCODAGES_DIR, filename)
                try:
                    with open(filepath, 'rb') as f:
                        encoding = pickle.load(f)
                    
                    # Extraire l'ID étudiant du nom de fichier
                    etudiant_id = filename.replace('.pkl', '')
                    
                    self.known_encodings.append(encoding)
                    self.known_ids.append(etudiant_id)
                    count += 1
                    
                except Exception as e:
                    logger.error(f"❌ Erreur chargement {filename}: {e}")
        
        logger.info(f"✅ {count} encodages chargés depuis {config.ENCODAGES_DIR}")
    
    def encoder_visage(self, image_path, etudiant_id):
        """
        Encode un visage depuis une image et sauvegarde l'encodage
        
        Args:
            image_path: Chemin vers l'image
            etudiant_id: ID de l'étudiant
            
        Returns:
            encoding: L'encodage du visage
            
        Raises:
            ValueError: Si aucun visage ou plusieurs visages détectés
        """
        try:
            # Charger l'image
            logger.info(f"📸 Chargement image: {image_path}")
            image = face_recognition.load_image_file(image_path)
            
            # Détecter les visages (utilise HOG pour la vitesse)
            face_locations = face_recognition.face_locations(image, model='hog')
            
            if len(face_locations) == 0:
                raise ValueError("❌ Aucun visage détecté dans l'image")
            
            if len(face_locations) > 1:
                raise ValueError(f"❌ {len(face_locations)} visages détectés. Une seule personne par photo.")
            
            logger.info(f"✅ 1 visage détecté")
            
            # Encoder le visage
            encodings = face_recognition.face_encodings(image, face_locations)
            encoding = encodings[0]
            
            # Sauvegarder l'encodage
            encoding_path = os.path.join(config.ENCODAGES_DIR, f"{etudiant_id}.pkl")
            with open(encoding_path, 'wb') as f:
                pickle.dump(encoding, f)
            
            logger.info(f"💾 Encodage sauvegardé: {encoding_path}")
            
            # Recharger tous les encodages pour mettre à jour la liste
            self.charger_encodages()
            
            return encoding
            
        except Exception as e:
            logger.error(f"❌ Erreur encodage {etudiant_id}: {e}")
            raise
    
    def supprimer_encodage(self, etudiant_id):
        """
        Supprime l'encodage d'un étudiant
        
        Args:
            etudiant_id: ID de l'étudiant
            
        Returns:
            bool: True si supprimé avec succès
        """
        try:
            encoding_path = os.path.join(config.ENCODAGES_DIR, f"{etudiant_id}.pkl")
            
            if os.path.exists(encoding_path):
                os.remove(encoding_path)
                logger.info(f"🗑️ Encodage supprimé: {etudiant_id}")
                
                # Recharger les encodages
                self.charger_encodages()
                return True
            else:
                logger.warning(f"⚠️ Encodage non trouvé: {etudiant_id}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Erreur suppression encodage {etudiant_id}: {e}")
            return False
    
    def reconnaitre_visage(self, face_encoding, tolerance=0.5):
        """
        Reconnaît un visage en comparant son encodage avec les encodages connus
        
        Args:
            face_encoding: L'encodage du visage à reconnaître
            tolerance: Seuil de tolérance (plus bas = plus strict)
            
        Returns:
            tuple: (etudiant_id, distance) ou (None, None) si non reconnu
        """
        if len(self.known_encodings) == 0:
            logger.warning("⚠️ Aucun encodage chargé")
            return None, None
        
        # Calculer les distances avec tous les encodages connus
        face_distances = face_recognition.face_distance(self.known_encodings, face_encoding)
        
        # Trouver la meilleure correspondance
        best_match_index = face_distances.argmin()
        min_distance = face_distances[best_match_index]
        
        if min_distance < tolerance:
            etudiant_id = self.known_ids[best_match_index]
            logger.info(f"✅ Visage reconnu: {etudiant_id} (distance: {min_distance:.3f})")
            return etudiant_id, min_distance
        else:
            logger.info(f"❌ Visage non reconnu (distance min: {min_distance:.3f})")
            return None, None
    
    def obtenir_info_encodages(self):
        """
        Retourne des informations sur les encodages chargés
        
        Returns:
            dict: Informations sur les encodages
        """
        return {
            'total': len(self.known_encodings),
            'etudiants': self.known_ids,
            'dossier': config.ENCODAGES_DIR
        }
