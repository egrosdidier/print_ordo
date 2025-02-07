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

# Sauvegarder les préférences utilisateur
def sauvegarder_preferences_utilisateur(preferences):
    with open("preferences.json", "w") as f:
        json.dump(preferences, f, indent=4)

# Interface Streamlit
st.title("Générateur d'ordonnances sécurisées")

if "afficher_preferences" not in st.session_state:
    st.session_state.afficher_preferences = False

if st.button("Modifier les préférences de la structure"):
    st.session_state.afficher_preferences = not st.session_state.afficher_preferences

if st.session_state.afficher_preferences:
    st.header("Paramètres de la structure")
    preferences = charger_preferences_utilisateur()
    
    preferences["structure"] = st.text_input("Nom de la structure", preferences["structure"])
    preferences["adresse"] = st.text_area("Adresse", preferences["adresse"])
    preferences["finess"] = st.text_input("Numéro FINESS", preferences["finess"])
    preferences["medecin"] = st.text_input("Nom du médecin", preferences["medecin"])
    preferences["rpps"] = st.text_input("Numéro RPPS", preferences["rpps"])
    preferences["logo"] = st.file_uploader("Logo de la structure (optionnel)", type=["png", "jpg", "jpeg"])

    if st.button("Enregistrer les préférences"):
        sauvegarder_preferences_utilisateur(preferences)
        st.success("Préférences enregistrées avec succès")

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
    
    # Vérification des champs obligatoires
    if not patient_data["Nom"] or not patient_data["Prenom"]:
        st.error("Veuillez renseigner le Nom et le Prénom du patient avant de générer l'ordonnance.")
    else:
        pdf = FPDF()
        pdf.add_page()
        nom = patient_data.get("Nom", "Nom inconnu")
        prenom = patient_data.get("Prenom", "Prénom inconnu")
        pdf.set_font("Arial", '', 12)
pdf.cell(0, 10, txt=f"Ordonnance générée pour {nom} {prenom}", ln=True, align="L")
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
        nom = patient.get("Nom", "Nom inconnu")
        prenom = patient.get("Prenom", "Prénom inconnu")
        single_pdf = FPDF()
        single_pdf.add_page()
        single_pdf.cell(0, 10, txt=f"Ordonnance générée pour {nom} {prenom}", ln=True, align="L")
        buffer.write(single_pdf.output(dest="S").encode("latin1"))
    
    buffer.seek(0)
    st.download_button("Télécharger les ordonnances", buffer, "ordonnances.pdf", "application/pdf")
