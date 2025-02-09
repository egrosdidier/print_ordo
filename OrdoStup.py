import streamlit as st
import json
import io
import os
import datetime
from fpdf import FPDF
from PIL import Image
from num2words import num2words
# Définir les préférences par défaut
defaut_preferences = {
    "structure": "Nom de la structure",
    "adresse": "Adresse de la structure",
    "finess": "Numéro FINESS",
    "medecin": "Nom du médecin",
    "rpps": "Numéro RPPS",
    "logo": None,
    "coordonnees": "Coordonnées complètes",
    "marges": {
        "haut": 20,
        "bas": 20,
        "gauche": 20,
        "droite": 20
    }
}
# Charger les préférences utilisateur
def charger_preferences_utilisateur():
    try:
        with open("preferences.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return defaut_preferences
# Sauvegarder les préférences utilisateur
def sauvegarder_preferences_utilisateur(preferences):
    with open("preferences.json", "w") as f:
        json.dump(preferences, f, indent=4)
# Interface Streamlit
st.title("Générateur d'ordonnances sécurisées")
# Interface de saisie des préférences
st.sidebar.header("Paramètres de la structure")
preferences = charger_preferences_utilisateur()
preferences["structure"] = st.sidebar.text_input("Nom de la structure", preferences["structure"])
preferences["adresse"] = st.sidebar.text_area("Adresse", preferences["adresse"])
preferences["finess"] = st.sidebar.text_input("Numéro FINESS", preferences["finess"])
preferences["medecin"] = st.sidebar.text_input("Nom du médecin", preferences["medecin"])
preferences["rpps"] = st.sidebar.text_input("Numéro RPPS", preferences["rpps"])
preferences["coordonnees"] = st.sidebar.text_area("Coordonnées", preferences["coordonnees"])
# Gestion du logo
defaut_logo_path = "logo_structure.png"
logo_uploaded = st.sidebar.file_uploader("Logo de la structure (PNG, JPG, JPEG)", type=["png", "jpg", "jpeg"])
if logo_uploaded:
    image = Image.open(logo_uploaded).convert("RGBA")
    white_background = Image.new("RGBA", image.size, (255, 255, 255, 255))
    image = Image.alpha_composite(white_background, image).convert("RGB")
    image.save(defaut_logo_path, format="PNG", optimize=True)
    preferences["logo"] = defaut_logo_path
else:
    preferences["logo"] = preferences.get("logo", None)

if st.sidebar.button("Sauvegarder les préférences"):
    sauvegarder_preferences_utilisateur(preferences)
    st.sidebar.success("Préférences enregistrées avec succès !")
# Interface de saisie de l'ordonnance
st.header("Créer une ordonnance")
# Saisie des informations du patient avec valeurs par défaut
patient_data = {
    "Civilite": st.selectbox("Civilité", ["Madame", "Monsieur"], index=1),
    "Nom": st.text_input("Nom du patient", value="NOM"),
    "Prenom": st.text_input("Prénom du patient", value="Prénom"),
    "Date_de_Naissance": st.date_input("Date de naissance", value=None, format="DD/MM/YYYY"),
  import re
}
def generer_num_secu_base(civilite, date_naissance):
    """Génère les 6 premiers chiffres du numéro de Sécurité Sociale."""
    if not date_naissance:
        return ""  # Pas de génération sans date
    
    sexe = "1" if civilite == "Monsieur" else "2"
    annee = f"{date_naissance.year % 100:02d}"  # Année sur 2 chiffres
    mois = f"{date_naissance.month:02d}"  # Mois sur 2 chiffres

    return f"{sexe}{annee}{mois}"  # Retourne 6 premiers chiffres

# Générer les 6 premiers chiffres par défaut
num_secu_base = generer_num_secu_base(patient_data["Civilite"], patient_data["Date_de_Naissance"])

# Permettre à l'utilisateur de modifier les 6 premiers chiffres
num_secu_base = st.text_input(
    "Premiers chiffres du Numéro de Sécurité Sociale (modifiable)", 
    value=num_secu_base, 
    max_chars=6,
    help="Les 6 premiers chiffres sont : Sexe (1/2) + Année (2 derniers chiffres) + Mois (2 chiffres)"
)
# Champ de saisie pour compléter les 7 derniers chiffres
reste_num_secu = st.text_input(
    "Complétez avec les 7 derniers chiffres", 
    value="",
    max_chars=7,
    help="Entrez les 7 derniers chiffres de votre N° SS"
)
# Vérification et assemblage du numéro complet
if re.fullmatch(r"\d{6}", num_secu_base) and re.fullmatch(r"\d{7}", reste_num_secu):
    patient_data["Numero_Securite_Sociale"] = num_secu_base + reste_num_secu
else:
    patient_data["Numero_Securite_Sociale"] = ""
    st.error("Le numéro doit contenir exactement 13 chiffres (6 + 7).")

# Fonction pour calculer la clé de Sécurité Sociale
def calculer_cle_securite_sociale(numero):
    """Calcule la clé de contrôle pour un numéro de Sécurité Sociale."""
    numero = re.sub(r"[^0-9]", "", numero)  # Supprime les espaces et caractères non numériques
    if len(numero) == 13 and numero.isdigit():
        return 97 - (int(numero) % 97)
    return None

# Calcul automatique de la clé
cle_secu = calculer_cle_securite_sociale(patient_data["Numero_Securite_Sociale"])

# Affichage du numéro formaté et de la clé de contrôle
if cle_secu is not None:
    st.success(f"N° SS : {patient_data['Numero_Securite_Sociale']} - Clé : {cle_secu:02d}")
# Liste déroulante des médicaments
medicament_options = [
    "METHADONE GELULES", "METHADONE SIROP", "BUPRENORPHINE HD", "SUBUTEX", "OROBUPRE",
    "SUBOXONE", "METHYLPHENIDATE", "CONCERTA", "QUASYM", "RITATINE LP",
    "RITALINE LI", "MEDIKINET", "(Champ libre)"
]
selected_medicament = st.selectbox("Médicament", medicament_options)
# Si l'utilisateur choisit "(Champ libre)", lui permettre d'entrer un médicament
if selected_medicament == "(Champ libre)":
    selected_medicament = st.text_input("Entrez le médicament")
# Assigner correctement la valeur au dictionnaire patient_data
patient_data["Medicament"] = selected_medicament if selected_medicament else "Non spécifié"
patient_data["Posologie"] = st.number_input("Posologie (mg/jour)", min_value=0)
patient_data["Duree"] = st.number_input("Durée (jours)", min_value=0)
patient_data["Rythme_de_Delivrance"] = st.number_input("Rythme de délivrance (jours)", min_value=0)
patient_data["Lieu_de_Delivrance"] = st.text_input("Lieu de délivrance")
patient_data["Chevauchement_Autorise"] = st.selectbox("Chevauchement autorisé", ["Oui", "Non"], index=1)
if st.button("Générer l'ordonnance PDF"):
    # Initialiser le document PDF avant toute action
    pdf = FPDF()
    pdf.add_page()
    pdf.set_left_margin(preferences["marges"]["gauche"])
    pdf.set_right_margin(preferences["marges"]["droite"])
    pdf.set_top_margin(preferences["marges"]["haut"])
    # Ajouter le logo (après l'initialisation de pdf)
    if preferences.get("logo") and os.path.exists(preferences["logo"]):
        try:
            pdf.image(preferences["logo"], x=10, y=10, w=40)
        except RuntimeError:
            st.warning("Erreur lors du chargement du logo : fichier invalide.")
    # pdf defini
    pdf.set_xy(10, 50)  # ✅ Plus d'erreur ici
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 5, preferences["structure"], ln=True, align="L")
    pdf.set_x(10)  # Réaligner l'adresse à gauche
    pdf.set_font("Arial", '', 9)
    pdf.cell(0, 5, preferences["adresse"], ln=True, align="L")
    pdf.set_x(10)  # Réaligner le FINESS à gauche
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 5, f"FINESS: {preferences['finess']}", ln=True, align="L")
# Bloc identification médecin   
    pdf.set_xy(150, 50)
# Écriture du nom du médecin en gras
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 5, preferences['medecin'], ln=True, align="C")
# Écriture du RPPS en standard mais dans la même cellule
    pdf.set_font("Arial", '', 10)
    pdf.set_x(150)  # Remet l'alignement en X à la position précédente
    pdf.cell(0, 5, f"RPPS: {preferences['rpps']}", ln=True, align="C")
# Afficher la date en toutes lettres
    from num2words import num2words
    jours_fr = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
    mois_fr = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
    maintenant = datetime.datetime.now()
    jour_lettres = num2words(maintenant.day, lang='fr')
    jour_semaine = jours_fr[maintenant.weekday()]
    mois_lettres = mois_fr[maintenant.month - 1]
    date_complete = f"{jour_semaine} {jour_lettres} {mois_lettres} {maintenant.year}"
# Définir le pdf
    pdf.set_xy(150, 70)
    pdf.set_font("Arial", 'B', 10)
# Vérification et formatage de la date de naissance
    if patient_data["Date_de_Naissance"]:
        date_naissance = patient_data["Date_de_Naissance"].strftime("%d/%m/%Y")
        today = datetime.date.today()
        birth_date = patient_data["Date_de_Naissance"]
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    else:
        date_naissance = "Non renseignée"
        age = "Non renseigné"
# Ecrire la date sur le PDF 
    pdf.cell(0, 5, date_complete, ln=True, align="R")
# Ecrire le infos patient sur le PDF
    pdf.cell(0, 10, txt=f"{patient_data['Civilite']} {patient_data['Nom']} {patient_data['Prenom']}", ln=True, align="R")
    pdf.set_y(pdf.get_y())  # Réduit l'espacement
    pdf.set_font("Arial", 'I', 9)
    pdf.cell(0, 5, f"Né(e) le : {date_naissance} (Âge: {age})", ln=True, align="R")
# Ajouter les informations de l'ordonnance
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 10, txt=f"{patient_data.get('Medicament', 'Non spécifié')}", ln=True, align="L")
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 5, txt=f"Posologie: {patient_data.get('Posologie', 'Non spécifiée')} mg/j", ln=True, align="L")
    pdf.cell(0, 5, txt=f"Durée: {patient_data.get('Duree', 'Non spécifiée')} jours", ln=True, align="L")
    pdf.cell(0, 5, txt=f"Rythme de délivrance: Tous les {patient_data.get('Rythme_de_Delivrance', 'Non spécifié')} jours", ln=True, align="L")
    pdf.cell(0, 10, txt=f"Lieu de délivrance: {patient_data.get('Lieu_de_Delivrance', 'Non spécifié')}", ln=True, align="L")
    pdf.cell(0, 5, txt=f"Chevauchement autorisé: {patient_data.get('Chevauchement_Autorise', 'Non spécifié')}", ln=True, align="L")
# Buffer
    buffer = io.BytesIO()
    buffer.write(pdf.output(dest="S").encode("latin1"))
    buffer.seek(0)
# Bouton télécharger
    st.download_button("Télécharger l'ordonnance", buffer, "ordonnance.pdf", "application/pdf")
