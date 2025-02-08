import streamlit as st
import json
import io
from fpdf import FPDF
from datetime import datetime

# Charger les préférences utilisateur
def charger_preferences_utilisateur():
    try:
        with open("preferences.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "structure": "Nom de la structure",
            "adresse": "Adresse non configurée",
            "finess": "",
            "medecin": "Nom du médecin",
            "rpps": "",
            "logo": None,
            "coordonnees": "Coordonnées non configurées",
            "marges": {
                "haut": 20,
                "bas": 20,
                "gauche": 20,
                "droite": 20
            }
        }

# Sauvegarder les préférences utilisateur
def sauvegarder_preferences_utilisateur(preferences):
    with open("preferences.json", "w") as f:
        json.dump(preferences, f, indent=4)

# Convertir une date en toutes lettres
def date_en_toutes_lettres(date):
    mois = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
    return f"{date.day} {mois[date.month - 1]} {date.year}"

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
preferences["logo"] = st.sidebar.file_uploader("Logo de la structure (PNG, JPG, JPEG)", type=["png", "jpg", "jpeg"])
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
    
    # Ajouter le logo en haut à gauche si disponible
    if preferences.get("logo"):
        logo_path = "logo_structure.png"
        with open(logo_path, "wb") as f:
            if preferences["logo"] is not None:
    logo_path = "logo_structure.png"
    with open(logo_path, "wb") as f:
        f.write(preferences["logo"].read())
else:
    from PIL import Image
    default_logo = Image.new('RGB', (200, 200), color='white')
    logo_path = "default_logo.png"
    default_logo.save(logo_path)
    logo_path = "logo_structure.png"
    with open(logo_path, "wb") as f:
        f.write(preferences["logo"].read())
        logo_path = "logo_structure.png"
        with open(logo_path, "wb") as f:
            f.write(preferences["logo"].read())
            with open(logo_path, "wb") as f:
                f.write(preferences["logo"].read())
            f.write(preferences["logo"].read())
    else:
        from PIL import Image
        default_logo = Image.new('RGB', (200, 200), color='white')
        logo_path = "default_logo.png"
        default_logo.save(logo_path)
        logo_path = "logo_structure.png"
        with open(logo_path, "wb") as f:
            f.write(preferences["logo"].read())
        pdf.image(logo_path, x=10, y=10, w=40)
        pdf.set_xy(10, 50)

        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, preferences["structure"], ln=True, align="L")
        pdf.set_font("Arial", '', 10)
        pdf.multi_cell(0, 5, preferences["adresse"], align="L")
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, preferences["structure"], ln=True, align="L")
    
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
