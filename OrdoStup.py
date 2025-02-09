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

# Saisie des informations du patient
patient_data = {
    "Civilite": st.selectbox("Civilité", ["Madame", "Monsieur"], index=1),
    "Nom": st.text_input("Nom du patient"),
    "Prenom": st.text_input("Prénom du patient"),
    "Date_de_Naissance": st.date_input("Date de naissance", value=None, format="DD/MM/YYYY"),
}

# Liste déroulante des médicaments
medicament_options = [
    "METHADONE GELULES", "METHADONE SIROP", "BUPRENORPHINE HD", "SUBUTEX", "OROBUPRE",
    "SUBOXONE", "METHYLPHENIDATE", "CONCERTA", "QUASYM", "RITATINE LP",
    "RITALINE LI", "MEDIKINET", "(Champ libre)"
]
selected_medicament = st.selectbox("Médicament", medicament_options)
if selected_medicament == "(Champ libre)":
    selected_medicament = st.text_input("Entrez le médicament")
    patient_data["Medicament"] = selected_medicament

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
    
    pdf.set_xy(150, 70)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 5, date_complete, ln=True, align="R")
    
    pdf.cell(0, 20, txt=f"{patient_data['Civilite']} {patient_data['Nom']} {patient_data['Prenom']}", ln=True, align="R")
   
# Ajouter la date de naissance et l'âge sous le nom du patient
    pdf.set_xy(10, pdf.get_y() + 5)
    pdf.set_font("Arial", '', 10)

# Vérification et formatage de la date de naissance
    if patient_data["Date_de_Naissance"]:
        date_naissance = patient_data["Date_de_Naissance"].strftime("%d/%m/%Y")
        today = datetime.date.today()
        birth_date = patient_data["Date_de_Naissance"]
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    else:
        date_naissance = "Non renseignée"
        age = "Non renseigné"

# Ecrire la date de naissance sur le PDF
    pdf.cell(0, 5, f"Date de naissance : {date_naissance} (Âge: {age})", ln=True, align="L")

# Ajouter les informations de l'ordonnance
pdf.set_font("Arial", 'B', 10)
pdf.cell(0, 5, txt=f"Médicament: {patient_data['Medicament']}", ln=True, align="L")
pdf.set_font("Arial", '', 10)
pdf.cell(0, 5, txt=f"Posologie: {patient_data['Posologie']} mg/j", ln=True, align="L")
pdf.cell(0, 5, txt=f"Durée: {patient_data['Duree']} jours", ln=True, align="L")
pdf.cell(0, 5, txt=f"Rythme de délivrance: Tous les {patient_data['Rythme_de_Delivrance']} jours", ln=True, align="L")
pdf.cell(0, 10, txt=f"Lieu de délivrance: {patient_data['Lieu_de_Delivrance']}", ln=True, align="L")
pdf.cell(0, 5, txt=f"Chevauchement autorisé: {patient_data['Chevauchement_Autorise']}", ln=True, align="L")
  
buffer = io.BytesIO()
buffer.write(pdf.output(dest="S").encode("latin1"))
buffer.seek(0)
st.download_button("Télécharger l'ordonnance", buffer, "ordonnance.pdf", "application/pdf")
