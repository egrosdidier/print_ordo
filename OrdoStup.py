import streamlit as st
import csv
import json
import io
from fpdf import FPDF
from datetime import datetime
import os
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
            "logo": None
        }

# Sauvegarder les préférences utilisateur
def sauvegarder_preferences_utilisateur(preferences):
    with open("preferences.json", "w") as f:
        json.dump(preferences, f, indent=4)

# Convertir une date en toutes lettres
def date_en_toutes_lettres(date):
    mois = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
    return f"{num2words(date.day, lang='fr')} {mois[date.month - 1]} {num2words(date.year, lang='fr')}"

# Décomposer la posologie en unités disponibles
def decomposer_posologie(posologie, doses):
    distribution = {}
    for dose in doses:
        distribution[dose], posologie = divmod(posologie, dose)
    return distribution

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
