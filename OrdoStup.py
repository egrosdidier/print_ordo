import streamlit as st
import csv
import json
import io
from fpdf import FPDF
from datetime import datetime
import barcode
from barcode.writer import ImageWriter

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

# Générer un code-barres
def generer_code_barre(numero, nom_fichier):
    if numero:
        code128 = barcode.get("code128", numero, writer=ImageWriter())
        chemin_fichier = f"{nom_fichier}.png"
        code128.save(chemin_fichier)
        return chemin_fichier
    return None

# Générer un PDF d'ordonnance
def generer_ordonnance_pdf(patient_data, preferences):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_left_margin(preferences["marges"]["gauche"])
    pdf.set_right_margin(preferences["marges"]["droite"])
    pdf.set_top_margin(preferences["marges"]["haut"])

    # Ajouter le logo si disponible
    if preferences.get("logo"):
        pdf.image(preferences["logo"], x=10, y=10, w=40)

    # Ajouter les coordonnées et informations structure
    pdf.set_font("Arial", size=10)
    pdf.ln(20)
    pdf.multi_cell(0, 10, f"{preferences['structure']}\n{preferences['adresse']}\nMédecin: {preferences['medecin']}")
    
    # Ajouter les codes-barres pour FINESS et RPPS
    finess_barcode = generer_code_barre(preferences["finess"], "finess_code")
    rpps_barcode = generer_code_barre(preferences["rpps"], "rpps_code")
    
    if finess_barcode:
        pdf.image(finess_barcode, x=10, y=pdf.get_y(), w=50)
        pdf.ln(15)
    if rpps_barcode:
        pdf.image(rpps_barcode, x=10, y=pdf.get_y(), w=50)
        pdf.ln(15)
    
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

# Formulaire de saisie manuelle d'une ordonnance
st.header("Créer une ordonnance manuellement")
patient_data = {
    "Nom": st.text_input("Nom du patient"),
    "Prenom": st.text_input("Prénom du patient"),
    "Medicament": st.text_input("Médicament"),
    "Posologie": st.number_input("Posologie (mg/jour)", min_value=0),
    "Duree": st.number_input("Durée (jours)", min_value=0),
    "Rythme_de_Delivrance": st.number_input("Rythme de délivrance (jours)", min_value=0),
    "Chevauchement": st.checkbox("Chevauchement autorisé"),
    "Lieu_de_Delivrance": st.text_input("Lieu de délivrance")
}

if st.button("Générer l'ordonnance PDF"):
    preferences = charger_preferences_utilisateur()
    pdf = generer_ordonnance_pdf(patient_data, preferences)
    buffer = io.BytesIO()
    buffer.write(pdf.output(dest="S").encode("latin1"))
    buffer.seek(0)
    st.download_button("Télécharger l'ordonnance", buffer, "ordonnance.pdf", "application/pdf")

# Importer un fichier CSV
st.header("Importer un fichier CSV")
uploaded_file = st.file_uploader("Choisir un fichier CSV", type=["csv"])

if uploaded_file:
    patients = []
    csv_data = csv.DictReader(io.StringIO(uploaded_file.getvalue().decode("utf-8")))
    for row in csv_data:
        patients.append(row)
    
    buffer = io.BytesIO()
    pdf = FPDF()
    
    for patient in patients:
        single_pdf = generer_ordonnance_pdf(patient, preferences)
        buffer.write(single_pdf.output(dest="S").encode("latin1"))
    
    buffer.seek(0)
    st.download_button("Télécharger les ordonnances", buffer, "ordonnances.pdf", "application/pdf")
