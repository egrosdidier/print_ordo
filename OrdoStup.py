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

# Définiton des unités de prise
from num2words import num2words

def formater_unite(medicament, quantite):
    """Retourne la bonne unité (gélule, flacon, comprimé) avec l'accord en français."""
    if medicament == "METHADONE GELULES":
        unite_nom = "gélule" if quantite == 1 else "gélules"
    elif medicament == "METHADONE SIROP":
        unite_nom = "flacon" if quantite == 1 else "flacons"
    else:  # Pour les comprimés (Buprénorphine HD, Subutex, Orobupré, etc.)
        unite_nom = "comprimé" if quantite == 1 else "comprimés"

    # Utiliser "une" au lieu de "un" devant gélule
    quantite_text = "une" if quantite == 1 and unite_nom in ["gélule"] else num2words(quantite, lang='fr')

    return quantite_text, unite_nom

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
logo_uploaded = st.sidebar.file_uploader("Logo de la structure en haut à gauche (PNG, JPG, JPEG)", type=["png", "jpg", "jpeg"])
if logo_uploaded:
    image = Image.open(logo_uploaded).convert("RGBA")
    white_background = Image.new("RGBA", image.size, (255, 255, 255, 255))
    image = Image.alpha_composite(white_background, image).convert("RGB")
    image.save(defaut_logo_path, format="PNG", optimize=True)
    preferences["logo"] = defaut_logo_path
else:
    preferences["logo"] = preferences.get("logo", None)

# Gestion du deuxième logo (haut à droite)
defaut_logo_droit_path = "logo_droit.png"
logo_droit_uploaded = st.sidebar.file_uploader("Deuxième logo (haut à droite)", type=["png", "jpg", "jpeg"])
if logo_droit_uploaded:
    image = Image.open(logo_droit_uploaded).convert("RGBA")
    white_background = Image.new("RGBA", image.size, (255, 255, 255, 255))
    image = Image.alpha_composite(white_background, image).convert("RGB")
    image.save(defaut_logo_droit_path, format="PNG", optimize=True)
    preferences["logo_droit"] = defaut_logo_droit_path
else:
    preferences["logo_droit"] = preferences.get("logo_droit", None)
    
# Gestion de la signature du médecin
defaut_signature_path = "signature_medecin.png"
signature_uploaded = st.sidebar.file_uploader("Signature du médecin (PNG, JPG, JPEG)", type=["png", "jpg", "jpeg"])

if signature_uploaded:
    image = Image.open(signature_uploaded).convert("RGBA")
    white_background = Image.new("RGBA", image.size, (255, 255, 255, 255))
    image = Image.alpha_composite(white_background, image).convert("RGB")
    image.save(defaut_signature_path, format="PNG", optimize=True)
    preferences["signature"] = defaut_signature_path
else:
    preferences["signature"] = preferences.get("signature", None)
    
# Sauvegarde des préférences
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

# Sélection ALD 30 : Oui / Non
patient_data["ALD_30"] = st.selectbox("ALD 30 :", ["Oui", "Non"], index=1)

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

from num2words import num2words

def decomposer_posologie(medicament, dose_totale):
    """Décompose la posologie en fonction des unités disponibles pour chaque médicament."""
    
    # Définition des unités disponibles pour chaque médicament
    decompositions = {
        "METHADONE GELULES": [40, 20, 10, 5, 1],
        "METHADONE SIROP": [60, 40, 20, 10, 5, 1],
        "BUPRENORPHINE HD": [8, 6, 2],
        "SUBUTEX": [8, 2, 0.4],
        "OROBUPRE": [8, 2]
    }

    # Vérifier que le médicament est dans la liste et que la dose est valide
    if medicament not in decompositions or dose_totale <= 0:
        return {}

    result = {}  # Dictionnaire qui stocke la décomposition
    reste = dose_totale

    # Répartition de la dose totale en unités adaptées
    for unite in decompositions[medicament]:
        if reste >= unite:
            quantite = reste // unite
            reste = reste % unite
            result[unite] = quantite  # Ajout de l'unité et de la quantité correspondante

    return result  # Retourne un dictionnaire {unité: quantité}

# Générer la décomposition automatique
decomposition = decomposer_posologie(patient_data["Medicament"], patient_data["Posologie"])

# Affichage et modification manuelle de la décomposition dans Streamlit
st.subheader("Décomposition de la posologie")

decomposition_modifiee = {}  # Stocke les valeurs modifiées par l'utilisateur

# Liste des unités disponibles en fonction du médicament
unités_possibles = {
    "METHADONE GELULES": [40, 20, 10, 5, 1],
    "METHADONE SIROP": [60, 40, 20, 10, 5, 1],
    "BUPRENORPHINE HD": [8, 6, 2],
    "SUBUTEX": [8, 2, 0.4],
    "OROBUPRE": [8, 2]
}

# Vérifier si le médicament est dans la liste
if patient_data["Medicament"] in unités_possibles:
    total_corrige = 0  # Initialisation du total recalculé
    
    for unite in unités_possibles[patient_data["Medicament"]]:  # Boucle sur toutes les unités
        quantite = decomposition.get(unite, 0)  # Récupérer la quantité ou 0 par défaut
        nouvelle_valeur = st.number_input(
            f"{quantite} unité(s) de {unite} mg", 
            min_value=0, 
            value=quantite, 
            step=1,
            key=f"decomp_{unite}"  # Clé unique pour éviter StreamlitDuplicateElementId
        )
        decomposition_modifiee[unite] = nouvelle_valeur  # Mise à jour des valeurs modifiées
        total_corrige += nouvelle_valeur * unite  # Ajoute la dose corrigée au total recalculé

    # Vérification si le total correspond à la posologie souhaitée
    if total_corrige != patient_data["Posologie"]:
        st.error(f"La somme des corrections ({total_corrige} mg) ne correspond pas à la posologie totale ({patient_data['Posologie']} mg).")
    else:
        st.success(f"Décomposition correcte : {total_corrige} mg = {patient_data['Posologie']} mg")

else:
    st.warning("Décomposition impossible pour ce médicament.")

# Vérification pour affichage dans le PDF
decomposition_finale = decomposition_modifiee if decomposition_modifiee else decomposition
decomposition_finale = {unite: quantite for unite, quantite in decomposition_finale.items() if quantite > 0}

# Saisies suivantes
patient_data["Duree"] = st.number_input("Durée du traitement (jours)", min_value=1, step=1)
patient_data["Rythme_de_Delivrance"] = st.number_input("Rythme de délivrance (jours)", min_value=1, step=1)
patient_data["Chevauchement_Autorise"] = st.selectbox("Chevauchement autorisé", ["Oui", "Non"], index=1)

# Saisie du lieu de délivrance en multi-ligne, obligatoire
# Saisie multi-ligne
patient_data["Lieu_de_Delivrance"] = st.text_area("Lieu de délivrance (Nom + Adresse)",
                                                  placeholder="Exemple : \nPharmacie Centrale\n12 rue des Lilas, 75000 Paris")
# Bouton pour valider la saisie
if st.button("Valider"):
    st.success("Lieu de délivrance validé ✅")
# Vérification que le champ est rempli
if not patient_data["Lieu_de_Delivrance"].strip():
    st.error("Lieu de délivrance obligatoire. A renseigner et valider avant de générer l'ordonnance.")
    lieu_rempli = False
else:
    lieu_rempli = True
    
if st.button("Générer l'ordonnance PDF"):
# Initialiser le document PDF avant toute action
    pdf = FPDF()
    pdf.add_page()
    pdf.set_left_margin(preferences["marges"]["gauche"])
    pdf.set_right_margin(preferences["marges"]["droite"])
    pdf.set_top_margin(preferences["marges"]["haut"])

# Ajouter le premier logo (après l'initialisation de pdf)
    if preferences.get("logo") and os.path.exists(preferences["logo"]):
        try:
            pdf.image(preferences["logo"], x=10, y=10, w=40)
        except RuntimeError:
            st.warning("Erreur lors du chargement du logo : fichier invalide.")

# Bloc info structure
    pdf.set_xy(10, 50)  # ✅ Plus d'erreur ici
    pdf.set_font("Arial", 'B', 10)
    pdf.cell(0, 5, preferences["structure"], ln=True, align="L")
    pdf.set_x(10)  # Réaligner l'adresse à gauche
    pdf.set_font("Arial", '', 9)
    pdf.cell(0, 5, preferences["adresse"], ln=True, align="L")
    pdf.set_x(10)  # Réaligner le FINESS à gauche
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 5, f"FINESS: {preferences['finess']}", ln=True, align="L")

# Ajout du deuxième logo (haut à droite)
    if preferences.get("logo_droit") and os.path.exists(preferences["logo_droit"]):
        try:
            pdf.image(preferences["logo_droit"], x=150, y=10, w=40)  # Logo à droite (aligné au même niveau)
        except RuntimeError:
            st.warning("Erreur lors du chargement du logo de droite : fichier invalide.")

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
        pdf.cell(0, 5, f"N° Sécurité Sociale : {num_secu_formatte} - Clé : {cle_secu:02d}", ln=True, align="R")

    pdf.set_font("Arial", 'B', 12)  # Texte en gras et taille 12

# Titre
# Définition du titre selon l'ALD 30
    titre_prescription = "PRESCRIPTIONS ALD 30" if patient_data["ALD_30"] == "Oui" else "PRESCRIPTIONS MÉDICALES"
# Position du titre
    pdf.cell(0, 5, "", ln=True)  # Ligne vide pour espacement
    y_position = pdf.get_y()  # Récupération de la position actuelle
# Ajout du premier trait horizontal
    pdf.set_line_width(0.5)
    pdf.line(10, y_position, 200, y_position)  # Trait horizontal supérieur
# Ajout du titre
    pdf.set_xy(10, y_position + 3)  # Légèrement en dessous du trait
    pdf.cell(190, 10, titre_prescription, border=0, ln=True, align="C")
# Ajout du deuxième trait horizontal
    y_position = pdf.get_y() + 2  # Nouvelle position après le titre
    pdf.line(10, y_position, 200, y_position)  # Trait horizontal inférieur
# Ajout d'un espacement après le titre
    pdf.cell(0, 5, "", ln=True)
    
# Ajouter médicament
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 20, f"{patient_data['Medicament']} : {num2words(patient_data['Posologie'], lang='fr')} milligrammes par jour", ln=True, align="L")
    pdf.set_font("Arial", '', 10)
# Vérifier si la décomposition a été modifiée ou non
    decomposition_finale = decomposition_modifiee if decomposition_modifiee else decomposition
# Supprimer les unités de quantité 0 pour l'affichage dans le PDF
    decomposition_finale = {unite: quantite for unite, quantite in decomposition_finale.items() if quantite > 0}
# Vérifier s'il reste des unités à afficher
    if decomposition_finale:
        pdf.cell(0, 5, "Soit :", ln=True, align="L")  # Titre de la décomposition
        for unite, quantite in decomposition_finale.items():
            quantite_text, unite_nom = formater_unite(patient_data["Medicament"], quantite)
            pdf.cell(0, 5, f"- {quantite_text} {unite_nom} de {num2words(unite, lang='fr')} milligrammes", ln=True, align="L")
    else:
        pdf.cell(0, 5, "Décomposition impossible pour ce médicament.", ln=True, align="L")
    pdf.set_font("Arial", '', 10)
    pdf.cell(0, 10, f"Pendant : {num2words(patient_data['Duree'], lang='fr')} jours", ln=True, align="L")    
    pdf.set_font("Arial", '', 10)
# Vérification pour ajouter (délivrance en une fois) si durée = rythme
    if patient_data["Rythme_de_Delivrance"] == patient_data["Duree"]:
        pdf.set_font("Arial", '', 10)
        pdf.cell(0, 8, f"A délivrer tous les {num2words(patient_data['Rythme_de_Delivrance'], lang='fr')} jours (délivrance en une fois)", ln=True, align="L")
    else:
        pdf.set_font("Arial", '', 10)
        pdf.cell(0, 8, f"A délivrer tous les {num2words(patient_data['Rythme_de_Delivrance'], lang='fr')} jours", ln=True, align="L")

# Autres mentions
    pdf.cell(0, 5, txt=f"Chevauchement autorisé: {patient_data.get('Chevauchement_Autorise', 'Non spécifié')}", ln=True, align="L")
    pdf.set_font("Arial", '', 10)
    pdf.multi_cell(0, 5, f"Lieu de délivrance :\n{patient_data['Lieu_de_Delivrance']}", align="L")

# Position par défaut pour la signature et le nom du médecin
    y_position_signature = pdf.get_y() + 10  # Position de référence en bas du document

# Vérifier si une signature est téléversée
    if preferences.get("signature") and os.path.exists(preferences["signature"]):
        try:
            pdf.image(preferences["signature"], x=150, y=y_position_signature, w=50)  # Signature alignée à droite
            y_position_text = y_position_signature + 15  # Décaler le texte sous la signature
        except RuntimeError:
            st.warning("Erreur lors du chargement de la signature : fichier invalide.")
            y_position_text = y_position_signature  # Si erreur, placer le texte à la position initiale
    else:
        y_position_text = y_position_signature  # Si pas de signature, mettre le texte à la position initiale

# Ajouter le nom du médecin (sous la signature ou seul)
    pdf.set_xy(150, y_position_text)  # Position définie
    pdf.set_font("Arial", '', 10)
    pdf.cell(50, 5, preferences["medecin"], ln=True, align="C")  # Centré

# Saisie du lieu de délivrance (obligatoire)
    patient_data["Lieu_de_Delivrance"] = st.text_area("Lieu de délivrance (Nom + Adresse)", 
                                                  placeholder="Exemple : \nPharmacie Centrale\n12 rue des Lilas, 75000 Paris")

# Initialisation de l'état de la génération si elle n'existe pas encore
    if "pdf_ready" not in st.session_state:
        st.session_state.pdf_ready = False

# Vérification après un clic sur le bouton
    if st.button("Générer l'ordonnance PDF"):
        if not patient_data["Lieu_de_Delivrance"].strip():  # Vérifie si le champ est vide
            st.error("Le lieu de délivrance est obligatoire. Veuillez le renseigner et le valider.")
            st.session_state.pdf_ready = False  # Bloque la génération
        else:
            # Génération du PDF seulement si le lieu de délivrance est rempli
            pdf = FPDF()
            pdf.add_page()
        
            pdf.set_font("Arial", '', 10)
            pdf.multi_cell(0, 5, f"Lieu de délivrance :\n{patient_data['Lieu_de_Delivrance']}", align="L")

        # Génération du fichier en mémoire
            buffer = io.BytesIO()
            buffer.write(pdf.output(dest="S").encode("latin1"))
            buffer.seek(0)

        # Stocke le fichier PDF dans session_state pour qu'il reste disponible après le clic
            st.session_state.pdf_buffer = buffer
            st.session_state.pdf_ready = True  # Autorise l'affichage du bouton de téléchargement

# Affichage du bouton de téléchargement uniquement si le PDF a été généré avec succès
    if st.session_state.pdf_ready:
        st.download_button("Télécharger l'ordonnance", st.session_state.pdf_buffer, "ordonnance.pdf", "application/pdf")
