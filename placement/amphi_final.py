# Ajout du verrouillage de fichier
import customtkinter as ctk
from tkinter import messagebox, filedialog, ttk
import csv
from datetime import datetime
import json
import threading
import os
import random
from filelock import FileLock, Timeout
# Paramètres globaux
ctk.set_appearance_mode("dark")
app = ctk.CTk()
app.title("Système Expert - Placement Amphi Entreprise")
app.geometry("1600x900")
app._set_appearance_mode("dark")
# Nouvelle palette de couleurs
COLOR_BG = "#181c24"         # Fond général
COLOR_SIDEBAR = "#23283a"    # Barre latérale
COLOR_GRID_BG = "#23283a"    # Fond de la grille
COLOR_BTN_M = "#2563eb"      # Bleu vif pour hommes
COLOR_BTN_F = "#a855f7"      # Violet vif pour femmes
COLOR_BTN_EMPTY = "#374151"   # Gris foncé pour sièges vides
COLOR_BTN_HOVER = "#475569"  # Hover boutons sièges
COLOR_GOLD = "#d9ebee"       # Doré moderne
COLOR_GREEN = "#22c55e"      # Vert vif
COLOR_RED = "#ef4444"        # Rouge vif
COLOR_STATUS = "#0ea5e9"     # Bleu clair pour statut
COLOR_TEXT = "#f1f5f9"       # Texte principal
COLOR_TEXT_MUTED = "#94a3b8" # Texte secondaire

# Palette de couleurs pour domaines (variation visuelle)
DOMAIN_COLORS = {
    "informatique": "#06b6d4",      # Cyan
    "vente": "#ec4899",              # Rose
    "marketing": "#f97316",          # Orange
    "rh": "#06b6d4",                 # Cyan
    "finance": "#8b5cf6",            # Violet
    "ingénierie": "#6366f1",         # Indigo
    "logistique": "#14b8a6",         # Teal
    "production": "#f59e0b",         # Ambre
    "qualité": "#10b981",            # Émeraude
    "support": "#3b82f6",            # Bleu
    "direction": "#dc2626",          # Rouge
    "audit": "#7c3aed",              # Violet foncé
    "communications": "#84cc16",     # Lime
    "ressources": "#06b6d4",         # Cyan
}

# Emojis par domain
DOMAIN_EMOJIS = {
    "informatique": "💻",
    "vente": "📊",
    "marketing": "📢",
    "rh": "👥",
    "finance": "💰",
    "ingénierie": "⚙️",
    "logistique": "📦",
    "production": "🏭",
    "qualité": "✓",
    "support": "🔧",
    "direction": "👔",
    "audit": "📋",
    "communications": "📣",
    "ressources": "🎯",
}

# --- MAPPING RÉEL (48 PLACES) - PYRAMIDES SÉPARÉES COMME DANS L'IMAGE ---
places_exactes = []

# BLOC HAUT - Pyramide inversée (8, 7, 3) = 18 places, pyramide uniforme
# Rangée 0: 8 places
for col in range(4, 12):  # colonnes 4 à 11
    places_exactes.append((0, col))

# Rangée 1: 7 places
for col in range(4, 11):  # colonnes 4 à 10
    places_exactes.append((1, col))

# Rangée 2: 3 places
for col in range(7, 10):  # colonnes 7 à 9
    places_exactes.append((2, col))

# BLOC GAUCHE - Pyramide verticale décroissante (6, 4, 3, 2) = 15 places
# Colonne 1: 6 places
for row in range(2, 8):  # rangées 2 à 7
    places_exactes.append((row, 1))

# Colonne 2: 4 places
for row in range(3, 7):  # rangées 3 à 6
    places_exactes.append((row, 2))

# Colonne 3: 3 places
for row in range(3, 6):  # rangées 3 à 5
    places_exactes.append((row, 3))

# Colonne 4: 2 places
for row in range(4, 6):  # rangées 4 à 5
    places_exactes.append((row, 4))

# BLOC DROITE - Pyramide verticale décroissante mirroir (6, 4, 3, 2) = 15 places
# Colonne 14: 6 places
for row in range(2, 8):  # rangées 2 à 7
    places_exactes.append((row, 14))

# Colonne 13: 4 places
for row in range(3, 7):  # rangées 3 à 6
    places_exactes.append((row, 13))

# Colonne 12: 3 places
for row in range(3, 6):  # rangées 3 à 5
    places_exactes.append((row, 12))

# Colonne 11: 2 places
for row in range(4, 6):  # rangées 4 à 5
    places_exactes.append((row, 11))


sieges_data = {coord: None for coord in places_exactes}
sieges_btns = {}
stats = {"H": 0, "F": 0, "Total": 0}

# Pour la sélection/déplacement manuel
selected_seat = [None]  # Utilisation d'une liste pour mutabilité dans les closures

SAVE_FILE = "placements.json"
LOCK_FILE = SAVE_FILE + ".lock"

# Numérotation des sièges (1 à 48)
sieges_numeros = {coord: numero for numero, coord in enumerate(places_exactes, start=1)}

# Fonction pour obtenir couleur et emoji par domaine
def get_domain_color(domaine):
    """Retourne une couleur unique pour chaque domaine"""
    domaine_lower = domaine.lower()
    for key, color in DOMAIN_COLORS.items():
        if key in domaine_lower:
            return color
    return COLOR_BTN_M if domaine_lower.startswith('h') else COLOR_BTN_F

def get_domain_emoji(domaine):
    """Retourne un emoji pour chaque domaine"""
    domaine_lower = domaine.lower()
    for key, emoji in DOMAIN_EMOJIS.items():
        if key in domaine_lower:
            return emoji
    return "🎯"

# --- GESTION DE LA SAUVEGARDE ---
def sauvegarder_donnees():
    """Sauvegarde les placements dans un fichier JSON avec métadonnées"""
    try:
        # Verrouillage du fichier pour éviter les accès concurrents
        lock = FileLock(LOCK_FILE, timeout=5)
        with lock:
            # Relire le fichier pour fusionner si d'autres modifs ont eu lieu
            donnees_existantes = None
            if os.path.exists(SAVE_FILE):
                try:
                    with open(SAVE_FILE, 'r', encoding='utf-8') as f:
                        donnees_existantes = json.load(f)
                except Exception:
                    donnees_existantes = None

            donnees = {
                "version": "1.0",
                "last_modified": datetime.now().isoformat(),
                "metadata": {
                    "app": "Système Expert Amphithéâtre",
                    "total_seats": 48,
                    "rules": ["domaine", "entreprise", "poste", "age_diff"]
                },
                "placements": {str(k): v for k, v in sieges_data.items()},
                "stats": stats
            }

            # Fusionner les stats si d'autres modifs détectées (simple merge)
            if donnees_existantes:
                # On pourrait fusionner plus finement ici si besoin
                pass

            with open(SAVE_FILE, 'w', encoding='utf-8') as f:
                json.dump(donnees, f, ensure_ascii=False, indent=2)
    except Timeout:
        messagebox.showerror("Erreur", "Impossible de sauvegarder : accès concurrent au fichier. Réessayez.")
    except Exception as e:
        print(f"Erreur sauvegarde : {e}")
        messagebox.showerror("Erreur", f"Erreur lors de la sauvegarde : {e}")

def charger_donnees():
    """Charge les placements depuis le fichier JSON avec gestion des versions"""
    global sieges_data, stats
    try:
        lock = FileLock(LOCK_FILE, timeout=5)
        with lock:
            if os.path.exists(SAVE_FILE):
                with open(SAVE_FILE, 'r', encoding='utf-8') as f:
                    donnees = json.load(f)
                # Vérifier la version
                version = donnees.get("version", "0.0")
                if version != "1.0":
                    print(f"Version du fichier : {version}, migration nécessaire")
                # Charger les placements
                for coord_str, participant in donnees.get("placements", {}).items():
                    if participant is not None:
                        coord = eval(coord_str)
                        sieges_data[coord] = participant
                        if coord in sieges_btns:
                            color = get_domain_color(participant["domaine"])
                            emoji = get_domain_emoji(participant["domaine"])
                            sieges_btns[coord].configure(
                                text=f"{emoji} {participant['nom'][:3]}\n{participant['poste'][:8]}\nSiège {sieges_numeros[coord]}",
                                fg_color=color,
                                text_color=COLOR_TEXT
                            )
                # Charger les stats
                stats = donnees.get("stats", {"H": 0, "F": 0, "Total": 0})
                maj_stats()
                update_status("Données chargées avec succès")
    except Timeout:
        update_status("Erreur chargement données")
        messagebox.showerror("Erreur", "Impossible de lire le fichier : accès concurrent. Réessayez.")
    except Exception as e:
        update_status("Erreur chargement données")
        messagebox.showerror("Erreur", f"Erreur chargement : {e}")

def reinitialiser_donnees():
    """Réinitialise tous les placements"""
    global sieges_data, stats
    if messagebox.askyesno("Confirmation", "⚠️ Êtes-vous sûr de vouloir effacer tous les placements ?"):
        sieges_data = {coord: None for coord in places_exactes}
        stats = {"H": 0, "F": 0, "Total": 0}
        
        for coord in sieges_btns:
            sieges_btns[coord].configure(text="", fg_color=COLOR_BTN_EMPTY, text_color=COLOR_TEXT_MUTED)
        
        maj_stats()
        sauvegarder_donnees()
        messagebox.showinfo("Succès", "✅ Données réinitialisées")

# --- LOGIQUE ---
def maj_stats():
    stats_h.configure(text=f"♂ Hommes: {stats['H']}")
    stats_f.configure(text=f"♀ Femmes: {stats['F']}")
    pourcentage = int((stats['Total'] / 48) * 100)
    stats_percent.configure(text=f"Remplissage: {pourcentage}% ({stats['Total']}/48)")

def verifier_voisins(r, c, p):
    # Vérifie les 4 voisins directs (haut, bas, gauche, droite)
    voisins = [(r-1, c), (r+1, c), (r, c-1), (r, c+1)]
    for v_coord in voisins:
        if v_coord in sieges_data and sieges_data[v_coord] is not None:
            v = sieges_data[v_coord]
            # Vérification des critères
            if v['sexe'].lower() == p['sexe'].lower(): return False
            if v['domaine'].lower() == p['domaine'].lower(): return False
            if v['entreprise'].lower() == p['entreprise'].lower(): return False
            if v['poste'].lower() == p['poste'].lower(): return False
            if v['origine'].lower() == p['origine'].lower(): return False
            # Nouvelle règle : équipes différentes (si équipe existe)
            if 'equipe' in v and 'equipe' in p:
                if v['equipe'] and p['equipe']:  # Si les deux ont une équipe
                    if v['equipe'].lower() == p['equipe'].lower(): return False
    return True

def importer_csv():
    fichier = filedialog.askopenfilename(
        title="Choisir un fichier CSV",
        filetypes=[("Fichiers CSV", "*.csv")]
    )

    if not fichier:
        return

    def process_import():
        update_status("Importation en cours...")
        try:
            with open(fichier, newline='', encoding='utf-8') as f:
                lecteur = csv.DictReader(f)
                lignes = list(lecteur)
                total = len(lignes)
                
                for i, ligne in enumerate(lignes):
                    try:
                        # Convertir le sexe correctement : "Homme" → "M", "Femme" → "F"
                        sexe_raw = ligne.get("sexe", "").strip()
                        if sexe_raw.lower() == "homme":
                            sexe = "M"
                        elif sexe_raw.lower() == "femme":
                            sexe = "F"
                        else:
                            sexe = sexe_raw.upper()  # Au cas où c'est déjà "M" ou "F"
                        
                        equipe = ligne.get("equipe", "").strip()
                        p = {
                            "nom": ligne.get("nom", "").strip(),
                            "origine": ligne.get("origine", "").strip(),
                            "entreprise": ligne.get("entreprise", "").strip(),
                            "domaine": ligne.get("domaine", "").strip(),
                            "poste": ligne.get("poste", "").strip(),
                            "sexe": sexe,
                            "equipe": equipe if equipe else None
                        }

                        place_trouvee = False
                        # Créer une copie aléatoire des places disponibles pour plus de variation
                        places_melangees = [c for c in places_exactes if sieges_data[c] is None]
                        random.shuffle(places_melangees)
                        
                        for coord in places_melangees:
                            if verifier_voisins(coord[0], coord[1], p):
                                sieges_data[coord] = p
                                stats["Total"] += 1
                                if p["sexe"] == "M":
                                    stats["H"] += 1
                                else:
                                    stats["F"] += 1

                                color = get_domain_color(p["domaine"])
                                emoji = get_domain_emoji(p["domaine"])
                                sieges_btns[coord].configure(
                                    text=f"{emoji} {p['nom'][:3]}\n{p['poste'][:8]}\nSiège {sieges_numeros[coord]}",
                                    fg_color=color,
                                    text_color=COLOR_TEXT
                                )

                                place_trouvee = True
                                break

                        if not place_trouvee:
                            print(f"Aucune place pour {p['nom']}")

                    except ValueError:
                        print(f"Erreur âge invalide : {ligne.get('nom', 'inconnu')}")
                    except Exception as e:
                        print(f"Erreur ligne : {ligne} -> {e}")

                maj_stats()  # Mettre à jour l'affichage des stats
                sauvegarder_donnees()
                update_status(f"Import: {stats['H']} hommes, {stats['F']} femmes")
                messagebox.showinfo("Succès", f"✅ Importation terminée : {stats['Total']} personnes")

        except Exception as e:
            update_status("Erreur lors de l'importation")
            messagebox.showerror("Erreur", f"Impossible de lire le fichier : {e}")

    # Lancer l'import dans un thread séparé
    threading.Thread(target=process_import, daemon=True).start()


def generer_fiche():
    """Génère une fiche HTML avec la disposition visuelle exacte des participants"""
    if stats["Total"] == 0:
        messagebox.showwarning("Attention", "Aucun participant placé pour générer la fiche.")
        return
    
    # Créer le contenu HTML avec le plan visuel
    html_content = f"""
    <!DOCTYPE html>
    <html lang="fr">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Fiche de Placement - Amphi Entreprise</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #f5f5f5;
                margin: 20px;
                padding: 20px;
            }}
            .header {{
                text-align: center;
                margin-bottom: 30px;
                border-bottom: 3px solid #1976d2;
                padding-bottom: 20px;
            }}
            .header h1 {{
                margin: 0;
                color: #1976d2;
                font-size: 28px;
            }}
            .stats {{
                text-align: center;
                margin-bottom: 30px;
                font-size: 16px;
            }}
            .stats span {{
                margin: 0 20px;
                font-weight: 600;
            }}
            .plan-container {{
                margin: 30px 0;
                padding: 20px;
                background-color: #23283a;
                border-radius: 8px;
                display: inline-block;
                margin-left: auto;
                margin-right: auto;
                width: 100%;
                box-sizing: border-box;
            }}
            .plan-grid {{
                display: inline-grid;
                gap: 4px;
                grid-template-columns: repeat(16, 1fr);
                margin: 0 auto;
                padding: 20px;
                background-color: #23283a;
                border-radius: 8px;
            }}
            .seat {{
                width: 50px;
                height: 50px;
                display: flex;
                flex-direction: column;
                align-items: center;
                justify-content: center;
                border-radius: 4px;
                font-size: 9px;
                font-weight: bold;
                color: white;
                border: 1px solid #555;
                text-align: center;
                padding: 2px;
                box-sizing: border-box;
            }}
            .seat-empty {{
                background-color: #374151;
                color: #94a3b8;
            }}
            .seat-male {{
                background-color: #2563eb;
            }}
            .seat-female {{
                background-color: #a855f7;
            }}
            .seat-tech {{
                background-color: #06b6d4;
            }}
            .seat-sales {{
                background-color: #ec4899;
            }}
            .seat-marketing {{
                background-color: #f97316;
            }}
            .seat-hr {{
                background-color: #06b6d4;
            }}
            .seat-finance {{
                background-color: #8b5cf6;
            }}
            .seat-engineering {{
                background-color: #6366f1;
            }}
            .seat-logistics {{
                background-color: #14b8a6;
            }}
            .seat-production {{
                background-color: #f59e0b;
            }}
            .seat-quality {{
                background-color: #10b981;
            }}
            .seat-support {{
                background-color: #3b82f6;
            }}
            .seat-management {{
                background-color: #dc2626;
            }}
            .seat-audit {{
                background-color: #7c3aed;
            }}
            .seat-communications {{
                background-color: #84cc16;
            }}
            .podium {{
                background: linear-gradient(135deg, #d9ebee 0%, #a0bbc4 100%);
                color: #181c24;
                font-size: 18px;
                font-weight: bold;
                border-radius: 8px;
                height: 50px;
                line-height: 50px;
                text-align: center;
                margin: 15px auto;
                box-shadow: 0 4px 6px rgba(0,0,0,0.2);
                border: 2px solid #7a9aa5;
                width: 100%;
                box-sizing: border-box;
            }}
            .spacer {{
                visibility: hidden;
            }}
            .legend {{
                margin-top: 20px;
                text-align: center;
                font-size: 12px;
            }}
            .legend-item {{
                display: inline-block;
                margin: 0 20px;
            }}
            .legend-color {{
                display: inline-block;
                width: 15px;
                height: 15px;
                margin-right: 5px;
                border-radius: 2px;
                vertical-align: middle;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin-top: 30px;
                background-color: white;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            }}
            th {{
                background-color: #1976d2;
                color: white;
                padding: 12px;
                text-align: left;
                font-weight: 600;
            }}
            td {{
                border: 1px solid #ddd;
                padding: 10px;
            }}
            tr:nth-child(even) {{
                background-color: #f9f9f9;
            }}
            .footer {{
                text-align: center;
                margin-top: 30px;
                color: #666;
                font-size: 12px;
            }}
            .print-center {{
                text-align: center;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🎤 FICHE DE PLACEMENT - AMPHITHÉÂTRE ENTREPRISE</h1>
            <p>Généré le {datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}</p>
        </div>
        
        <div class="stats">
            <span><strong>TOTAL :</strong> {stats['Total']} / 48</span>
            <span style="color: #2563eb; font-weight: bold;">◆ ♂ ◆ HOMMES : {stats['H']}</span>
            <span style="color: #a855f7; font-weight: bold;">◆ ♀ ◆ FEMMES : {stats['F']}</span>
        </div>
        
        <div class="print-center">
            <h2>PLAN DE L'AMPHITHÉÂTRE</h2>
            <div class="plan-container">
                <div class="plan-grid">
"""
    
    # Générer la grille visuelle (16 colonnes x 12 rangées)
    for row in range(12):
        for col in range(16):
            coord = (row, col)
            
            # Vérifier si ce siège existe
            if coord in sieges_data:
                participant = sieges_data[coord]
                if participant is not None:
                    # Siège occupé
                    color_class = "seat-male" if participant["sexe"] == "M" else "seat-female"
                    # Utiliser la couleur du domaine pour plus de variation
                    domaine_lower = participant["domaine"].lower()
                    if "informatique" in domaine_lower:
                        color_class = "seat-tech"
                    elif "vente" in domaine_lower:
                        color_class = "seat-sales"
                    elif "marketing" in domaine_lower:
                        color_class = "seat-marketing"
                    elif "rh" in domaine_lower or "ressources" in domaine_lower:
                        color_class = "seat-hr"
                    elif "finance" in domaine_lower:
                        color_class = "seat-finance"
                    elif "ingénierie" in domaine_lower or "engineering" in domaine_lower:
                        color_class = "seat-engineering"
                    elif "logistique" in domaine_lower:
                        color_class = "seat-logistics"
                    elif "production" in domaine_lower:
                        color_class = "seat-production"
                    elif "qualité" in domaine_lower or "quality" in domaine_lower:
                        color_class = "seat-quality"
                    elif "support" in domaine_lower:
                        color_class = "seat-support"
                    elif "direction" in domaine_lower or "management" in domaine_lower:
                        color_class = "seat-management"
                    elif "audit" in domaine_lower:
                        color_class = "seat-audit"
                    elif "communication" in domaine_lower:
                        color_class = "seat-communications"
                    
                    nom_siège = sieges_numeros[coord]
                    nom = participant['nom'][:3].upper()
                    emoji = get_domain_emoji(participant["domaine"])
                    origine = participant['origine']
                    titre_tooltip = f'{nom_siège}. {participant["nom"]}, {origine} - {participant["poste"]}'
                    html_content += f'<div class="seat {color_class}" title="{titre_tooltip}"><strong>{nom_siège}</strong><br>{emoji} {nom}</div>'
                else:
                    # Siège vide
                    html_content += '<div class="seat seat-empty"></div>'
            else:
                # Pas de siège à cette position
                html_content += '<div class="seat spacer"></div>'
    
    html_content += """
                </div>
                <div class="podium">🎤 PODIUM</div>
            </div>
        </div>
        
        <div class="legend">
            <span class="legend-item">
                <span class="legend-color" style="background-color: #2563eb;"></span>
                Hommes
            </span>
            <span class="legend-item">
                <span class="legend-color" style="background-color: #a855f7;"></span>
                Femmes
            </span>
            <span class="legend-item">
                <span class="legend-color" style="background-color: #374151;"></span>
                Siège vide
            </span>
        </div>
        
        <h2 style="margin-top: 30px;">DÉTAIL DES PLACEMENTS</h2>
        <table>
            <thead>
                <tr>
                    <th>Siège</th>
                    <th>Nom complet</th>
                    <th>Origine</th>
                    <th>Entreprise</th>
                    <th>Domaine</th>
                    <th>Poste</th>
                    <th>Sexe</th>
                </tr>
            </thead>
            <tbody>
"""
    
    # Ajouter les participants dans le tableau détaillé, triés par numéro de siège
    sieges_sorted = sorted([(n, coord) for coord, n in sieges_numeros.items()], key=lambda x: x[0])
    
    for num_siège, coord in sieges_sorted:
        if sieges_data[coord] is not None:
            p = sieges_data[coord]
            sexe_text = "Homme" if p['sexe'] == "M" else "Femme"
            sexe_symbol = "♂" if p['sexe'] == "M" else "♀"
            html_content += f"""
                <tr>
                    <td><strong>{num_siège}</strong></td>
                    <td>{p['nom']}</td>
                    <td>{p['origine']}</td>
                    <td>{p['entreprise']}</td>
                    <td>{p['domaine']}</td>
                    <td>{p['poste']}</td>
                    <td>{sexe_symbol} {sexe_text}</td>
                </tr>
            """
    
    html_content += """
            </tbody>
        </table>
        
        <div class="footer">
            <p>Système Expert de Placement en Amphithéâtre</p>
            <p><em>Cette fiche peut être imprimée pour consultation lors de l'événement.</em></p>
        </div>
    </body>
    </html>
    """
    
    # Sauvegarder le fichier HTML
    filename = f"Fiche_Placement_{datetime.now().strftime('%Y%m%d_%H%M%S')}.html"
    filepath = os.path.join(os.path.expanduser("~"), "Desktop", filename)
    
    try:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Ouvrir le fichier dans le navigateur par défaut
        os.startfile(filepath)
        messagebox.showinfo("Succès", f"Fiche générée avec succès !\n\nFichier : {filename}\n\nLe plan imprimé reproduit fidèlement la disposition numérique avec couleurs et numérotation.")
    except Exception as e:
        messagebox.showerror("Erreur", f"Erreur lors de la génération : {e}")


def placer_membre():
    nom = en_nom.get().strip()
    origine = origine_var.get().strip()
    ent = en_ent.get().strip()
    dom = en_dom.get().strip()
    pos = en_pos.get().strip()
    equipe = equipe_var.get().strip()
    
    if not all([nom, origine, ent, dom, pos]):
        messagebox.showerror("Erreur", "⚠️ Tous les champs sont obligatoires !")
        return
    
    if not origine:
        messagebox.showerror("Erreur", "⚠️ Veuillez sélectionner une origine !")
        return

    p = {
        "nom": nom,
        "origine": origine,
        "entreprise": ent,
        "domaine": dom,
        "poste": pos,
        "sexe": "M" if sex_var.get() == "Homme" else "F",
        "equipe": equipe if equipe and equipe != "Aucune" else None
    }

    # Créer une copie aléatoire des places disponibles pour plus de variation
    places_melangees = [c for c in places_exactes if sieges_data[c] is None]
    random.shuffle(places_melangees)
    
    for coord in places_melangees:
        if verifier_voisins(coord[0], coord[1], p):
            sieges_data[coord] = p
            stats["Total"] += 1
            if p["sexe"] == "M":
                stats["H"] += 1
            else:
                stats["F"] += 1

            color = get_domain_color(p["domaine"])
            emoji = get_domain_emoji(p["domaine"])
            sieges_btns[coord].configure(text=f"{emoji} {p['nom'][:3]}\n{p['poste'][:8]}\nSiège {sieges_numeros[coord]}", fg_color=color, text_color=COLOR_TEXT)
            maj_stats()
            sauvegarder_donnees()

            en_nom.delete(0, 'end')
            origine_var.set("")
            en_ent.delete(0, 'end')
            en_dom.delete(0, 'end')
            en_pos.delete(0, 'end')
            equipe_var.set("")
            messagebox.showinfo("Succès", f"✅ {nom} placé avec succès !")
            return

    messagebox.showwarning("Attention", "⚠️ Aucune place ne respecte les contraintes pour ce profil.")

# --- INTERFACE ---

# Barre latérale (Saisie) - Modernisée
sidebar = ctk.CTkFrame(app, width=260, fg_color=COLOR_SIDEBAR, corner_radius=0)
sidebar.pack(side="left", fill="y", padx=0, pady=0)

sidebar_content = ctk.CTkScrollableFrame(sidebar, width=260, height=800, fg_color="transparent")
sidebar_content.pack(fill="both", expand=True, padx=6, pady=6)

ctk.CTkLabel(sidebar_content, text="INFOS MEMBRE", font=("Arial", 18, "bold"), text_color=COLOR_GOLD).pack(pady=(10, 8))

en_nom = ctk.CTkEntry(sidebar_content, placeholder_text="Nom complet", width=220, height=40, font=("Arial", 12), border_width=1, border_color=COLOR_GOLD)
en_nom.pack(pady=2)
ctk.CTkLabel(sidebar_content, text="Origine", font=("Arial", 12, "bold"), text_color=COLOR_GOLD).pack(pady=(10, 8), anchor="w", padx=5)
origine_var = ctk.StringVar(value="")
origine_menu = ctk.CTkComboBox(sidebar_content, values=["Blanc", "Noir", "Asiatique", "Amérindien"], variable=origine_var, width=220, height=40, font=("Arial", 12))
origine_menu.pack(pady=2)
en_ent = ctk.CTkEntry(sidebar_content, placeholder_text="Entreprise", width=220, height=40, font=("Arial", 12), border_width=1, border_color=COLOR_GOLD)
en_ent.pack(pady=2)
en_dom = ctk.CTkEntry(sidebar_content, placeholder_text="Domaine", width=220, height=40, font=("Arial", 12), border_width=1, border_color=COLOR_GOLD)
en_dom.pack(pady=2)
en_pos = ctk.CTkEntry(sidebar_content, placeholder_text="Poste", width=220, height=40, font=("Arial", 12), border_width=1, border_color=COLOR_GOLD)
en_pos.pack(pady=2)
ctk.CTkLabel(sidebar_content, text="Équipe", font=("Arial", 12, "bold"), text_color=COLOR_GOLD).pack(pady=(10, 8), anchor="w", padx=5)
equipe_var = ctk.StringVar(value="")
equipe_menu = ctk.CTkComboBox(sidebar_content, values=["1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "Aucune"], variable=equipe_var, width=220, height=40, font=("Arial", 12))
equipe_menu.pack(pady=2)

ctk.CTkLabel(sidebar_content, text="Sexe", font=("Arial", 12, "bold"), text_color=COLOR_GOLD).pack(pady=(10, 8), anchor="w", padx=5)
sex_var = ctk.StringVar(value="M")

sex_frame = ctk.CTkFrame(sidebar_content, fg_color="transparent")
sex_frame.pack(pady=(0, 8))

def select_sexe(value):
    sex_var.set(value)
    update_sexe_buttons()

def update_sexe_buttons():
    if sex_var.get() == "M":
        btn_homme.configure(fg_color=COLOR_BTN_M, text_color=COLOR_TEXT)
        btn_femme.configure(fg_color=COLOR_BTN_EMPTY, text_color=COLOR_TEXT_MUTED)
    else:
        btn_homme.configure(fg_color=COLOR_BTN_EMPTY, text_color=COLOR_TEXT_MUTED)
        btn_femme.configure(fg_color=COLOR_BTN_F, text_color=COLOR_TEXT)


btn_homme = ctk.CTkButton(sex_frame, text="♂ Homme", font=("Arial", 12, "bold"), 
                          width=100, height=38, command=lambda: select_sexe("M"), corner_radius=6)
btn_homme.pack(side="left", padx=3)

btn_femme = ctk.CTkButton(sex_frame, text="♀ Femme", font=("Arial", 12, "bold"), 
                          width=100, height=38, command=lambda: select_sexe("F"), corner_radius=6)
btn_femme.pack(side="left", padx=3)

update_sexe_buttons()


ctk.CTkButton(sidebar_content, text="PLACER MEMBRE", fg_color=COLOR_BTN_M, text_color=COLOR_TEXT, font=("Arial", 13, "bold"), 
              height=42, corner_radius=8, command=placer_membre).pack(pady=12)
ctk.CTkButton(
    sidebar_content,
    text="IMPORTER CSV",
    fg_color=COLOR_GREEN,
    text_color=COLOR_TEXT,
    font=("Arial", 12, "bold"),
    height=40,
    corner_radius=8,
    command=importer_csv
).pack(pady=8)

ctk.CTkButton(
    sidebar_content,
    text="IMPRIMER FICHE",
    fg_color=COLOR_RED,
    text_color=COLOR_TEXT,
    font=("Arial", 12, "bold"),
    height=40,
    corner_radius=8,
    command=generer_fiche
).pack(pady=8)

ctk.CTkButton(
    sidebar_content,
    text="RÉINIT",
    fg_color=COLOR_RED,
    text_color=COLOR_TEXT,
    font=("Arial", 11, "bold"),
    height=38,
    corner_radius=8,
    command=reinitialiser_donnees
).pack(pady=8)


# Compteurs
ctk.CTkLabel(sidebar_content, text="STATISTIQUES", font=("Arial", 14, "bold"), text_color=COLOR_GOLD).pack(pady=(20, 8))
stats_h = ctk.CTkLabel(sidebar_content, text="♂ Hommes: 0", font=("Arial", 13, "bold"), text_color=COLOR_BTN_M)
stats_h.pack(pady=4)
stats_f = ctk.CTkLabel(sidebar_content, text="♀ Femmes: 0", font=("Arial", 13, "bold"), text_color=COLOR_BTN_F)
stats_f.pack(pady=4)
stats_percent = ctk.CTkLabel(sidebar_content, text="Remplissage: 0% (0/48)", font=("Arial", 13, "bold"), text_color=COLOR_GREEN)
stats_percent.pack(pady=4)

def afficher_aide():
    aide_text = """
    SYSTÈME EXPERT DE PLACEMENT AMPHITHÉÂTRE

    RÈGLES DE PLACEMENT :
    - Pas de personnes du même sexe adjacentes
    - Pas de personnes du même domaine à proximité
    - Pas de collègues de la même entreprise proches
    - Pas de personnes du même poste adjacentes
    - Pas de personnes de la même origine à proximité
    - Deux personnes d'une même équipe ne peuvent pas être côte à côte

    UTILISATION :
    1. Importer un CSV avec colonnes : nom,origine,entreprise,domaine,poste,sexe,equipe
       (Origines : Blanc, Noir, Asiatique, Amérindien)
       (Équipe : numéro 1-10 ou vide)
    2. Placer manuellement via le formulaire
    3. Générer la fiche finale
    4. Sauvegarde automatique des données

    RACCOURCIS :
    - Ctrl+S : Sauvegarder manuellement
    - F1 : Aide
    """
    messagebox.showinfo("Aide - Système Expert", aide_text)

def exporter_csv():
    if stats["Total"] == 0:
        messagebox.showwarning("Attention", "Aucune donnée à exporter.")
        return
    
    fichier = filedialog.asksaveasfilename(
        title="Exporter vers CSV",
        defaultextension=".csv",
        filetypes=[("Fichiers CSV", "*.csv")]
    )
    
    if not fichier:
        return
    
    try:
        with open(fichier, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(["Siège", "Nom", "Origine", "Entreprise", "Domaine", "Poste", "Sexe"])
            
            for coord in sorted(sieges_data.keys()):
                if sieges_data[coord] is not None:
                    p = sieges_data[coord]
                    writer.writerow([
                        sieges_numeros[coord],
                        p['nom'],
                        p['origine'],
                        p['entreprise'],
                        p['domaine'],
                        p['poste'],
                        "Homme" if p['sexe'] == "M" else "Femme"
                    ])
        
        update_status("Export CSV réussi")
        messagebox.showinfo("Succès", f"✅ Exporté vers {fichier}")
    except Exception as e:
        update_status("Erreur export CSV")
        messagebox.showerror("Erreur", f"Erreur lors de l'export : {e}")




# Zone Map
map_frame = ctk.CTkFrame(app, fg_color=COLOR_BG, corner_radius=0)
map_frame.pack(side="right", expand=True, fill="both", padx=0, pady=0)

# Suppression du cadre central et du cadre de grille, on place tout directement dans map_frame
# Titre du plan
title_label = ctk.CTkLabel(map_frame, text="PLAN DE L'AMPHITHÉÂTRE", font=("Arial", 18, "bold"), text_color=COLOR_GOLD)
title_label.pack(pady=3)

# Grille directement dans map_frame
grid_container = ctk.CTkFrame(map_frame, fg_color=COLOR_GRID_BG, corner_radius=0)
grid_container.pack(expand=True, fill="both", padx=0, pady=0)


# Nouvelle fonction de gestion du clic pour déplacement manuel
def on_seat_click(coord):
    # Si aucun siège sélectionné
    if selected_seat[0] is None:
        if sieges_data[coord] is not None:
            # Sélectionner ce siège
            selected_seat[0] = coord
            sieges_btns[coord].configure(border_width=4, border_color=COLOR_STATUS)
        else:
            # Siège vide : afficher info
            messagebox.showinfo("Siège vide", f"Siège {sieges_numeros[coord]} (Ligne {coord[0]+1}, Colonne {coord[1]+1}) est vide.")
    else:
        # Un siège est déjà sélectionné
        if coord == selected_seat[0]:
            # Reselection du même siège : désélectionner
            sieges_btns[coord].configure(border_width=0)
            selected_seat[0] = None
        elif sieges_data[coord] is None:
            # Déplacement possible
            src = selected_seat[0]
            participant = sieges_data[src]
            sieges_data[coord] = participant
            sieges_data[src] = None
            # Mettre à jour les boutons
            color = get_domain_color(participant["domaine"])
            emoji = get_domain_emoji(participant["domaine"])
            sieges_btns[coord].configure(
                text=f"{emoji} {participant['nom'][:3]}\n{participant['poste'][:8]}\nSiège {sieges_numeros[coord]}",
                fg_color=color,
                text_color=COLOR_TEXT,
                border_width=0
            )
            sieges_btns[src].configure(text="", fg_color=COLOR_BTN_EMPTY, text_color=COLOR_TEXT_MUTED, border_width=0)
            selected_seat[0] = None
            sauvegarder_donnees()
            maj_stats()
            update_status(f"Déplacement effectué vers siège {sieges_numeros[coord]}")
        else:
            # Siège occupé : afficher détails
            p = sieges_data[coord]
            details = f"""
            DÉTAILS DU SIÈGE {sieges_numeros[coord]}

            Nom : {p['nom']}
            Âge : {p['age']} ans
            Entreprise : {p['entreprise']}
            Domaine : {p['domaine']}
            Poste : {p['poste']}
            Sexe : {"Homme" if p['sexe'] == "M" else "Femme"}

            Position : Ligne {coord[0]+1}, Colonne {coord[1]+1}
            """
            messagebox.showinfo("Détails du participant", details)
            # Réinitialiser la sélection précédente
            sieges_btns[selected_seat[0]].configure(border_width=0)
            selected_seat[0] = None

# Configure grid weights for responsive layout
for r in range(12):
    grid_container.grid_rowconfigure(r, weight=0, minsize=70)
for c in range(16):
    grid_container.grid_columnconfigure(c, weight=0, minsize=70)


for (r, c) in places_exactes:
    btn = ctk.CTkButton(grid_container, text="", fg_color=COLOR_BTN_EMPTY, corner_radius=4, font=("Arial", 9, "bold"), hover_color=COLOR_BTN_HOVER, width=60, height=60, text_color=COLOR_TEXT_MUTED)
    btn.configure(command=lambda coord=(r,c): on_seat_click(coord))
    btn.grid(row=r, column=c, padx=2, pady=2, sticky="")
    sieges_btns[(r, c)] = btn


# Podium modernisé et arrondi - RANGÉE 8
podium = ctk.CTkLabel(grid_container, text="🎤 PODIUM 🎤", fg_color=COLOR_GOLD, 
                      text_color=COLOR_BG, font=("Arial", 20, "bold"), corner_radius=12, width=300, height=80)
podium.grid(row=8, column=5, columnspan=6, padx=5, pady=20, sticky="ew")
grid_container.grid_rowconfigure(8, weight=0, minsize=110)


# Sauvegarder les données à la fermeture
def on_closing():
    sauvegarder_donnees()
    app.destroy()

def on_key_press(event):
    if event.keysym == 'F1':
        afficher_aide()
    elif event.state & 4 and event.keysym == 's':  # Ctrl+S
        sauvegarder_donnees()
        update_status("Données sauvegardées manuellement")

app.bind('<Key>', on_key_press)


# Barre de statut
status_bar = ctk.CTkFrame(app, height=22, fg_color=COLOR_BG, corner_radius=0)
status_bar.pack(side="bottom", fill="x", padx=0, pady=0)

status_label = ctk.CTkLabel(status_bar, text="Prêt - Système Expert de Placement Amphithéâtre", font=("Arial", 10), text_color=COLOR_STATUS)
status_label.pack(side="left", padx=10)

def update_status(message):
    status_label.configure(text=message)
    app.after(3000, lambda: status_label.configure(text="Prêt - Système Expert de Placement Amphithéâtre"))

# Charger les données au démarrage
charger_donnees()

app.mainloop()
