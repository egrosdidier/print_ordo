import csv
from flask import Flask, request, send_file, render_template_string, redirect, url_for, flash
from fpdf import FPDF
from datetime import datetime, timedelta
import io
import json

app = Flask(__name__)
app.secret_key = "secret-key-for-flash-messages"

# Charger les préférences utilisateur depuis un fichier JSON
def charger_preferences_utilisateur():
    try:
        with open("preferences.json", "r") as f:
            return json.load(f)
    except FileNotFoundError:
        return {
            "logo": None,
            "coordonnees": "Coordonnées non configurées",
            "marges": {
                "haut": 20,
                "bas": 20,
                "gauche": 20,
                "droite": 20
            }
        }

# Sauvegarder les préférences utilisateur dans le fichier JSON
def sauvegarder_preferences_utilisateur(preferences):
    with open("preferences.json", "w") as f:
        json.dump(preferences, f, indent=4)

# Convertir une date en toutes lettres
def date_en_toutes_lettres(date):
    jours = [
        "premier", "deux", "trois", "quatre", "cinq", "six", "sept", "huit", "neuf", "dix",
        "onze", "douze", "treize", "quatorze", "quinze", "seize", "dix-sept", "dix-huit", "dix-neuf",
        "vingt", "vingt et un", "vingt-deux", "vingt-trois", "vingt-quatre", "vingt-cinq", "vingt-six",
        "vingt-sept", "vingt-huit", "vingt-neuf", "trente", "trente et un"
    ]
    mois = [
        "janvier", "février", "mars", "avril", "mai", "juin",
        "juillet", "août", "septembre", "octobre", "novembre", "décembre"
    ]
    jour = date.day
    mois_index = date.month - 1
    annee = date.year
    jour_lettres = jours[jour - 1]
    mois_lettres = mois[mois_index]
    return f"{jour_lettres} {mois_lettres} {annee}"

# Générer une ordonnance en PDF pour un patient
def generer_ordonnance_pdf(patient_data, preferences):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_left_margin(preferences["marges"]["gauche"])
    pdf.set_right_margin(preferences["marges"]["droite"])
    pdf.set_top_margin(preferences["marges"]["haut"])

    # Ajouter le logo si disponible
    logo = preferences.get("logo")
    if logo:
        pdf.image(logo, x=10, y=10, w=40)

    # Ajouter les coordonnées de l'utilisateur
    pdf.set_font("Arial", size=10)
    pdf.ln(20)
    pdf.multi_cell(0, 10, preferences["coordonnees"])

    # Contenu de l'ordonnance
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

# Page d'accueil
@app.route("/", methods=["GET"])
def home():
    return render_template_string("""
    <h1>Générateur d'ordonnances</h1>
    <ul>
        <li><a href="/preferences">Modifier mes préférences</a></li>
        <li><a href="/import_csv">Importer un fichier CSV</a></li>
    </ul>
    """)

# Gestion des préférences utilisateur
@app.route("/preferences", methods=["GET", "POST"])
def preferences():
    if request.method == "POST":
        # Récupérer les préférences modifiées depuis le formulaire
        logo = request.form.get("logo")
        coordonnees = request.form.get("coordonnees")
        marges_haut = int(request.form.get("marges_haut"))
        marges_bas = int(request.form.get("marges_bas"))
        marges_gauche = int(request.form.get("marges_gauche"))
        marges_droite = int(request.form.get("marges_droite"))

        # Mettre à jour le fichier JSON
        new_preferences = {
            "logo": logo,
            "coordonnees": coordonnees,
            "marges": {
                "haut": marges_haut,
                "bas": marges_bas,
                "gauche": marges_gauche,
                "droite": marges_droite
            }
        }
        sauvegarder_preferences_utilisateur(new_preferences)
        return redirect(url_for("preferences"))

    # Charger les préférences actuelles
    prefs = charger_preferences_utilisateur()

    return render_template_string("""
    <h1>Modifier mes préférences</h1>
    <form method="POST">
        <label for="logo">Logo (nom du fichier) :</label>
        <input type="text" id="logo" name="logo" value="{{ prefs['logo'] }}">
        <br><br>
        <label for="coordonnees">Coordonnées :</label>
        <textarea id="coordonnees" name="coordonnees">{{ prefs['coordonnees'] }}</textarea>
        <br><br>
        <label for="marges_haut">Marge en haut :</label>
        <input type="number" id="marges_haut" name="marges_haut" value="{{ prefs['marges']['haut'] }}">
        <br><br>
        <label for="marges_bas">Marge en bas :</label>
        <input type="number" id="marges_bas" name="marges_bas" value="{{ prefs['marges']['bas'] }}">
        <br><br>
        <label for="marges_gauche">Marge à gauche :</label>
        <input type="number" id="marges_gauche" name="marges_gauche" value="{{ prefs['marges']['gauche'] }}">
        <br><br>
        <label for="marges_droite">Marge à droite :</label>
        <input type="number" id="marges_droite" name="marges_droite" value="{{ prefs['marges']['droite'] }}">
        <br><br>
        <button type="submit">Mettre à jour</button>
    </form>
    <a href="/">Retour à l'accueil</a>
    """, prefs=prefs)

# Route pour importer un fichier CSV
@app.route("/import_csv", methods=["GET", "POST"])
def import_csv():
    if request.method == "POST":
        file = request.files.get("csv_file")
        if not file:
            flash("Aucun fichier sélectionné", "error")
            return redirect(url_for("import_csv"))

        # Lire le fichier CSV
        patients = []
        try:
            csv_data = csv.DictReader(io.TextIOWrapper(file, encoding="utf-8"))
            for row in csv_data:
                patients.append(row)
        except Exception as e:
            flash(f"Erreur lors de la lecture du fichier CSV : {str(e)}", "error")
            return redirect(url_for("import_csv"))

        # Générer les PDFs pour tous les patients
        preferences = charger_preferences_utilisateur()
        buffer = io.BytesIO()
        pdf = FPDF()
        for patient in patients:
            single_pdf = generer_ordonnance_pdf(patient, preferences)
            buffer.write(single_pdf.output(dest="S").encode("latin1"))

        buffer.seek(0)
        return send_file(buffer, as_attachment=True, download_name="ordonnances.pdf", mimetype="application/pdf")

    return render_template_string("""
    <h1>Importer un fichier CSV</h1>
    <form method="POST" enctype="multipart/form-data">
        <label for="csv_file">Fichier CSV :</label>
        <input type="file" id="csv_file" name="csv_file" required>
        <br><br>
        <button type="submit">Importer et générer les ordonnances</button>
    </form>
    <a href="/">Retour à l'accueil</a>
    """)

if __name__ == "__main__":
    app.run(debug=True)