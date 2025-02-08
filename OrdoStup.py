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

# Interface de saisie de l'ordonnance
st.header("Créer une ordonnance")

# Saisie des informations du patient
patient_data = {
    "Nom": st.text_input("Nom du patient"),
    "Prenom": st.text_input("Prénom du patient"),
    "Date_de_Naissance": st.date_input("Date de naissance", value=None, format="DD/MM/YYYY"),
}

# Calcul automatique de l'âge si une date de naissance est saisie
age = None
if patient_data["Date_de_Naissance"]:
    today = datetime.date.today()
    birth_date = patient_data["Date_de_Naissance"]
    age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    st.write(f"Âge : {age} ans")

# Autres champs du formulaire
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
    pdf = FPDF()
    pdf.add_page()
    pdf.set_left_margin(preferences["marges"]["gauche"])
    pdf.set_right_margin(preferences["marges"]["droite"])
    pdf.set_top_margin(preferences["marges"]["haut"])
    
    # Ajouter les informations de l'ordonnance
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, txt=f"Patient: {patient_data['Nom']} {patient_data['Prenom']}", ln=True, align="L")
    if age is not None:
        pdf.cell(0, 10, txt=f"Date de naissance: {patient_data['Date_de_Naissance']} (Âge: {age} ans)", ln=True, align="L")
    pdf.cell(0, 10, txt=f"Médicament: {patient_data['Medicament']}", ln=True, align="L")
    pdf.cell(0, 10, txt=f"Posologie: {patient_data['Posologie']} mg/j", ln=True, align="L")
    pdf.cell(0, 10, txt=f"Durée: {patient_data['Duree']} jours", ln=True, align="L")
    pdf.cell(0, 10, txt=f"Rythme de délivrance: Tous les {patient_data['Rythme_de_Delivrance']} jours", ln=True, align="L")
    pdf.cell(0, 10, txt=f"Lieu de délivrance: {patient_data['Lieu_de_Delivrance']}", ln=True, align="L")
    pdf.cell(0, 10, txt=f"Chevauchement autorisé: {patient_data['Chevauchement_Autorise']}", ln=True, align="L")
    
    buffer = io.BytesIO()
    buffer.write(pdf.output(dest="S").encode("latin1"))
    buffer.seek(0)
    st.download_button("Télécharger l'ordonnance", buffer, "ordonnance.pdf", "application/pdf")
