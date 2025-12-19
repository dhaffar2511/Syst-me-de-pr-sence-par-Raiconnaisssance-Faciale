// Configuration API
const API_URL = 'http://localhost:5000';

// Navigation entre onglets
function showTab(tabName, event) {
    // Masquer tous les onglets
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    
    // Afficher l'onglet sélectionné
    document.getElementById(tabName).classList.add('active');
    if (event && event.target) {
        event.target.classList.add('active');
    }
    
    // Charger les données selon l'onglet
    if (tabName === 'etudiants') {
        loadStudents();
    } else if (tabName === 'cours') {
        loadCourses();
    } else if (tabName === 'presence') {
        loadAttendanceHistory();
        loadCoursesForSelect();
        loadCoursesForWebcam();
    }
}

// Afficher une notification
function showNotification(message, type = 'success') {
    const notification = document.getElementById('notification');
    notification.textContent = message;
    notification.className = `notification ${type}`;
    
    setTimeout(() => {
        notification.style.display = 'none';
    }, 4000);
}

// ========== GESTION DES ÉTUDIANTS ==========

// Charger la liste des étudiants
async function loadStudents() {
    try {
        const response = await fetch(`${API_URL}/api/etudiants`);
        const data = await response.json();
        
        const studentsList = document.getElementById('studentsList');
        
        // Utiliser le bon tableau selon la réponse
        const etudiants = data.etudiants || data.data || [];
        
        if (etudiants && etudiants.length > 0) {
            studentsList.innerHTML = etudiants.map(student => {
                // Gérer les différents noms de champs possibles
                const studentId = student.numero_etudiant || student.id_etudiant || student._id;
                const studentName = student.nom || student.nom_complet || 'Sans nom';
                const studentEmail = student.email || 'Non renseigné';
                
                return `
                    <div class="list-item">
                        <div class="list-item-info">
                            <h3>${studentName}</h3>
                            <p>ID: ${studentId} | Email: ${studentEmail}</p>
                        </div>
                        <div class="list-item-actions">
                            <button class="btn btn-danger" onclick="deleteStudent('${studentId}')">
                                🗑️ Supprimer
                            </button>
                        </div>
                    </div>
                `;
            }).join('');
        } else {
            studentsList.innerHTML = '<p style="text-align:center;color:#999;">Aucun étudiant enregistré</p>';
        }
    } catch (error) {
        console.error('Erreur:', error);
        showNotification('Erreur lors du chargement des étudiants', 'error');
    }
}

// Aperçu de la photo
document.getElementById('studentPhoto')?.addEventListener('change', function(e) {
    const file = e.target.files[0];
    if (file) {
        const reader = new FileReader();
        reader.onload = function(e) {
            const preview = document.getElementById('photoPreview');
            preview.innerHTML = `<img src="${e.target.result}" alt="Aperçu">`;
        };
        reader.readAsDataURL(file);
    }
});

// Ajouter un étudiant
document.getElementById('addStudentForm')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const formData = new FormData();
    formData.append('id_etudiant', document.getElementById('studentId').value);
    formData.append('nom', document.getElementById('studentName').value);
    formData.append('email', document.getElementById('studentEmail').value);
    formData.append('photo', document.getElementById('studentPhoto').files[0]);
    
    try {
        const response = await fetch(`${API_URL}/api/etudiants`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showNotification('✅ Étudiant ajouté avec succès!', 'success');
            this.reset();
            document.getElementById('photoPreview').innerHTML = '';
            loadStudents();
        } else {
            showNotification('❌ ' + (data.erreur || 'Erreur lors de l\'ajout'), 'error');
        }
    } catch (error) {
        console.error('Erreur:', error);
        showNotification('❌ Erreur de connexion au serveur', 'error');
    }
});

// Supprimer un étudiant
async function deleteStudent(studentId) {
    if (!confirm(`Voulez-vous vraiment supprimer l'étudiant ${studentId} ?`)) {
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/api/etudiants/${studentId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showNotification('✅ Étudiant supprimé avec succès', 'success');
            loadStudents();
        } else {
            showNotification('❌ ' + (data.erreur || 'Erreur lors de la suppression'), 'error');
        }
    } catch (error) {
        console.error('Erreur:', error);
        showNotification('❌ Erreur de connexion au serveur', 'error');
    }
}

// Recherche d'étudiants
document.getElementById('searchStudent')?.addEventListener('input', function(e) {
    const searchTerm = e.target.value.toLowerCase();
    const items = document.querySelectorAll('#studentsList .list-item');
    
    items.forEach(item => {
        const text = item.textContent.toLowerCase();
        item.style.display = text.includes(searchTerm) ? 'flex' : 'none';
    });
});

// ========== GESTION DES COURS ==========

// Charger la liste des cours
async function loadCourses() {
    try {
        const response = await fetch(`${API_URL}/api/cours`);
        const data = await response.json();
        
        const coursesList = document.getElementById('coursesList');
        
        // L'API retourne 'data' et non 'cours'
        const cours = data.data || data.cours || [];
        
        if (cours && cours.length > 0) {
            coursesList.innerHTML = cours.map(course => `
                <div class="list-item">
                    <div class="list-item-info">
                        <h3>${course.nom || course.nom_cours || 'Sans nom'}</h3>
                        <p>Code: ${course.code_cours} | Professeur: ${course.professeur || 'Non renseigné'}</p>
                    </div>
                    <div class="list-item-actions">
                        <button class="btn btn-danger" onclick="deleteCourse('${course.code_cours}')">
                            🗑️ Supprimer
                        </button>
                    </div>
                </div>
            `).join('');
        } else {
            coursesList.innerHTML = '<p style="text-align:center;color:#999;">Aucun cours enregistré</p>';
        }
    } catch (error) {
        console.error('Erreur:', error);
        showNotification('Erreur lors du chargement des cours', 'error');
    }
}

// Ajouter un cours
document.getElementById('addCourseForm')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const courseData = {
        code_cours: document.getElementById('courseId').value,
        nom: document.getElementById('courseName').value,
        professeur: document.getElementById('courseProf').value,
        email_professeur: document.getElementById('courseProfEmail').value
    };
    
    try {
        const response = await fetch(`${API_URL}/api/cours`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(courseData)
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showNotification('✅ Cours créé avec succès!', 'success');
            this.reset();
            loadCourses();
        } else {
            showNotification('❌ ' + (data.erreur || data.error || 'Erreur lors de la création'), 'error');
        }
    } catch (error) {
        console.error('Erreur:', error);
        showNotification('❌ Erreur de connexion au serveur', 'error');
    }
});

// Supprimer un cours
async function deleteCourse(courseId) {
    if (!confirm(`Voulez-vous vraiment supprimer le cours ${courseId} ?`)) {
        return;
    }
    
    try {
        const response = await fetch(`${API_URL}/api/cours/${courseId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            showNotification('✅ Cours supprimé avec succès', 'success');
            loadCourses();
        } else {
            showNotification('❌ ' + (data.erreur || 'Erreur lors de la suppression'), 'error');
        }
    } catch (error) {
        console.error('Erreur:', error);
        showNotification('❌ Erreur de connexion au serveur', 'error');
    }
}

// ========== GESTION DES PRÉSENCES ==========

// Charger les cours pour le sélecteur
async function loadCoursesForSelect() {
    try {
        const response = await fetch(`${API_URL}/api/cours`);
        const data = await response.json();
        
        const select = document.getElementById('attendanceCourse');
        const cours = data.data || data.cours || [];
        
        select.innerHTML = '<option value="">-- Choisir un cours --</option>';
        
        if (cours && cours.length > 0) {
            cours.forEach(course => {
                const option = document.createElement('option');
                option.value = course.code_cours;
                option.textContent = `${course.code_cours} - ${course.nom || course.nom_cours}`;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Erreur:', error);
    }
}

// Prendre la présence
document.getElementById('takeAttendanceForm')?.addEventListener('submit', async function(e) {
    e.preventDefault();
    
    const courseId = document.getElementById('attendanceCourse').value;
    const videoFile = document.getElementById('attendanceVideo').files[0];
    const sendEmail = document.getElementById('sendEmailToProf').checked;
    
    if (!courseId || !videoFile) {
        showNotification('⚠️ Veuillez remplir tous les champs', 'warning');
        return;
    }
    
    const formData = new FormData();
    formData.append('code_cours', courseId);
    formData.append('video', videoFile);
    formData.append('envoyer_email', 'true'); // Toujours envoyer l'email
    
    const resultBox = document.getElementById('attendanceResult');
    resultBox.className = 'result-box';
    resultBox.innerHTML = `
        <div style="text-align:center;">
            <div class="loading"></div>
            <p style="color:#2563eb; font-weight:bold; margin-top:10px;">⏳ Analyse de la vidéo en cours...</p>
            <p style="color:#666; font-size:0.9em;">Détection des visages dans la vidéo</p>
        </div>
    `;
    resultBox.style.display = 'block';
    
    try {
        const response = await fetch(`${API_URL}/api/presences/video`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            resultBox.className = 'result-box success';
            
            // Construire la liste des étudiants présents
            let studentsListHTML = '';
            if (data.etudiants_presents && data.etudiants_presents.length > 0) {
                studentsListHTML = `
                    <div style="background:#f0fdf4; padding:15px; border-radius:5px; margin:15px 0;">
                        <h4 style="color:#10b981; margin-bottom:10px;">👥 Étudiants Détectés (${data.etudiants_presents.length}):</h4>
                        <div style="display:grid; gap:8px;">
                            ${data.etudiants_presents.map(student => `
                                <div style="background:white; padding:10px; border-radius:5px; border-left:4px solid #10b981; display:flex; align-items:center;">
                                    <span style="font-size:1.2em; margin-right:10px;">✓</span>
                                    <strong style="color:#10b981;">${student}</strong>
                                    <span style="color:#666; margin-left:auto; font-size:0.9em;">Présent</span>
                                </div>
                            `).join('')}
                        </div>
                    </div>
                `;
            }
            
            let emailInfo = '';
            if (data.email_envoye) {
                emailInfo = `
                    <div style="background:#dcfce7; padding:12px; border-radius:5px; margin-top:10px; border-left:4px solid #10b981;">
                        <p style="margin:0; color:#059669;">
                            <span style="font-size:1.3em;">📧</span>
                            <strong style="margin-left:8px;">Email envoyé au professeur</strong>
                        </p>
                        <p style="margin:5px 0 0 0; color:#666; font-size:0.9em; padding-left:30px;">
                            → ${data.email_destinataire || 'Professeur'}
                        </p>
                    </div>
                `;
            }
            
            resultBox.innerHTML = `
                <h3 style="color:#10b981; margin-bottom:15px;">✅ Présence Enregistrée avec Succès!</h3>
                
                <div style="display:grid; grid-template-columns: 1fr 1fr; gap:10px; margin-bottom:15px;">
                    <div style="background:#f0fdf4; padding:15px; border-radius:8px; text-align:center; border:2px solid #10b981;">
                        <div style="font-size:2.5em; color:#10b981; font-weight:bold;">${data.etudiants_presents?.length || 0}</div>
                        <div style="color:#059669; font-weight:500;">Étudiants Présents</div>
                    </div>
                    <div style="background:#f9fafb; padding:15px; border-radius:8px; text-align:center; border:2px solid #e5e7eb;">
                        <div style="font-size:1.2em; color:#666; margin-bottom:5px;">📅 ${new Date().toLocaleDateString('fr-FR')}</div>
                        <div style="color:#666; font-size:0.9em;">${new Date().toLocaleTimeString('fr-FR')}</div>
                    </div>
                </div>
                
                ${studentsListHTML}
                ${emailInfo}
                
                <div style="background:#f0f9ff; padding:12px; border-radius:5px; margin-top:10px; text-align:center;">
                    <p style="margin:0; color:#2563eb;">
                        <strong>Cours:</strong> ${courseId}
                    </p>
                </div>
            `;
            this.reset();
            loadAttendanceHistory();
        } else {
            resultBox.className = 'result-box error';
            resultBox.innerHTML = `
                <h3 style="color:#ef4444;">❌ Erreur</h3>
                <p style="color:#666;">${data.erreur || 'Erreur lors de l\'enregistrement'}</p>
            `;
        }
    } catch (error) {
        console.error('Erreur:', error);
        resultBox.className = 'result-box error';
        resultBox.innerHTML = '<h3>❌ Erreur de connexion au serveur</h3>';
    }
});

// Charger l'historique des présences
async function loadAttendanceHistory() {
    try {
        const response = await fetch(`${API_URL}/api/presences`);
        const data = await response.json();
        
        const historyDiv = document.getElementById('attendanceHistory');
        
        if (data.presences && data.presences.length > 0) {
            historyDiv.innerHTML = data.presences.slice(0, 10).map(attendance => `
                <div class="list-item">
                    <div class="list-item-info">
                        <h3>Cours: ${attendance.code_cours}</h3>
                        <p>Date: ${new Date(attendance.date).toLocaleString('fr-FR')} | 
                           Présents: ${attendance.etudiants_presents?.length || 0}</p>
                    </div>
                </div>
            `).join('');
        } else {
            historyDiv.innerHTML = '<p style="text-align:center;color:#999;">Aucune présence enregistrée</p>';
        }
    } catch (error) {
        console.error('Erreur:', error);
    }
}

// ========== GESTION WEBCAM EN CONTINU ==========

let webcamStream = null;
let liveSession = {
    allStudents: [],
    presents: new Set(),
    courseId: null,
    currentDetected: null,
    isCapturing: false
};

// Démarrer la webcam et la reconnaissance continue
document.getElementById('startWebcam')?.addEventListener('click', async function() {
    try {
        // Vérifier qu'un cours est sélectionné
        const courseId = document.getElementById('webcamCourseId').value;
        if (!courseId) {
            showNotification('❌ Veuillez sélectionner un cours', 'error');
            return;
        }
        
        // Récupérer la liste de tous les étudiants
        const studentsRes = await fetch(`${API_URL}/api/etudiants`);
        const studentsData = await studentsRes.json();
        
        liveSession.allStudents = studentsData.data || studentsData.etudiants || [];
        liveSession.courseId = courseId;
        liveSession.presents = new Set();
        liveSession.currentDetected = null;
        liveSession.isCapturing = false;
        
        console.log('📚 Étudiants chargés:', liveSession.allStudents.length);
        console.log('IDs des étudiants:', liveSession.allStudents.map(s => s.numero_etudiant));
        
        // Demander l'accès à la webcam
        webcamStream = await navigator.mediaDevices.getUserMedia({ 
            video: { 
                width: { ideal: 640 },
                height: { ideal: 480 }
            } 
        });
        
        const video = document.getElementById('webcam');
        const placeholder = document.getElementById('webcamPlaceholder');
        
        video.srcObject = webcamStream;
        video.style.display = 'block';
        placeholder.style.display = 'none';
        
        // Afficher/masquer les boutons
        document.getElementById('startWebcam').style.display = 'none';
        document.getElementById('captureNextBtn').style.display = 'inline-block';
        document.getElementById('stopWebcam').style.display = 'inline-block';
        
        // Afficher la zone de reconnaissance en direct
        document.getElementById('liveRecognition').style.display = 'block';
        document.getElementById('currentRecognizedName').textContent = 'En attente...';
        document.getElementById('recognitionStatus').textContent = 'Placez-vous devant la webcam';
        
        // Initialiser l'affichage
        updateLiveDisplay();
        
        showNotification('✅ Webcam démarrée! Cliquez sur "Capturer Étudiant" pour reconnaître', 'success');
    } catch (error) {
        console.error('Erreur webcam:', error);
        let errorMsg = '❌ Impossible d\'accéder à la webcam';
        
        if (error.name === 'NotAllowedError') {
            errorMsg = '❌ Accès à la webcam refusé. Autorisez l\'accès dans votre navigateur.';
        } else if (error.name === 'NotFoundError') {
            errorMsg = '❌ Aucune webcam détectée sur votre appareil.';
        }
        
        showNotification(errorMsg, 'error');
    }
});

// Capturer l'étudiant suivant
document.getElementById('captureNextBtn')?.addEventListener('click', async function() {
    if (liveSession.isCapturing) return;
    
    liveSession.isCapturing = true;
    const button = this;
    button.disabled = true;
    button.textContent = '⏳ Analyse en cours...';
    
    document.getElementById('currentRecognizedName').textContent = 'Analyse en cours...';
    document.getElementById('recognitionStatus').textContent = '🔍 Recherche du visage...';
    
    try {
        const video = document.getElementById('webcam');
        const canvas = document.getElementById('webcamCanvas');
        const ctx = canvas.getContext('2d');
        
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;
        
        // Capturer 3 frames avec un petit délai
        const formData = new FormData();
        
        for (let i = 0; i < 3; i++) {
            ctx.drawImage(video, 0, 0);
            const blob = await new Promise(resolve => canvas.toBlob(resolve, 'image/jpeg', 0.9));
            formData.append('frames', blob, `frame_${i}.jpg`);
            if (i < 2) await new Promise(resolve => setTimeout(resolve, 200));
        }
        
        // Envoyer au serveur pour reconnaissance SEULEMENT
        const response = await fetch(`${API_URL}/api/presences/recognize`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        console.log('🔍 Données reconnaissance:', data);
        console.log('📚 Tous les étudiants IDs:', liveSession.allStudents.map(s => s.numero_etudiant));
        
        if (data.success && data.recognized) {
            const studentId = data.student_id;
            const studentName = data.student_name;
            
            console.log('✅ ID reconnu:', studentId, 'Type:', typeof studentId);
            console.log('🔎 Recherche dans allStudents...');
            
            // Chercher l'étudiant dans la liste chargée
            const foundStudent = liveSession.allStudents.find(s => {
                console.log('Comparaison:', s.numero_etudiant, '===', studentId, '?', s.numero_etudiant === studentId);
                return s.numero_etudiant === studentId || String(s.numero_etudiant) === String(studentId);
            });
            
            console.log('Étudiant trouvé?', foundStudent);
            
            // Utiliser l'ID exact de l'étudiant dans notre liste
            const normalizedId = foundStudent ? foundStudent.numero_etudiant : studentId;
            console.log('🎯 ID normalisé à stocker:', normalizedId);
            
            // Afficher le nom détecté
            document.getElementById('currentRecognizedName').textContent = studentName;
            document.getElementById('recognitionStatus').textContent = `✅ ID: ${normalizedId} (${data.detections}/${data.total_frames} détections)`;
            document.getElementById('currentRecognition').style.background = 'linear-gradient(135deg, #10b981 0%, #059669 100%)';
            
            liveSession.currentDetected = normalizedId;
            
            // Vérifier si déjà présent
            if (liveSession.presents.has(studentId)) {
                showNotification(`⚠️ ${studentName} déjà enregistré comme présent`, 'warning');
                document.getElementById('recognitionStatus').textContent = `⚠️ Déjà présent - ID: ${studentId}`;
            } else {
                showNotification(`✅ ${studentName} reconnu!`, 'success');
            }
            
            // Afficher le bouton "Suivant"
            document.getElementById('nextStudentBtn').style.display = 'inline-block';
        } else {
            // Aucun visage reconnu
            document.getElementById('currentRecognizedName').textContent = 'Aucun visage reconnu';
            document.getElementById('recognitionStatus').textContent = '❌ Réessayez ou passez au suivant';
            document.getElementById('currentRecognition').style.background = 'linear-gradient(135deg, #ef4444 0%, #dc2626 100%)';
            
            showNotification('❌ Aucun visage reconnu. Réessayez', 'error');
            
            // Afficher quand même le bouton "Suivant" pour pouvoir passer
            document.getElementById('nextStudentBtn').style.display = 'inline-block';
        }
        
    } catch (error) {
        console.error('Erreur capture:', error);
        document.getElementById('currentRecognizedName').textContent = 'Erreur';
        document.getElementById('recognitionStatus').textContent = '❌ Erreur de connexion';
        showNotification('❌ Erreur lors de la capture', 'error');
    } finally {
        liveSession.isCapturing = false;
        button.disabled = false;
        button.textContent = '👤 Capturer Étudiant';
    }
});

// Passer à l'étudiant suivant
document.getElementById('nextStudentBtn')?.addEventListener('click', function() {
    console.log('\n🔘 ========== BOUTON SUIVANT CLIQUÉ =========='  );
    console.log('Current detected:', liveSession.currentDetected, 'Type:', typeof liveSession.currentDetected);
    console.log('Presents AVANT ajout:', Array.from(liveSession.presents));
    console.log('Taille du Set AVANT:', liveSession.presents.size);
    
    // Ajouter l'étudiant détecté aux présents
    if (liveSession.currentDetected) {
        const alreadyPresent = liveSession.presents.has(liveSession.currentDetected);
        console.log('Déjà présent?', alreadyPresent);
        
        if (!alreadyPresent) {
            liveSession.presents.add(liveSession.currentDetected);
            console.log('✅ Étudiant ajouté au Set:', liveSession.currentDetected);
            console.log('Taille du Set APRÈS ajout:', liveSession.presents.size);
            console.log('Contenu du Set:', Array.from(liveSession.presents));
            
            const student = liveSession.allStudents.find(s => {
                const match = s.numero_etudiant === liveSession.currentDetected || 
                              String(s.numero_etudiant) === String(liveSession.currentDetected);
                console.log(`Recherche: ${s.numero_etudiant} === ${liveSession.currentDetected} ? ${match}`);
                return match;
            });
            console.log('Étudiant trouvé:', student);
            showNotification(`✅ ${student ? student.nom : liveSession.currentDetected} ajouté à la liste`, 'success');
        } else {
            console.log('⚠️ Déjà présent:', liveSession.currentDetected);
            showNotification(`⚠️ Déjà enregistré`, 'warning');
        }
    } else {
        console.log('❌ Aucun étudiant à ajouter (currentDetected est null)');
    }
    
    console.log('Presents APRÈS traitement:', Array.from(liveSession.presents));
    console.log('Taille finale du Set:', liveSession.presents.size);
    
    // Réinitialiser l'affichage
    document.getElementById('currentRecognizedName').textContent = 'En attente...';
    document.getElementById('recognitionStatus').textContent = 'Placez-vous devant la webcam';
    document.getElementById('currentRecognition').style.background = 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)';
    document.getElementById('nextStudentBtn').style.display = 'none';
    
    liveSession.currentDetected = null;
    
    // Mettre à jour l'affichage
    console.log('📊 Appel updateLiveDisplay()');
    updateLiveDisplay();
});

// Mettre à jour l'affichage en temps réel
function updateLiveDisplay() {
    console.log('\n📊 ========== UPDATE LIVE DISPLAY ==========');
    
    const presentsDiv = document.getElementById('livePresents');
    const absentsDiv = document.getElementById('liveAbsents');
    
    if (!presentsDiv || !absentsDiv) {
        console.error('Éléments livePresents ou liveAbsents introuvables');
        return;
    }
    
    console.log('État actuel:', {
        totalStudents: liveSession.allStudents.length,
        presentsSize: liveSession.presents.size,
        presentsArray: Array.from(liveSession.presents)
    });
    
    console.log('IDs dans allStudents:', liveSession.allStudents.map(s => ({
        id: s.numero_etudiant,
        nom: s.nom,
        type: typeof s.numero_etudiant
    })));
    
    // Calculer les absents (tous les étudiants - présents)
    const absents = liveSession.allStudents.filter(s => {
        const isPresent = liveSession.presents.has(s.numero_etudiant) || 
                         liveSession.presents.has(String(s.numero_etudiant));
        console.log(`Étudiant ${s.nom} (${s.numero_etudiant}): présent=${isPresent}`);
        return !isPresent;
    });
    
    console.log('❌ Absents calculés:', absents.length, absents.map(s => `${s.nom} (${s.numero_etudiant})`));
    console.log('✅ Présents:', liveSession.presents.size);
    
    // Mettre à jour les compteurs
    document.getElementById('livePresentsCount').textContent = liveSession.presents.size;
    document.getElementById('liveAbsentsCount').textContent = absents.length;
    
    // Afficher les présents
    presentsDiv.innerHTML = Array.from(liveSession.presents).map(id => {
        const student = liveSession.allStudents.find(s => s.numero_etudiant === id);
        return `
            <div style="padding: 8px; margin: 3px 0; background: white; border-radius: 5px; font-size: 0.9em;">
                <strong>✅ ${student ? student.nom : id}</strong>
            </div>
        `;
    }).join('') || '<p style="color:#999; text-align:center; font-size:0.9em;">Aucun</p>';
    
    // Afficher les absents
    absentsDiv.innerHTML = absents.map(student => {
        return `
            <div style="padding: 8px; margin: 3px 0; background: white; border-radius: 5px; font-size: 0.9em;">
                <strong>❌ ${student.nom}</strong>
            </div>
        `;
    }).join('') || '<p style="color:#999; text-align:center; font-size:0.9em;">Aucun</p>';
}

// Arrêter la webcam et enregistrer
document.getElementById('stopWebcam')?.addEventListener('click', async function() {
    if (!webcamStream) return;
    
    // Arrêter la webcam
    webcamStream.getTracks().forEach(track => track.stop());
    
    const video = document.getElementById('webcam');
    const placeholder = document.getElementById('webcamPlaceholder');
    
    video.srcObject = null;
    video.style.display = 'none';
    placeholder.style.display = 'flex';
    
    document.getElementById('startWebcam').style.display = 'inline-block';
    document.getElementById('captureNextBtn').style.display = 'none';
    document.getElementById('nextStudentBtn').style.display = 'none';
    document.getElementById('stopWebcam').style.display = 'none';
    document.getElementById('liveRecognition').style.display = 'none';
    
    // Enregistrer les présences
    if (liveSession.presents.size > 0) {
        try {
            showNotification('💾 Enregistrement en cours...', 'info');
            
            const absents = liveSession.allStudents
                .filter(s => !liveSession.presents.has(s.numero_etudiant))
                .map(s => s.numero_etudiant);
            
            const response = await fetch(`${API_URL}/api/presences/interactive/finalize`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    code_cours: liveSession.courseId,
                    presents: Array.from(liveSession.presents),
                    absents: absents
                })
            });
            
            const data = await response.json();
            
            if (data.success) {
                showNotification(`✅ Présence enregistrée: ${liveSession.presents.size} présent(s), ${absents.length} absent(s)`, 'success');
                
                if (data.email_envoye) {
                    showNotification(`📧 Email envoyé au professeur`, 'success');
                }
                
                // Afficher le résumé dans webcamStatus
                const statusDiv = document.getElementById('webcamStatus');
                const presentsList = Array.from(liveSession.presents).map(id => {
                    const student = liveSession.allStudents.find(s => s.numero_etudiant === id);
                    return student ? student.nom : id;
                }).join(', ');
                
                const absentsList = absents.map(id => {
                    const student = liveSession.allStudents.find(s => s.numero_etudiant === id);
                    return student ? student.nom : id;
                }).join(', ');
                
                statusDiv.innerHTML = `
                    <div style="background:#f0fdf4; border-left:4px solid #10b981; padding:15px; border-radius:5px; margin-top:15px;">
                        <h3 style="color:#10b981; margin:0 0 15px 0;">✅ Session Terminée</h3>
                        <div style="display:grid; grid-template-columns: 1fr 1fr; gap:10px; margin-bottom:15px;">
                            <div style="background:white; padding:10px; border-radius:5px; text-align:center;">
                                <div style="font-size:2em; color:#10b981;">✓ ${liveSession.presents.size}</div>
                                <div style="color:#666;">Présents</div>
                            </div>
                            <div style="background:white; padding:10px; border-radius:5px; text-align:center;">
                                <div style="font-size:2em; color:#ef4444;">✗ ${absents.length}</div>
                                <div style="color:#666;">Absents</div>
                            </div>
                        </div>
                        <details style="margin-top:10px;">
                            <summary style="cursor:pointer; color:#2563eb; font-weight:500;">Voir la liste complète</summary>
                            <div style="margin-top:10px; padding:10px; background:white; border-radius:5px;">
                                <p style="margin:5px 0;"><strong style="color:#10b981;">✓ Présents:</strong> ${presentsList || 'Aucun'}</p>
                                <p style="margin:5px 0;"><strong style="color:#ef4444;">✗ Absents:</strong> ${absentsList || 'Aucun'}</p>
                            </div>
                        </details>
                    </div>
                `;
                
                loadAttendanceHistory();
            } else {
                showNotification('❌ Erreur lors de l\'enregistrement', 'error');
            }
        } catch (error) {
            console.error('Erreur:', error);
            showNotification('❌ Erreur de connexion au serveur', 'error');
        }
    } else {
        showNotification('⏹️ Session arrêtée - Aucun étudiant détecté', 'warning');
    }
    
    // Réinitialiser la session
    liveSession = {
        allStudents: [],
        presents: new Set(),
        courseId: null,
        currentDetected: null,
        isCapturing: false
    };
});

// Charger les cours dans le select webcam
async function loadCoursesForWebcam() {
    try {
        const response = await fetch(`${API_URL}/api/cours`);
        const data = await response.json();
        
        const select = document.getElementById('webcamCourseId');
        const cours = data.data || data.cours || [];
        
        if (select) {
            select.innerHTML = '<option value="">-- Sélectionner un cours --</option>';
            cours.forEach(course => {
                const option = document.createElement('option');
                option.value = course.code_cours;
                option.textContent = `${course.code_cours} - ${course.nom || course.nom_cours}`;
                select.appendChild(option);
            });
        }
    } catch (error) {
        console.error('Erreur chargement cours:', error);
    }
}

// Charger les données au démarrage
window.addEventListener('DOMContentLoaded', () => {
    loadStudents();
    loadStatistics();
    loadCoursesForWebcam();
});
