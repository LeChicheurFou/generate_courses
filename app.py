import streamlit as st
import os
from datetime import datetime, timedelta
from backend import CourseGenerator
import time
from dotenv import load_dotenv

# Charger les variables d'environnement depuis .env
load_dotenv()

# Configuration de la page
st.set_page_config(
    page_title="Générateur de Cours IA",
    page_icon="📚",
    layout="wide"
)

# Initialisation du session state
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
if 'login_attempts' not in st.session_state:
    st.session_state.login_attempts = {}

# Fonction de sécurité anti-brute-force
def check_login_attempts(username):
    now = datetime.now()
    if username in st.session_state.login_attempts:
        attempts = st.session_state.login_attempts[username]
        # Nettoyer les tentatives de plus d'1 heure
        attempts = [t for t in attempts if now - t < timedelta(hours=1)]
        st.session_state.login_attempts[username] = attempts
        
        if len(attempts) >= 5:
            return False, "Trop de tentatives. Réessayez dans 1 heure."
    return True, ""

def record_failed_attempt(username):
    if username not in st.session_state.login_attempts:
        st.session_state.login_attempts[username] = []
    st.session_state.login_attempts[username].append(datetime.now())

# Page de connexion
def login_page():
    st.title("🔐 Connexion Sécurisée")
    
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("### Accédez au générateur de cours")
        
        username = st.text_input("Nom d'utilisateur", key="username")
        password = st.text_input("Mot de passe", type="password", key="password")
        
        if st.button("Se connecter", use_container_width=True):
            can_login, message = check_login_attempts(username)
            
            if not can_login:
                st.error(message)
                return
            
            # Vérification depuis le fichier .env
            correct_username = os.getenv("APP_USERNAME")
            correct_password = os.getenv("APP_PASSWORD")
            
            if not correct_username or not correct_password:
                st.error("❌ Erreur: APP_USERNAME ou APP_PASSWORD non configurés dans .env")
                st.stop()
            
            if username == correct_username and password == correct_password:
                st.session_state.authenticated = True
                st.success("✅ Connexion réussie!")
                time.sleep(0.5)
                st.rerun()
            else:
                record_failed_attempt(username)
                remaining = 5 - len(st.session_state.login_attempts.get(username, []))
                st.error(f"❌ Identifiants incorrects. {remaining} tentatives restantes.")

# Application principale
def main_app():
    # Header
    st.markdown("""
        <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                    padding: 2rem; border-radius: 10px; margin-bottom: 2rem;'>
            <h1 style='color: white; margin: 0;'>📚 Générateur de Cours IA</h1>
            <p style='color: #e0e0e0; margin: 0.5rem 0 0 0;'>
                Transformez vos images en cours structurés instantanément
            </p>
        </div>
    """, unsafe_allow_html=True)
    
    # Bouton de déconnexion
    col1, col2 = st.columns([6, 1])
    with col2:
        if st.button("🚪 Déconnexion"):
            st.session_state.authenticated = False
            st.rerun()
    
    # Vérification de la clé API
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        st.error("❌ Clé API Mistral non configurée! Ajoutez-la dans le fichier .env")
        st.stop()
    
    # Upload d'image ou PDF
    st.markdown("### 📤 Étape 1: Chargez votre fichier")
    uploaded_file = st.file_uploader(
        "Glissez votre image ou PDF ici",
        type=['png', 'jpg', 'jpeg', 'webp', 'pdf'],
        help="Formats acceptés: PNG, JPG, JPEG, WEBP, PDF"
    )
    
    if uploaded_file:
        col1, col2 = st.columns([1, 1])
        
        with col1:
            st.markdown("#### 🖼️ Aperçu du fichier")
            
            # Afficher selon le type de fichier
            if uploaded_file.type == "application/pdf":
                st.info("📄 Fichier PDF chargé")
                st.write(f"**Nom:** {uploaded_file.name}")
                st.write(f"**Taille:** {uploaded_file.size / 1024:.2f} KB")
            else:
                st.image(uploaded_file, use_container_width=True)
        
        with col2:
            st.markdown("#### ⚙️ Génération du cours")
            
            if st.button("🚀 Générer le cours", use_container_width=True, type="primary"):
                try:
                    with st.spinner("🔄 Analyse en cours... Cela peut prendre 30-60 secondes"):
                        generator = CourseGenerator(api_key)
                        
                        # Analyse selon le type de fichier
                        if uploaded_file.type == "application/pdf":
                            course_text = generator.analyze_pdf(uploaded_file)
                        else:
                            course_text = generator.analyze_image(uploaded_file)
                        
                        # Génération du PDF
                        pdf_path = generator.generate_pdf(course_text, "cours_genere.pdf")
                    
                    st.success("✅ Cours généré avec succès!")
                    
                    # Affichage du texte
                    st.markdown("### 📝 Contenu du cours")
                    with st.expander("Voir le texte complet", expanded=True):
                        st.markdown(course_text)
                    
                    # Téléchargement du PDF
                    st.markdown("### 📥 Téléchargement")
                    with open(pdf_path, "rb") as file:
                        st.download_button(
                            label="📄 Télécharger le PDF",
                            data=file,
                            file_name=f"cours_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                            mime="application/pdf",
                            use_container_width=True
                        )
                    
                    # Nettoyage
                    os.remove(pdf_path)
                    
                except Exception as e:
                    st.error(f"❌ Erreur: {str(e)}")

# Point d'entrée
if not st.session_state.authenticated:
    login_page()
else:
    main_app()