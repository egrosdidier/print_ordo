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

# Convertir une date en toutes lettres
def date_en_toutes_lettres(date):
    jours = ["premier", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf", "dix",
             "onze", "douze", "treize", "quatorze", "quinze", "seize", "dix-sept", "dix-huit", "dix-neuf",
             "vingt", "vingt et un", "vingt-deux", "vingt-trois", "vingt-quatre", "vingt-cinq", "vingt-six",
             "vingt-sept", "vingt-huit", "vingt-neuf", "trente", "trente et un"]
    mois = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
    jour_lettres = jours[date.day - 1]
    mois_lettres = mois[date.month - 1]
    return f"{jour_lettres} {mois_lettres} {date.year}"

# Décomposer la posologie en unités disponibles
def decomposer_posologie(posologie, doses):
    distribution = {}
    for dose in doses:
        distribution[dose], posologie = divmod(posologie, dose)
    return distribution

# Générer un PDF d'ordonnance
def generer_ordonnance_pdf(patient_data, preferences, decomposed_dose, unit_label):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", '', 12)
    
    if preferences.get("logo"):
        pdf.image(preferences["logo"], x=10, y=10, w=40)
    
    pdf.set_xy(10, 50)
    pdf.multi_cell(0, 10, f"{preferences['structure']}\n{preferences['adresse']}\nFINESS: {preferences['finess']}")
    
    pdf.set_xy(150, 50)
    pdf.multi_cell(0, 10, f"Dr. {preferences['medecin']}\nRPPS: {preferences['rpps']}")
    
    date_ordo = date_en_toutes_lettres(datetime.now())
    pdf.set_xy(10, 100)
    pdf.cell(0, 10, txt=f"Date: {date_ordo}", ln=True, align="L")
    
    pdf.cell(0, 10, txt=f"Patient: {patient_data['Nom']} {patient_data['Prenom']}", ln=True, align="L")
    pdf.ln(10)
    pdf.cell(0, 10, txt=f"Médicament: {patient_data['Medicament']}", ln=True, align="L")
    pdf.cell(0, 10, txt=f"Dose quotidienne: {num2words(patient_data['Posologie'], lang='fr')} mg", ln=True, align="L")
    pdf.cell(0, 10, txt=f"Traitement pour: {num2words(patient_data['Duree'], lang='fr')} jours", ln=True, align="L")
    pdf.cell(0, 10, txt=f"À délivrer tous les: {num2words(patient_data['Rythme_de_Delivrance'], lang='fr')} jours", ln=True, align="L")
    pdf.cell(0, 10, txt=f"Lieu de délivrance: {patient_data['Lieu_de_Delivrance']}", ln=True, align="L")
    pdf.ln(10)
    pdf.cell(0, 10, txt="Soit:", ln=True, align="L")
    for dose, qty in decomposed_dose.items():
        if qty > 0:
            pdf.cell(0, 10, txt=f" - {num2words(qty, lang='fr')} {unit_label} de {num2words(dose, lang='fr')} milligrammes", ln=True, align="L")
    
    return pdf

# Interface Streamlit
st.title("Générateur d'ordonnances sécurisées")

if st.button("Modifier les préférences de la structure"):
    st.header("Paramètres de la structure")
    preferences = charger_preferences_utilisateur()
    preferences["structure"] = st.text_input("Nom de la structure", preferences["structure"])
    preferences["adresse"] = st.text_area("Adresse", preferences["adresse"])
    preferences["finess"] = st.text_input("Numéro FINESS", preferences["finess"])
    preferences["medecin"] = st.text_input("Nom du médecin", preferences["medecin"])
    preferences["rpps"] = st.text_input("Numéro RPPS", preferences["rpps"])
    preferences["logo"] = st.file_uploader("Logo de la structure (optionnel)", type=["png", "jpg", "jpeg"])

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

unit_labels = {
    "METHADONE GELULES": "gélules",
    "METHADONE SIROP": "flacons",
    "BUPRENORPHINE HD": "comprimés",
    "SUBUTEX": "comprimés",
    "OROBUPRE": "comprimés"
}

decomposed_dose = {}
if patient_data["Medicament"] in unit_labels and patient_data["Posologie"] > 0:
    decomposed_dose = decomposer_posologie(patient_data["Posologie"], [40, 20, 10, 5, 1])

if st.button("Générer l'ordonnance PDF"):
    preferences = charger_preferences_utilisateur()
    pdf = generer_ordonnance_pdf(patient_data, preferences, decomposed_dose, unit_labels[patient_data["Medicament"]])
    buffer = io.BytesIO()
    buffer.write(pdf.output(dest="S").encode("latin1"))
    buffer.seek(0)
    st.download_button("Télécharger l'ordonnance", buffer, "ordonnance.pdf", "application/pdf")
