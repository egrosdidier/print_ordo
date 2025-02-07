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
            "logo": None
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
    return num2words(date.day, lang='fr') + " " + date.strftime("%B %Y")

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

if st.button("Générer l'ordonnance PDF"):
    preferences = charger_preferences_utilisateur()
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
    pdf.cell(0, 10, txt=f"Médicament: {patient_data['Medicament']}", ln=True, align="L")
    pdf.cell(0, 10, txt=f"Dose quotidienne: {num2words(patient_data['Posologie'], lang='fr')} mg", ln=True, align="L")
    pdf.cell(0, 10, txt=f"Traitement pour: {num2words(patient_data['Duree'], lang='fr')} jours", ln=True, align="L")
    pdf.cell(0, 10, txt=f"À délivrer tous les: {num2words(patient_data['Rythme_de_Delivrance'], lang='fr')} jours", ln=True, align="L")
    pdf.cell(0, 10, txt=f"Lieu de délivrance: {patient_data['Lieu_de_Delivrance']}", ln=True, align="L")
    
    buffer = io.BytesIO()
    buffer.write(pdf.output(dest="S").encode("latin1"))
    buffer.seek(0)
    st.download_button("Télécharger l'ordonnance", buffer, "ordonnance.pdf", "application/pdf")
