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
# Fonction decomposer les posologies
import re
def decomposer_posologie(medicament, dose_totale):
    """Décompose la posologie en fonction des unités disponibles pour chaque médicament."""
    
    decompositions = {
        "METHADONE GELULES": [40, 20, 10, 5, 1],
        "METHADONE SIROP": [60, 40, 20, 10, 5, 1],
        "BUPRENORPHINE HD": [8, 6, 2],
        "SUBUTEX": [8, 2, 0.4],
        "OROBUPRE": [8, 2]
    }

    if medicament not in decompositions or dose_totale <= 0:
        return {}

    result = {}
    reste = dose_totale

    for unite in decompositions[medicament]:
        if reste >= unite:
            quantite = reste // unite
            reste = reste % unite
            result[unite] = quantite

    return result  # Retourne un dictionnaire {unité: quantité}
    
# Fonction posologie en toutes lettes
from num2words import num2words
def posologie_en_toutes_lettres(posologie):
"""Convertit une posologie en toutes lettres."""
    if posologie > 0:
        return num2words(posologie, lang='fr')
    return "zéro"
    
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
# Gestion du logo
defaut_logo_path = "logo_structure.png"
logo_uploaded = st.sidebar.file_uploader("Logo de la structure (PNG, JPG, JPEG)", type=["png", "jpg", "jpeg"])
if logo_uploaded:
    image = Image.open(logo_uploaded).convert("RGBA")
    white_background = Image.new("RGBA", image.size, (255, 255, 255, 255))
    image = Image.alpha_composite(white_background, image).convert("RGB")
    image.save(defaut_logo_path, format="PNG", optimize=True)
    preferences["logo"] = defaut_logo_path
else:
    preferences["logo"] = preferences.get("logo", None)

if st.sidebar.button("Sauvegarder les préférences"):
    sauvegarder_preferences_utilisateur(preferences)
    st.sidebar.success("Préférences enregistrées avec succès !")
# Interface de saisie de l'ordonnance
st.header("Créer une ordonnance")
# Saisie des informations du patient avec valeurs par défaut
patient_data = {
    "Civilite": st.selectbox("Civilité", ["Madame", "Monsieur"], index=1),
    "Nom": st.text_input("Nom du patient", value="NOM"),
    "Prenom": st.text_input("Prénom du patient", value="Prénom"),
    "Date_de_Naissance": st.date_input("Date de naissance", value=None, format="DD/MM/YYYY"),
}
from datetime import date

def calculer_age(date_naissance):
    """Calcule l'âge à partir de la date de naissance."""
    if date_naissance:
        today = date.today()
        age = today.year - date_naissance.year - ((today.month, today.day) < (date_naissance.month, date_naissance.day))
        return age
    return None  # Si la date est vide

# Calcul de l'âge si une date est saisie
age_patient = calculer_age(patient_data["Date_de_Naissance"])

# Affichage de l'âge sous la date de naissance
if age_patient is not None:
    st.info(f"Âge du patient : {age_patient} ans")

# Numéro sécurité sociale
import re

def generer_num_secu_base(civilite, date_naissance):
    """Génère les 5 premiers chiffres du numéro de Sécurité Sociale."""
    if not date_naissance:
        return ""  # Pas de génération sans date
    
    sexe = "1" if civilite == "Monsieur" else "2"
    annee = f"{date_naissance.year % 100:02d}"  # Année sur 2 chiffres
    mois = f"{date_naissance.month:02d}"  # Mois sur 2 chiffres
    return f"{sexe}{annee}{mois}"  # Retourne 5 premiers chiffres

def formater_num_secu(numero):
    """Ajoute des espaces au format 0 00 00 00 000 000."""
    numero = re.sub(r"[^0-9]", "", numero)  # Supprime les caractères non numériques
    if len(numero) == 13:  # Vérifie que le numéro est bien valide
        return f"{numero[0]} {numero[1:3]} {numero[3:5]} {numero[5:7]} {numero[7:10]} {numero[10:13]}"
    return numero  # Retourne tel quel si le format est incorrect

# Fonction pour calculer la clé de Sécurité Sociale
def calculer_cle_securite_sociale(numero):
    """Calcule la clé de contrôle pour un numéro de Sécurité Sociale."""
    numero = re.sub(r"[^0-9]", "", numero)  # Supprime les espaces et caractères non numériques
    if len(numero) == 13 and numero.isdigit():
        return 97 - (int(numero) % 97)
    return None  # ✅ Retourne None si invalide

# Générer les 5 premiers chiffres par défaut
num_secu_base = generer_num_secu_base(patient_data["Civilite"], patient_data["Date_de_Naissance"])

# Champ de saisie pour entrer/modifier les 13 chiffres du N° SS
num_secu_complet = st.text_input(
    "Numéro de Sécurité Sociale (13 chiffres)", 
    value=num_secu_base, 
    max_chars=13,
    help="Les 5 premiers chiffres sont pré-remplis : Sexe (1/2) + Année (2 derniers chiffres) + Mois (2 chiffres). Complétez les 8 autres."
)

# Vérification si 13 chiffres sont bien saisis
cle_secu = None  # Valeur par défaut avant validation complète
num_secu_formatte = ""  # Initialisation
if len(num_secu_complet) == 13 and re.fullmatch(r"\d{13}", num_secu_complet):
    patient_data["Numero_Securite_Sociale"] = num_secu_complet
    cle_secu = calculer_cle_securite_sociale(patient_data["Numero_Securite_Sociale"])
    num_secu_formatte = formater_num_secu(patient_data["Numero_Securite_Sociale"])  # Formate le numéro

# Affichage du numéro formaté et de la clé de contrôle uniquement si complet
if cle_secu is not None:
    st.success(f"N° SS : {num_secu_formatte} - Clé : {cle_secu:02d}")
# Liste déroulante des médicaments
medicament_options = [
    "METHADONE GELULES", "METHADONE SIROP", "BUPRENORPHINE HD", "SUBUTEX", "OROBUPRE",
    "SUBOXONE", "METHYLPHENIDATE", "CONCERTA", "QUASYM", "RITATINE LP",
    "RITALINE LI", "MEDIKINET", "(Champ libre)"
]
selected_medicament = st.selectbox("Médicament", medicament_options)
# Si l'utilisateur choisit "(Champ libre)", lui permettre d'entrer un médicament
if selected_medicament == "(Champ libre)":
    selected_medicament = st.text_input("Entrez le médicament")
# Assigner correctement la valeur au dictionnaire patient_data
patient_data["Medicament"] = selected_medicament if selected_medicament else "Non spécifié"
patient_data["Posologie"] = st.number_input("Posologie (mg/jour)", min_value=0)
# Décomposition automatique de la posologie
decomposition = decomposer_posologie(patient_data["Medicament"], patient_data["Posologie"])

# Affichage de la décomposition avec possibilité de modification
st.subheader("Décomposition de la posologie")
if decomposition:
    for unite, quantite in decomposition.items():
        nouvelle_valeur = st.number_input(
            f"{quantite} unité(s) de {unite} mg", 
            min_value=0, 
            value=quantite, 
            step=1,
            key=f"decomp_{unite}"  # ✅ Ajout d'un identifiant unique basé sur l'unité
        )
        decomposition[unite] = nouvelle_valeur  # Mise à jour si l'utilisateur modifie
# Convertir la décomposition en texte pour affichage sur PDF
    decomposition_text = "Soit : " + ", ".join(
        [f"{quantite} unité(s) de {unite} mg" for unite, quantite in decomposition.items() if quantite > 0]
    )
else:
    decomposition_text = "Décomposition impossible pour ce médicament."
    st.warning(decomposition_text)
st.write(decomposition_text)

# Autres saisies
patient_data["Duree"] = st.number_input("Durée (jours)", min_value=0)
patient_data["Rythme_de_Delivrance"] = st.number_input("Rythme de délivrance (jours)", min_value=0)
patient_data["Lieu_de_Delivrance"] = st.text_input("Lieu de délivrance")
patient_data["Chevauchement_Autorise"] = st.selectbox("Chevauchement autorisé", ["Oui", "Non"], index=1)

if st.button("Générer l'ordonnance PDF"):
    # Initialiser le document PDF avant toute action
    pdf = FPDF()
    pdf.add_page()
    pdf.set_left_margin(preferences["marges"]["gauche"])
    pdf.set_right_margin(preferences["marges"]["droite"])
    pdf.set_top_margin(preferences["marges"]["haut"])
    # Ajouter le logo (après l'initialisation de pdf)
    if preferences.get("logo") and os.path.exists(preferences["logo"]):
        try:
            pdf.image(preferences["logo"], x=10, y=10, w=40)
        except RuntimeError:
            st.warning("Erreur lors du chargement du logo : fichier invalide.")
    # pdf defini
    pdf.set_xy(10, 50)  # ✅ Plus d'erreur ici
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 5, preferences["structure"], ln=True, align="L")
    pdf.set_x(10)  # Réaligner l'adresse à gauche
    pdf.set_font("Arial", '', 9)
    pdf.cell(0, 5, preferences["adresse"], ln=True, align="L")
    pdf.set_x(10)  # Réaligner le FINESS à gauche
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 5, f"FINESS: {preferences['finess']}", ln=True, align="L")
# Bloc identification médecin   
    pdf.set_xy(150, 50)
# Écriture du nom du médecin en gras
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 5, preferences['medecin'], ln=True, align="C")
# Écriture du RPPS en standard mais dans la même cellule
    pdf.set_font("Arial", '', 10)
    pdf.set_x(150)  # Remet l'alignement en X à la position précédente
    pdf.cell(0, 5, f"RPPS: {preferences['rpps']}", ln=True, align="C")
# Afficher la date en toutes lettres
    from num2words import num2words
    jours_fr = ["lundi", "mardi", "mercredi", "jeudi", "vendredi", "samedi", "dimanche"]
    mois_fr = ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"]
    maintenant = datetime.datetime.now()
    jour_lettres = num2words(maintenant.day, lang='fr')
    jour_semaine = jours_fr[maintenant.weekday()]
    mois_lettres = mois_fr[maintenant.month - 1]
    date_complete = f"{jour_semaine} {jour_lettres} {mois_lettres} {maintenant.year}"
# Définir le pdf
    pdf.set_xy(150, 70)
    pdf.set_font("Arial", 'B', 10)
# Vérification et formatage de la date de naissance
    if patient_data["Date_de_Naissance"]:
        date_naissance = patient_data["Date_de_Naissance"].strftime("%d/%m/%Y")
        today = datetime.date.today()
        birth_date = patient_data["Date_de_Naissance"]
        age = today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
    else:
        date_naissance = "Non renseignée"
        age = "Non renseigné"
# Ecrire la date sur le PDF 
    pdf.cell(0, 5, date_complete, ln=True, align="R")
# Ecrire le infos patient sur le PDF
    pdf.cell(0, 10, txt=f"{patient_data['Civilite']} {patient_data['Nom']} {patient_data['Prenom']}", ln=True, align="R")
    pdf.set_y(pdf.get_y()-2)  # Réduit l'espacement
    pdf.set_font("Arial", 'I', 9)
    pdf.cell(0, 5, f"Né(e) le : {date_naissance} (Âge: {age})", ln=True, align="R")
## Vérifier securité sociale definie avant de les utiliser
    if "Numero_Securite_Sociale" not in patient_data:
        patient_data["Numero_Securite_Sociale"] = ""
    if "cle_secu" not in locals():
        cle_secu = None
# Vérifier que les données SS sont bien valides avant d'afficher
    if patient_data["Numero_Securite_Sociale"] and cle_secu is not None:
        pdf.set_font("Arial", '', 10)  # Texte standard
        pdf.cell(0, 5, f"N° Sécurité Sociale : {num_secu_formatte} - Clé : {cle_secu:02d}", ln=True, align="L")
# Ajouter les informations de l'ordonnance
    pdf.set_font("Arial", 'B', 10)  # Mettre en gras pour le médicament et la posologie
    pdf.cell(0, 5, f"{patient_data['Medicament']} {posologie_en_toutes_lettres(patient_data['Posologie'])} milligrammes", ln=True, align="L")
    pdf.set_font("Arial", '', 10)  # Remettre en normal après l'affichage
    pdf.cell(0, 5, txt=f"Durée: {patient_data.get('Duree', 'Non spécifiée')} jours", ln=True, align="L")
    pdf.cell(0, 5, txt=f"Rythme de délivrance: Tous les {patient_data.get('Rythme_de_Delivrance', 'Non spécifié')} jours", ln=True, align="L")
    pdf.cell(0, 10, txt=f"Lieu de délivrance: {patient_data.get('Lieu_de_Delivrance', 'Non spécifié')}", ln=True, align="L")
    pdf.cell(0, 5, txt=f"Chevauchement autorisé: {patient_data.get('Chevauchement_Autorise', 'Non spécifié')}", ln=True, align="L")
# Buffer
    buffer = io.BytesIO()
    buffer.write(pdf.output(dest="S").encode("latin1"))
    buffer.seek(0)
# Bouton télécharger
    st.download_button("Télécharger l'ordonnance", buffer, "ordonnance.pdf", "application/pdf")
