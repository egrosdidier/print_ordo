import streamlit as st
import json
import io
import os
from fpdf import FPDF
from datetime import datetime
from PIL import Image

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
    image = Image.open(logo_uploaded).convert("RGB")  # Assure un format sans inversion des couleurs
    image.save(defaut_logo_path, format="PNG", optimize=True)
    preferences["logo"] = defaut_logo_path
else:
    preferences["logo"] = preferences.get("logo", None)

preferences["marges"]["haut"] = st.sidebar.slider("Marge haut", 0, 50, preferences["marges"]["haut"])
preferences["marges"]["bas"] = st.sidebar.slider("Marge bas", 0, 50, preferences["marges"]["bas"])
preferences["marges"]["gauche"] = st.sidebar.slider("Marge gauche", 0, 50, preferences["marges"]["gauche"])
preferences["marges"]["droite"] = st.sidebar.slider("Marge droite", 0, 50, preferences["marges"]["droite"])
if st.sidebar.button("Sauvegarder les préférences"):
    sauvegarder_preferences_utilisateur(preferences)
    st.sidebar.success("Préférences enregistrées avec succès !")

# Interface de saisie de l'ordonnance
st.header("Créer une ordonnance")
patient_data = {
    "Nom": st.text_input("Nom du patient"),
    "Prenom": st.text_input("Prénom du patient"),
    "Medicament": st.text_input("Médicament"),
    "Posologie": st.number_input("Posologie (mg/jour)", min_value=0),
    "Duree": st.number_input("Durée (jours)", min_value=0),
    "Rythme_de_Delivrance": st.number_input("Rythme de délivrance (jours)", min_value=0),
    "Lieu_de_Delivrance": st.text_input("Lieu de délivrance")
}

if st.button("Générer l'ordonnance PDF"):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_left_margin(preferences["marges"]["gauche"])
    pdf.set_right_margin(preferences["marges"]["droite"])
    pdf.set_top_margin(preferences["marges"]["haut"])
    
    # Ajouter le logo et les informations de la structure
    if preferences.get("logo") and os.path.exists(preferences["logo"]):
        try:
            pdf.image(preferences["logo"], x=10, y=10, w=40)
        except RuntimeError:
            st.warning("Le fichier logo est invalide. Vérifiez le format de l'image.")
    else:
        st.warning("Aucun logo valide trouvé. Vérifiez le fichier dans vos préférences.")
    
    pdf.set_xy(10, 10 + 40 + 5)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(100, 5, preferences["structure"], ln=False, align="L")
    
    # Ajouter le nom du médecin et RPPS alignés à droite
    pdf.set_xy(150, 10 + 40 + 5)
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 5, preferences["medecin"], ln=True, align="R")
    pdf.set_xy(150, 10 + 40 + 10)
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 5, f"RPPS: {preferences['rpps']}", ln=True, align="R")
    pdf.set_x(150)
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 5, f"RPPS: {preferences['rpps']}", ln=True, align="R")  # Même hauteur que le nom de la structure
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 5, preferences["medecin"], ln=True, align="R")
    pdf.set_x(150)
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 5, f"RPPS: {preferences['rpps']}", ln=True, align="R")
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 5, preferences["structure"], ln=True, align="L")
    pdf.set_font("Arial", '', 9)
    pdf.set_x(10)
    pdf.multi_cell(0, 5, preferences["adresse"], align="L")
    pdf.set_font("Arial", '', 10)
    pdf.set_x(10)
    pdf.cell(0, 5, f"FINESS: {preferences['finess']}", ln=True, align="L")
    
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, txt=f"Patient: {patient_data['Nom']} {patient_data['Prenom']}", ln=True, align="L")
    pdf.cell(0, 10, txt=f"Médicament: {patient_data['Medicament']}", ln=True, align="L")
    pdf.cell(0, 10, txt=f"Posologie: {patient_data['Posologie']} mg/j", ln=True, align="L")
    pdf.cell(0, 10, txt=f"Durée: {patient_data['Duree']} jours", ln=True, align="L")
    pdf.cell(0, 10, txt=f"Rythme de délivrance: Tous les {patient_data['Rythme_de_Delivrance']} jours", ln=True, align="L")
    pdf.cell(0, 10, txt=f"Lieu de délivrance: {patient_data['Lieu_de_Delivrance']}", ln=True, align="L")
    
    buffer = io.BytesIO()
    buffer.write(pdf.output(dest="S").encode("latin1"))
    buffer.seek(0)
    st.download_button("Télécharger l'ordonnance", buffer, "ordonnance.pdf", "application/pdf")
