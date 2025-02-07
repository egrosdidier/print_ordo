import streamlit as st
import csv
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
            "logo": None,
            "coordonnees": "Coordonnées non configurées",
            "marges": {"haut": 20, "bas": 20, "gauche": 20, "droite": 20}
        }

# Générer un PDF d'ordonnance
def generer_ordonnance_pdf(patient_data, preferences):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_left_margin(preferences["marges"]["gauche"])
    pdf.set_right_margin(preferences["marges"]["droite"])
    pdf.set_top_margin(preferences["marges"]["haut"])

    # Ajouter les coordonnées
    pdf.set_font("Arial", size=10)
    pdf.ln(20)
    pdf.multi_cell(0, 10, preferences["coordonnees"])

    # Contenu ordonnance
    pdf.set_font("Arial", size=12)
    pdf.ln(10)
    pdf.cell(0, 10, txt=f"Nom du patient : {patient_data['Nom']} {patient_data['Prenom']}", ln=True, align="L")
    pdf.cell(0, 10, txt=f"Date : {datetime.now().strftime('%d/%m/%Y')}", ln=True, align="L")
    pdf.cell(0, 10, txt=f"Médicament : {patient_data['Medicament']}", ln=True, align="L")
    pdf.cell(0, 10, txt=f"Posologie : {patient_data['Posologie']} mg/j", ln=True, align="L")
    pdf.cell(0, 10, txt=f"Durée : {patient_data['Duree']} jours", ln=True, align="L")
    pdf.cell(0, 10, txt=f"Rythme de délivrance : Tous les {patient_data['Rythme_de_Delivrance']} jours", ln=True, align="L")
    pdf.cell(0, 10, txt=f"Chevauchement autorisé : {patient_data['Chevauchement']}", ln=True, align="L")
    pdf.cell(0, 10, txt=f"Délivrance : {patient_data['Lieu_de_Delivrance']}", ln=True, align="L")

    return pdf

# Interface Streamlit
st.title("Générateur d'ordonnances sécurisées")

# Modifier les préférences utilisateur
st.header("Paramètres")
coordonnees = st.text_area("Coordonnées", charger_preferences_utilisateur()["coordonnees"])
marge_haut = st.number_input("Marge haut (px)", value=20)
marge_bas = st.number_input("Marge bas (px)", value=20)
marge_gauche = st.number_input("Marge gauche (px)", value=20)
marge_droite = st.number_input("Marge droite (px)", value=20)

# Importer un fichier CSV
st.header("Importer un fichier CSV")
uploaded_file = st.file_uploader("Choisir un fichier CSV", type=["csv"])

if uploaded_file:
    patients = []
    csv_data = csv.DictReader(io.StringIO(uploaded_file.getvalue().decode("utf-8")))
    for row in csv_data:
        patients.append(row)
    
    # Générer les PDF
    buffer = io.BytesIO()
    pdf = FPDF()
    preferences = {
        "coordonnees": coordonnees,
        "marges": {"haut": marge_haut, "bas": marge_bas, "gauche": marge_gauche, "droite": marge_droite}
    }
    
    for patient in patients:
        single_pdf = generer_ordonnance_pdf(patient, preferences)
        buffer.write(single_pdf.output(dest="S").encode("latin1"))
    
    buffer.seek(0)
    st.download_button("Télécharger les ordonnances", buffer, "ordonnances.pdf", "application/pdf")
