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
            "coordonnees": "Coordonnées non configurées"
        }

# Sauvegarder les préférences utilisateur
def sauvegarder_preferences_utilisateur(preferences):
    with open("preferences.json", "w") as f:
        json.dump(preferences, f, indent=4)

# Générer un code-barres
def generer_code_barre(numero, nom_fichier):
    if numero:
        code128 = barcode.get("code128", numero, writer=ImageWriter())
        chemin_fichier = f"{nom_fichier}.png"
        code128.save(chemin_fichier)
        return chemin_fichier
    return None

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

# Générer un PDF d'ordonnance
def generer_ordonnance_pdf(patient_data, preferences, decomposed_dose, unit_label):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", '', 12)
    
    if preferences.get("logo"):
        pdf.image(preferences["logo"], x=10, y=10, w=40)
    
    pdf.set_xy(10, 50)
    pdf.multi_cell(0, 10, f"{preferences['structure']}\n{preferences['adresse']}\nFINESS: {preferences['finess']}")
    finess_barcode = generer_code_barre(preferences["finess"], "finess_code")
    if finess_barcode:
        pdf.image(finess_barcode, x=10, y=80, w=50)
    
    pdf.set_xy(150, 50)
    pdf.multi_cell(0, 10, f"Dr. {preferences['medecin']}\nRPPS: {preferences['rpps']}")
    rpps_barcode = generer_code_barre(preferences["rpps"], "rpps_code")
    if rpps_barcode:
        pdf.image(rpps_barcode, x=150, y=80, w=50)
    
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
