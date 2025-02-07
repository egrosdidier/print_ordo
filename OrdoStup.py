import streamlit as st
import csv
import json
import io
from fpdf import FPDF
from datetime import datetime
import barcode
from barcode.writer import ImageWriter
from num2words import num2words

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
            "marges": {"haut": 20, "bas": 20, "gauche": 20, "droite": 20}
        }

# Décomposer la posologie en unités disponibles
def decomposer_posologie(posologie, doses):
    distribution = {}
    for dose in doses:
        distribution[dose], posologie = divmod(posologie, dose)
    return distribution

# Générer un PDF d'ordonnance
def generer_ordonnance_pdf(patient_data, preferences, decomposed_dose):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", '', 12)
    
    if preferences.get("logo"):
        pdf.image(preferences["logo"], x=10, y=10, w=40)
    
    pdf.set_xy(10, 50)
    pdf.multi_cell(0, 10, f"{preferences['structure']}\n{preferences['adresse']}\nFINESS: {preferences['finess']}")
    
    pdf.set_xy(150, 10)
    pdf.multi_cell(0, 10, f"Dr. {preferences['medecin']}\nRPPS: {preferences['rpps']}")
    
    date_ordo = datetime.now().strftime("%d/%m/%Y")
    pdf.set_xy(10, 100)
    pdf.cell(0, 10, txt=f"Date: {date_ordo}", ln=True, align="L")
    
    pdf.cell(0, 10, txt=f"Patient: {patient_data['Nom']} {patient_data['Prenom']}", ln=True, align="L")
    pdf.ln(10)
    pdf.cell(0, 10, txt=f"Médicament: {patient_data['Medicament']}", ln=True, align="L")
    pdf.cell(0, 10, txt=f"Dose quotidienne: {num2words(patient_data['Posologie'], lang='fr')} milligrammes", ln=True, align="L")
    pdf.cell(0, 10, txt=f"Décomposition:", ln=True, align="L")
    for dose, qty in decomposed_dose.items():
        pdf.cell(0, 10, txt=f" - {qty} unités de {dose} mg", ln=True, align="L")
    
    return pdf

# Interface Streamlit
st.title("Générateur d'ordonnances sécurisées")

st.header("Créer une ordonnance manuellement")
patient_data = {
    "Nom": st.text_input("Nom du patient"),
    "Prenom": st.text_input("Prénom du patient"),
    "Medicament": st.selectbox("Médicament", ["METHADONE GELULES", "METHADONE SIROP", "BUPRENORPHINE HD", "SUBUTEX", "OROBUPRE"]),
    "Posologie": st.number_input("Posologie (mg/jour)", min_value=0),
    "Duree": st.number_input("Durée (jours)", min_value=0),
    "Rythme_de_Delivrance": st.number_input("Rythme de délivrance (jours)", min_value=0),
    "Lieu_de_Delivrance": st.text_input("Lieu de délivrance")
}

medicament_doses = {
    "METHADONE GELULES": [40, 20, 10, 5, 1],
    "METHADONE SIROP": [60, 40, 20, 10, 5, 1],
    "BUPRENORPHINE HD": [8, 6, 2],
    "SUBUTEX": [8, 2, 0.4],
    "OROBUPRE": [8, 2]
}

decomposed_dose = {}
if patient_data["Medicament"] in medicament_doses and patient_data["Posologie"] > 0:
    decomposed_dose = decomposer_posologie(patient_data["Posologie"], medicament_doses[patient_data["Medicament"]])
    st.subheader("Proposition de décomposition")
    for dose in medicament_doses[patient_data["Medicament"]]:
        decomposed_dose[dose] = st.number_input(f"Unités de {dose} mg", min_value=0, value=decomposed_dose.get(dose, 0))

if st.button("Générer l'ordonnance PDF"):
    preferences = charger_preferences_utilisateur()
    pdf = generer_ordonnance_pdf(patient_data, preferences, decomposed_dose)
    buffer = io.BytesIO()
    buffer.write(pdf.output(dest="S").encode("latin1"))
    buffer.seek(0)
    st.download_button("Télécharger l'ordonnance", buffer, "ordonnance.pdf", "application/pdf")
