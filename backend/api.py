"""
Flask + MongoDB + Reconnaissance Faciale
"""
from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import sys
from datetime import datetime
import base64
import io
from PIL import Image
import logging
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import cv2
import face_recognition
import numpy as np

# Ajouter le répertoire parent au path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import DatabaseManager
from face_manager import FaceRecognitionManager
import config

# Configuration logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialiser Flask
app = Flask(__name__)
CORS(app)  # Autoriser CORS pour le frontend

# Initialiser managers
db = DatabaseManager()
face_mgr = FaceRecognitionManager()

# Configuration Email (vous pouvez modifier ces paramètres)
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_USER = 'votre.email@gmail.com'  # À configurer
EMAIL_PASSWORD = 'votre_mot_de_passe'  # À configurer avec mot de passe d'application
EMAIL_FROM = 'Système de Présence ISIMM <noreply@isimm.tn>'



# Initialiser managers
db = DatabaseManager()
face_mgr = FaceRecognitionManager()

# ==================== ROUTES SANTÉ ====================

@app.route('/health', methods=['GET'])
def health_check():
    """Vérification de la santé du service"""
    try:
        # Tester MongoDB
        etudiants_count = len(db.obtenir_tous_etudiants())
        
        return jsonify({
            'status': 'healthy',
            'service': 'presence-api',
            'timestamp': datetime.now().isoformat(),
            'mongodb': 'connected',
            'etudiants': etudiants_count,
            'encodages': len(face_mgr.known_encodings)
        }), 200
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 500

# ÉTUDIANTS 

@app.route('/api/etudiants', methods=['GET'])
def get_etudiants():
    """Récupérer tous les étudiants"""
    try:
        etudiants = db.obtenir_tous_etudiants()
        # Convertir ObjectId en string et reformater
        etudiants_formatted = []
        for e in etudiants:
            numero = e.get('numero_etudiant', '')
            etudiants_formatted.append({
                '_id': str(e['_id']),
                'numero_etudiant': numero,  # Champ principal
                'id_etudiant': numero,       # Alias pour compatibilité
                'nom': f"{e.get('nom', '')} {e.get('prenom', '')}".strip(),
                'email': e.get('email', ''),
                'date_inscription': e.get('date_inscription', datetime.now()).isoformat() if 'date_inscription' in e else datetime.now().isoformat()
            })
        
        return jsonify({
            'success': True,
            'count': len(etudiants_formatted),
            'etudiants': etudiants_formatted
        }), 200
    except Exception as e:
        logger.error(f"Error getting students: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# PRÉSENCES 

@app.route('/api/presences', methods=['GET'])
def get_presences():
    """Récupérer l'historique des présences"""
    
    try:
        presences = db.obtenir_toutes_presences()
        for p in presences:
            if '_id' in p:
                p['_id'] = str(p['_id'])
            if 'etudiant_id' in p and hasattr(p['etudiant_id'], '__iter__'):
                if isinstance(p['etudiant_id'], list):
                    p['etudiant_id'] = [str(eid) if not isinstance(eid, str) else eid for eid in p['etudiant_id']]
                else:
                    p['etudiant_id'] = str(p['etudiant_id'])
            if 'date' in p and hasattr(p['date'], 'isoformat'):
                p['date'] = p['date'].isoformat()
        
        return jsonify({
            'success': True,
            'count': len(presences),
            'presences': presences
        }), 200
    except Exception as e:
        logger.error(f"Error getting presences: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/etudiants', methods=['POST'])
def add_etudiant():
    """Ajouter un nouvel étudiant"""
    try:
        # Récupérer les données du formulaire
        id_etudiant = request.form.get('id_etudiant')
        nom = request.form.get('nom')
        email = request.form.get('email')
        photo = request.files.get('photo')
        
        # Validation
        if not id_etudiant or not nom or not email:
            return jsonify({'success': False, 'erreur': 'Champs requis manquants'}), 400
        
        # Séparer nom et prénom (si fourni avec espace)
        nom_parts = nom.strip().split(' ', 1)
        prenom = nom_parts[1] if len(nom_parts) > 1 else ''
        nom_famille = nom_parts[0]
        
        # Traiter la photo si fournie
        photo_path = None
        encoding = None
        
        if photo and photo.filename:
            # Créer le dossier photos s'il n'existe pas
            photos_dir = os.path.join(config.BASE_DIR, 'photos')
            os.makedirs(photos_dir, exist_ok=True)
            
            # Sauvegarder la photo
            photo_filename = f"{id_etudiant}_{photo.filename}"
            photo_path = os.path.join(photos_dir, photo_filename)
            photo.save(photo_path)
            
            # Générer l'encodage facial
            encoding = face_mgr.encoder_visage(photo_path, id_etudiant)
            
            if encoding is None:
                logger.warning(f"Impossible d'encoder le visage pour {id_etudiant}")
        
        # Ajouter dans la base de données
        etudiant_id = db.ajouter_etudiant(
            id_etudiant,
            nom_famille,
            prenom,
            email,
            photo_path
        )
        
        if not etudiant_id:
            return jsonify({'success': False, 'erreur': 'Erreur lors de l\'ajout dans la base'}), 500
        
        response_data = {
            'success': True,
            'id': str(etudiant_id),
            'message': 'Étudiant ajouté avec succès'
        }
        
        if encoding is None and photo:
            response_data['warning'] = 'Visage non détecté dans la photo'
        
        return jsonify(response_data), 201
        
    except Exception as e:
        logger.error(f"Error adding student: {e}")
        return jsonify({'success': False, 'erreur': str(e)}), 500

@app.route('/api/etudiants/<numero>', methods=['DELETE'])
def delete_etudiant(numero):
    """Supprimer un étudiant"""
    try:
        # Vérifier si l'étudiant existe
        etudiant = db.obtenir_etudiant(numero)
        if not etudiant:
            return jsonify({'success': False, 'erreur': 'Étudiant introuvable'}), 404
        
        # Supprimer le fichier d'encodage s'il existe
        encodages_dir = os.path.join(os.path.dirname(__file__), '..', 'encodages')
        encoding_file = os.path.join(encodages_dir, f"{numero}.pkl")
        if os.path.exists(encoding_file):
            os.remove(encoding_file)
            logger.info(f"Encodage supprimé: {encoding_file}")
        
        # Supprimer la photo si elle existe
        if 'photo_path' in etudiant and etudiant['photo_path']:
            photo_path = etudiant['photo_path']
            if os.path.exists(photo_path):
                os.remove(photo_path)
                logger.info(f"Photo supprimée: {photo_path}")
        
        # Supprimer de la base de données
        result = db.supprimer_etudiant(numero)
        
        if result:
            # Recharger les encodages
            face_mgr.charger_encodages()
            
            return jsonify({
                'success': True,
                'message': f'Étudiant {numero} supprimé avec succès'
            }), 200
        else:
            return jsonify({'success': False, 'erreur': 'Erreur lors de la suppression'}), 500
            
    except Exception as e:
        logger.error(f"Error deleting student {numero}: {e}")
        return jsonify({'success': False, 'erreur': str(e)}), 500

#  COURS 

@app.route('/api/cours', methods=['GET'])
def get_cours():
    """Récupérer tous les cours"""
    try:
        cours = db.obtenir_tous_cours()
        for c in cours:
            c['_id'] = str(c['_id'])
            if 'date_creation' in c:
                c['date_creation'] = c['date_creation'].isoformat()
        
        return jsonify({
            'success': True,
            'count': len(cours),
            'data': cours
        }), 200
    except Exception as e:
        logger.error(f"Error getting courses: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/cours', methods=['POST'])
def add_cours():
    """Ajouter un nouveau cours"""
    try:
        data = request.json
        
        required = ['code_cours', 'nom', 'professeur']
        for field in required:
            if field not in data:
                return jsonify({'success': False, 'error': f'Champ requis: {field}'}), 400
        
        cours_id = db.ajouter_cours(
            data['code_cours'],
            data['nom'],
            data['professeur'],
            data.get('salle'),
            data.get('email_professeur')
        )
        
        if not cours_id:
            return jsonify({'success': False, 'error': 'Erreur lors de l\'ajout'}), 500
        
        return jsonify({
            'success': True,
            'id': cours_id,
            'message': 'Cours ajouté avec succès'
        }), 201
        
    except Exception as e:
        logger.error(f"Error adding course: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/cours/<code_cours>', methods=['DELETE'])
def delete_cours(code_cours):
    """Supprimer un cours"""
    try:
        # Vérifier si le cours existe
        cours = db.obtenir_cours(code_cours)
        if not cours:
            return jsonify({'success': False, 'erreur': 'Cours introuvable'}), 404
        
        # Supprimer le cours de la base de données
        result = db.supprimer_cours(code_cours)
        
        if result:
            return jsonify({
                'success': True,
                'message': f'Cours {code_cours} supprimé avec succès'
            }), 200
        else:
            return jsonify({'success': False, 'erreur': 'Erreur lors de la suppression'}), 500
            
    except Exception as e:
        logger.error(f"Error deleting course {code_cours}: {e}")
        return jsonify({'success': False, 'erreur': str(e)}), 500

# PRÉSENCES 

@app.route('/api/presences/video', methods=['POST'])
def enregistrer_presence_video():
    """Enregistrer la présence à partir d'une vidéo et envoyer email au professeur"""
    try:
        # Récupérer les données
        code_cours = request.form.get('code_cours')
        video = request.files.get('video')
        envoyer_email = request.form.get('envoyer_email', 'true').lower() == 'true'
        
        if not code_cours or not video:
            return jsonify({'success': False, 'error': 'Code cours et vidéo requis'}), 400
        
        # Récupérer les informations du cours
        cours = db.obtenir_cours(code_cours)
        if not cours:
            return jsonify({'success': False, 'error': 'Cours introuvable'}), 404
        
        # Sauvegarder temporairement la vidéo
        video_path = f'/tmp/presence_{code_cours}_{datetime.now().timestamp()}.mp4'
        video.save(video_path)
        
        logger.info(f" Analyse vidéo pour {code_cours}: {video.filename}")
        
        # Analyser la vidéo avec reconnaissance faciale
        etudiants_detectes = {}  # {id: nombre_detections}
        visages_inconnus = 0
        frames_analysees = 0
        
        try:
            # Ouvrir la vidéo
            video_capture = cv2.VideoCapture(video_path)
            frame_count = 0
            
            while video_capture.isOpened():
                ret, frame = video_capture.read()
                
                if not ret:
                    break
                
                # Analyser 1 frame sur 10 (pour la performance)
                frame_count += 1
                if frame_count % 10 != 0:
                    continue
                
                frames_analysees += 1
                
                # Convertir BGR (OpenCV) en RGB (face_recognition)
                rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Détecter les visages
                face_locations = face_recognition.face_locations(rgb_frame, model='hog')
                
                if not face_locations:
                    continue
                
                # Encoder les visages
                face_encodings = face_recognition.face_encodings(rgb_frame, face_locations)
                
                # Comparer avec les encodages connus
                for encoding in face_encodings:
                    if len(face_mgr.known_encodings) == 0:
                        visages_inconnus += 1
                        continue
                    
                    # Calculer les distances
                    face_distances = face_recognition.face_distance(
                        face_mgr.known_encodings,
                        encoding
                    )
                    
                    best_match_index = np.argmin(face_distances)
                    best_distance = face_distances[best_match_index]
                    
                    # Tolérance stricte
                    if best_distance < 0.5:
                        etudiant_id = face_mgr.known_ids[best_match_index]
                        
                        if etudiant_id in etudiants_detectes:
                            etudiants_detectes[etudiant_id] += 1
                        else:
                            etudiants_detectes[etudiant_id] = 1
                            logger.info(f" Étudiant détecté: {etudiant_id}")
                    else:
                        visages_inconnus += 1
            
            video_capture.release()
            
        except Exception as e:
            logger.error(f" Erreur analyse vidéo: {e}")
            import traceback
            traceback.print_exc()
        
        logger.info(f" Frames analysées: {frames_analysees}")
        logger.info(f" Détections: {etudiants_detectes}")
        logger.info(f" Visages inconnus: {visages_inconnus}")
        
        # Ne garder que les étudiants détectés au moins 3 fois
        presents_ids = [id for id, count in etudiants_detectes.items() if count >= 3]
        
        # Si personne n'est détecté 3 fois mais qu'il y a des détections, prendre ceux détectés au moins 1 fois
        if len(presents_ids) == 0 and len(etudiants_detectes) > 0:
            presents_ids = list(etudiants_detectes.keys())
        
        logger.info(f" Présents validés: {presents_ids}")
        
        # Récupérer les noms complets
        etudiants_presents = []
        for etud_id in presents_ids:
            etudiant = db.obtenir_etudiant(etud_id)
            if etudiant:
                nom_complet = f"{etudiant.get('nom', '')} {etudiant.get('prenom', '')}".strip()
                if not nom_complet:
                    nom_complet = etudiant.get('nom', etud_id)
                etudiants_presents.append(nom_complet)
            else:
                etudiants_presents.append(etud_id)
        
        # Enregistrer les présences
        if presents_ids:
            presence_id = db.ajouter_presence(
                code_cours,
                presents_ids,
                datetime.now()
            )
            logger.info(f" Présence vidéo enregistrée: {len(presents_ids)} présents")
        
        etudiants_absents = []  # Pas de notion d'absents sans liste d'inscrits
        
        # Envoyer email au professeur si demandé
        email_envoye = False
        email_destinataire = None
        
        if envoyer_email and cours.get('email_professeur'):
            email_destinataire = cours['email_professeur']
            success, message = envoyer_email_presence(
                email_destinataire,
                code_cours,
                cours.get('nom', 'Cours sans nom'),
                etudiants_presents,
                etudiants_absents,
                datetime.now().strftime('%d/%m/%Y à %H:%M')
            )
            email_envoye = success
            logger.info(f"Email {'envoyé' if success else 'non envoyé'}: {message}")
        
        # Nettoyer
        try:
            os.remove(video_path)
        except:
            pass
        
        return jsonify({
            'success': True,
            'etudiants_presents': etudiants_presents,
            'nombre_presents': len(etudiants_presents),
            'nombre_absents': len(etudiants_absents),
            'email_envoye': email_envoye,
            'email_destinataire': email_destinataire,
            'message': 'Présence enregistrée avec succès'
        }), 201
        
    except Exception as e:
        logger.error(f"Error recording video presence: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/presences/webcam', methods=['POST'])
def enregistrer_presence_webcam():
    """
    Enregistrer présence via frames webcam (capturées côté client)
    Compatible avec WSL2 - capture depuis le navigateur
    """
    try:
        code_cours = request.form.get('code_cours')
        frames = request.files.getlist('frames')
        
        if not code_cours:
            return jsonify({'erreur': 'Code cours requis'}), 400
        
        if not frames:
            return jsonify({'erreur': 'Aucune image reçue'}), 400
        
        # Obtenir le cours
        cours = db.obtenir_cours(code_cours)
        if not cours:
            return jsonify({'erreur': 'Cours introuvable'}), 404
        
        logger.info(f"Analyse webcam pour {code_cours}: {len(frames)} images reçues")
        
        # Analyser toutes les frames
        etudiants_detectes = {}  # {id: nombre_detections}
        visages_inconnus = 0
        
        for idx, frame_file in enumerate(frames):
            # Sauvegarder temporairement
            temp_path = f'/tmp/webcam_frame_{datetime.now().timestamp()}_{idx}.jpg'
            frame_file.save(temp_path)
            
            try:
                # Charger l'image
                image = face_recognition.load_image_file(temp_path)
                
                # Détecter les visages
                face_locations = face_recognition.face_locations(image, model='hog')
                
                if face_locations:
                    logger.info(f"Frame {idx+1}: {len(face_locations)} visage(s) détecté(s)")
                    
                    # Encoder les visages détectés
                    face_encodings = face_recognition.face_encodings(image, face_locations)
                    
                    # Comparer avec les encodages connus
                    for encoding in face_encodings:
                        if len(face_mgr.known_encodings) == 0:
                            logger.warning("Aucun encodage connu dans le système")
                            visages_inconnus += 1
                            continue
                        
                        # Calculer les distances avec TOUS les encodages
                        face_distances = face_recognition.face_distance(
                            face_mgr.known_encodings,
                            encoding
                        )
                        
                        # Trouver le meilleur match
                        best_match_index = np.argmin(face_distances)
                        best_distance = face_distances[best_match_index]
                        
                        # Tolérance stricte: 0.5 (plus bas = plus strict)
                        if best_distance < 0.5:
                            etudiant_id = face_mgr.known_ids[best_match_index]
                            
                            # Compter le nombre de fois qu'il est détecté
                            if etudiant_id in etudiants_detectes:
                                etudiants_detectes[etudiant_id] += 1
                            else:
                                etudiants_detectes[etudiant_id] = 1
                            
                            logger.info(f" Étudiant reconnu: {etudiant_id} (confiance: {1-best_distance:.2f}, distance: {best_distance:.3f})")
                        else:
                            visages_inconnus += 1
                            logger.info(f"Visage non reconnu (distance minimale: {best_distance:.3f})")
                else:
                    logger.info(f"Frame {idx+1}: Aucun visage détecté")
                
            except Exception as e:
                logger.warning(f"Erreur analyse frame {idx+1}: {e}")
                import traceback
                traceback.print_exc()
            
            # Supprimer le fichier temporaire
            try:
                os.remove(temp_path)
            except:
                pass
        
        # Ne garder que les étudiants détectés au moins 2 fois (pour éviter les faux positifs)
        presents = [id for id, count in etudiants_detectes.items() if count >= 2]
        
        # Si un étudiant n'est détecté qu'une fois mais qu'il n'y a qu'une personne, le garder
        if len(presents) == 0 and len(etudiants_detectes) == 1:
            presents = list(etudiants_detectes.keys())
        
        logger.info(f" Détections: {etudiants_detectes}")
        logger.info(f" Visages inconnus: {visages_inconnus}")
        logger.info(f" Présents validés: {presents}")
        logger.info(f" Détections: {etudiants_detectes}")
        logger.info(f" Visages inconnus: {visages_inconnus}")
        logger.info(f" Présents validés: {presents}")
        
        # Pour les absents: NE PAS utiliser tous les étudiants de la BDD
        # Car on ne sait pas qui est inscrit au cours
        # On considère simplement qu'il n'y a pas d'absents à notifier
        # (l'absence sera gérée par une liste d'inscrits au cours)
        absents = []
        
        # Enregistrer la présence
        presence_id = db.ajouter_presence(
            code_cours,
            presents,
            datetime.now()
        )
        
        logger.info(f"Présence webcam enregistrée: {len(presents)} présents")
        
        # Envoyer l'email au professeur
        email_envoye = False
        email_destinataire = None
        envoyer_email_param = request.form.get('envoyer_email', 'false').lower() == 'true'
        
        if envoyer_email_param and cours.get('email_professeur'):
            try:
                email_destinataire = cours['email_professeur']
                
                # Obtenir les noms complets des étudiants
                etudiants_presents_info = []
                for etud_id in presents:
                    etud = db.obtenir_etudiant(etud_id)
                    if etud:
                        etudiants_presents_info.append(etud.get('nom', etud_id))
                    else:
                        etudiants_presents_info.append(etud_id)
                
                etudiants_absents_info = []
                for etud_id in absents:
                    etud = db.obtenir_etudiant(etud_id)
                    if etud:
                        etudiants_absents_info.append(etud.get('nom', etud_id))
                    else:
                        etudiants_absents_info.append(etud_id)
                
                email_envoye, message = envoyer_email_presence(
                    email_destinataire,
                    code_cours,
                    cours.get('nom', code_cours),
                    etudiants_presents_info,
                    etudiants_absents_info,
                    datetime.now().strftime('%d/%m/%Y à %H:%M')
                )
                
                if email_envoye:
                    logger.info(f" Email envoyé à {email_destinataire}")
                else:
                    logger.warning(f" Échec envoi email à {email_destinataire}: {message}")
                    
            except Exception as e:
                logger.error(f"Erreur envoi email: {e}")
        
        return jsonify({
            'success': True,
            'presence_id': str(presence_id),
            'presents': etudiants_presents_info if envoyer_email_param else presents,
            'absents': etudiants_absents_info if envoyer_email_param else absents,
            'nb_presents': len(presents),
            'nb_absents': len(absents),
            'email_envoye': email_envoye,
            'email_destinataire': email_destinataire,
            'message': f'Présence enregistrée: {len(presents)} étudiant(s) reconnu(s)'
        }), 201
        
    except Exception as e:
        logger.error(f"Erreur présence webcam: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'erreur': str(e)}), 500

@app.route('/api/presences/recognize', methods=['POST'])
def recognize_face():
    """
    Reconnaissance de visage SANS enregistrement
    Utilisé pour la capture manuelle un par un
    """
    try:
        frames = request.files.getlist('frames')
        
        if not frames:
            return jsonify({'success': False, 'recognized': False, 'message': 'Aucune image reçue'}), 400
        
        logger.info(f" Reconnaissance: {len(frames)} image(s) reçue(s)")
        
        # Analyser toutes les frames
        etudiants_detectes = {}  # {id: nombre_detections}
        
        for idx, frame_file in enumerate(frames):
            # Sauvegarder temporairement
            temp_path = f'/tmp/recognize_frame_{datetime.now().timestamp()}_{idx}.jpg'
            frame_file.save(temp_path)
            
            try:
                # Charger l'image
                image = face_recognition.load_image_file(temp_path)
                
                # Détecter les visages
                face_locations = face_recognition.face_locations(image, model='hog')
                
                if face_locations:
                    # Encoder les visages détectés
                    face_encodings = face_recognition.face_encodings(image, face_locations)
                    
                    for encoding in face_encodings:
                        # Comparer avec tous les encodages connus
                        if len(face_mgr.known_encodings) == 0:
                            logger.warning(" Aucun encodage disponible")
                            continue
                        
                        face_distances = face_recognition.face_distance(face_mgr.known_encodings, encoding)
                        best_match_index = np.argmin(face_distances)
                        best_distance = face_distances[best_match_index]
                        
                        if best_distance < 0.5:  # Seuil strict
                            etudiant_id = face_mgr.known_ids[best_match_index]
                            confiance = 1 - best_distance
                            
                            etudiants_detectes[etudiant_id] = etudiants_detectes.get(etudiant_id, 0) + 1
                            
                            logger.info(f" Reconnu: {etudiant_id} (distance: {best_distance:.3f}, confiance: {confiance:.2f})")
                
                # Supprimer le fichier temporaire
                os.remove(temp_path)
                
            except Exception as e:
                logger.error(f"Erreur analyse frame {idx}: {e}")
                if os.path.exists(temp_path):
                    os.remove(temp_path)
        
        # Déterminer qui a été reconnu le plus souvent
        if etudiants_detectes:
            # Prendre l'étudiant avec le plus de détections
            best_student = max(etudiants_detectes.items(), key=lambda x: x[1])
            student_id = best_student[0]
            detections = best_student[1]
            
            # Récupérer les infos de l'étudiant
            etudiant = db.obtenir_etudiant(student_id)
            
            if etudiant:
                logger.info(f" Étudiant reconnu: {etudiant.get('nom')} ({student_id}) - {detections} détection(s)")
                
                return jsonify({
                    'success': True,
                    'recognized': True,
                    'student_id': student_id,
                    'student_name': etudiant.get('nom'),
                    'detections': detections,
                    'total_frames': len(frames)
                }), 200
        
        # Aucun visage reconnu
        logger.info(" Aucun visage reconnu")
        return jsonify({
            'success': True,
            'recognized': False,
            'message': 'Aucun visage reconnu'
        }), 200
        
    except Exception as e:
        logger.error(f"Erreur reconnaissance: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/presences/interactive/finalize', methods=['POST'])
def finalize_interactive_presence():
    """
    Finalise une session de présence interactive
    Enregistre tous les présents/absents
    """
    try:
        data = request.get_json()
        code_cours = data.get('code_cours')
        presents = data.get('presents', [])
        absents = data.get('absents', [])
        
        if not code_cours:
            return jsonify({'erreur': 'code_cours requis'}), 400
        
        logger.info(f" Finalisation session interactive pour {code_cours}")
        logger.info(f"   Présents: {len(presents)}, Absents: {len(absents)}")
        
        # Récupérer les infos du cours
        cours = db.obtenir_cours(code_cours)
        if not cours:
            return jsonify({'erreur': 'Cours non trouvé'}), 404
        
        # Enregistrer les présences
        presence_id = None
        if presents:
            presence_id = db.ajouter_presence(
                code_cours,
                presents,
                datetime.now()
            )
            logger.info(f" {len(presents)} présence(s) enregistrée(s)")
        
        # Envoyer l'email au professeur
        email_envoye = False
        email_destinataire = None
        
        if cours.get('email_professeur'):
            try:
                email_destinataire = cours['email_professeur']
                
                # Obtenir les noms complets des étudiants
                etudiants_presents_info = []
                for etud_id in presents:
                    etud = db.obtenir_etudiant(etud_id)
                    if etud:
                        etudiants_presents_info.append(etud.get('nom', etud_id))
                    else:
                        etudiants_presents_info.append(etud_id)
                
                etudiants_absents_info = []
                for etud_id in absents:
                    etud = db.obtenir_etudiant(etud_id)
                    if etud:
                        etudiants_absents_info.append(etud.get('nom', etud_id))
                    else:
                        etudiants_absents_info.append(etud_id)
                
                email_envoye, message = envoyer_email_presence(
                    email_destinataire,
                    code_cours,
                    cours.get('nom', code_cours),
                    etudiants_presents_info,
                    etudiants_absents_info,
                    datetime.now().strftime('%d/%m/%Y à %H:%M')
                )
                
                if email_envoye:
                    logger.info(f" Email envoyé à {email_destinataire}")
                else:
                    logger.warning(f" Échec envoi email: {message}")
                    
            except Exception as e:
                logger.error(f" Erreur envoi email: {e}")
        
        return jsonify({
            'success': True,
            'presence_id': str(presence_id) if presence_id else None,
            'nb_presents': len(presents),
            'nb_absents': len(absents),
            'email_envoye': email_envoye,
            'email_destinataire': email_destinataire,
            'message': f'Session terminée: {len(presents)} présent(s), {len(absents)} absent(s)'
        }), 201
        
    except Exception as e:
        logger.error(f" Erreur finalisation session: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'erreur': str(e)}), 500

# ==================== DÉMARRAGE ====================

if __name__ == '__main__':
    logger.info("🚀 Démarrage de l'API Backend...")
    logger.info(f"📊 MongoDB: {config.MONGODB_URI}")
    logger.info(f"🎯 Base: {config.DATABASE_NAME}")
    logger.info(f"👥 Étudiants encodés: {len(face_mgr.known_encodings)}")
    
    app.run(host='0.0.0.0', port=5000, debug=True)
