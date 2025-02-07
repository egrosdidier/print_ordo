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

# Sauvegarder les préférences utilisateur
def sauvegarder_preferences_utilisateur(preferences):
    with open("preferences.json", "w") as f:
        json.dump(preferences, f, indent=4)

# Initialiser la variable de session si elle n'existe pas
if "afficher_preferences" not in st.session_state:
    st.session_state.afficher_preferences = False

# Interface Streamlit
st.title("Générateur d'ordonnances sécurisées")

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

# Décomposer la posologie en unités disponibles
def decomposer_posologie(posologie, doses):
    distribution = {}
    for dose in doses:
        distribution[dose], posologie = divmod(posologie, dose)
    return distribution

# Interface de saisie des patients
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
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", '', 12)
    pdf.cell(0, 10, txt=f"Patient: {patient_data['Nom']} {patient_data['Prenom']}", ln=True, align="L")
    pdf.cell(0, 10, txt=f"Médicament: {patient_data['Medicament']}", ln=True, align="L")
    pdf.cell(0, 10, txt=f"Soit:", ln=True, align="L")
    for dose, qty in decomposed_dose.items():
        if qty > 0:
            pdf.cell(0, 10, txt=f" - {num2words(qty, lang='fr')} {unit_labels[patient_data['Medicament']]} de {num2words(dose, lang='fr')} milligrammes", ln=True, align="L")
    buffer = io.BytesIO()
    buffer.write(pdf.output(dest="S").encode("latin1"))
    buffer.seek(0)
    st.download_button("Télécharger l'ordonnance", buffer, "ordonnance.pdf", "application/pdf")
