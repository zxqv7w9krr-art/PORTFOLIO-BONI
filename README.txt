APPLICATION DE PLACEMENT EN AMPHITHÉÂTRE

Cette application de bureau a été développée avec Python et CustomTkinter.
Elle utilise aussi FileLock pour protéger l'accès au fichier JSON de sauvegarde.

LANCEMENT SOUS WINDOWS

1. Installe Python 3 depuis python.org.
2. Ouvre PowerShell dans le dossier contenant amphi_final.py.
3. Installe les dépendances avec :
   py -m pip install customtkinter filelock
4. Lance l'application avec :
   py amphi_final.py

Les placements sont sauvegardés dans placements.json dans le dossier courant.
L'application peut importer et exporter des listes CSV et générer une fiche HTML.
Les fichiers de données personnels ne sont pas inclus dans ce portfolio.
