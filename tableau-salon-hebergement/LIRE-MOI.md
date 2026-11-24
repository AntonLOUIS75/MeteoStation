# Tableau du salon — version hébergeable

Météo Paris–Montsouris et bus 21 / 64 à Glacière–Auguste Blanqui, dans les deux sens. Cette version remplace le serveur local de la première archive par Flask + Waitress, utilisables sur Windows et sur un hébergement Python ou Docker. Python 3.10 ou plus récent requis ; Python 3.12 conseillé.

## Les changements

- Rafraîchissement des bus : 15 secondes après chaque réponse, tant que la page est active. Les délais réseau peuvent allonger ce cycle ; les onglets en arrière-plan peuvent être ralentis par le navigateur.
- Cache serveur de 15 secondes, partagé par les deux lignes et tous les visiteurs d'un même processus. Il n'y a plus de minimum de 60 secondes ni de ralentissement calculé à partir de l'ancien budget de 900 appels.
- Météo : toujours 30 minutes. Données de modèle aux coordonnées du parc Montsouris, pas mesures directes de la station Météo-France.
- En cas d'erreur, les anciennes données sont signalées. Un quota dépassé entraîne une pause d'au moins 60 secondes, ou davantage si PRIM le demande.
- La clé reste côté serveur. Elle peut être lue dans `prim-key.txt` ou dans la variable secrète `PRIM_API_KEY` (prioritaire).
- Après hébergement, la tablette ouvre simplement l'URL HTTPS : ni ordinateur allumé ni Termux nécessaire.

Les appels sont déclenchés par la consultation du tableau : aucun appel périodique n'est effectué lorsqu'aucune page n'est ouverte. Interroger toutes les 15 secondes ne garantit pas que le fournisseur produise de nouvelles prévisions à cette fréquence.

## 1. Tester sur Windows

1. Extrais l'archive dans un **nouveau dossier**. Ne mélange pas les deux versions.
2. Copie ton fichier `prim-key.txt` existant à côté du nouveau `server.py`. Tu peux aussi créer ce fichier avec le Bloc-notes : une seule clé, sans guillemets ni préfixe `apikey`. Enregistre en UTF-8, avec le nom exact `prim-key.txt`.
3. Arrête l'ancien serveur avec Ctrl+C pour libérer le port 8000.
4. Double-clique sur **demarrer-windows.bat**. Il crée un environnement Python et installe les dépendances. L'installation nécessite Internet.
5. Quand le serveur est prêt, ouvre **http://localhost:8000**.
6. Garde la fenêtre ouverte. Ctrl+C permet d'arrêter le serveur.

Alternative manuelle, dans un terminal ouvert dans le dossier :

```bat
py -m venv .venv
.venv\Scripts\python.exe -m pip install -r requirements.txt
.venv\Scripts\python.exe server.py
```

Sans clé, la météo et l'horloge fonctionnent, le panneau transports signale la configuration manquante. L'ancien fichier `configure_key.py` reste disponible, mais il est facultatif.

## 2. Héberger sur Render

Le projet est prêt à être envoyé, mais n'est pas encore publié. Il faut créer les comptes et lancer le déploiement depuis ton compte. La page sera accessible aux personnes disposant de son adresse ; cette version ne contient pas de connexion utilisateur.

### A. Mettre les codes sur GitHub

1. Crée un compte sur https://github.com/ si nécessaire.
2. Crée un dépôt nommé par exemple `tableau-salon`, de préférence privé.
3. Envoie **le contenu du dossier extrait à la racine du dépôt** : `server.py`, `services.py`, `config.json`, `requirements.txt`, le dossier `static`, et éventuellement les autres fichiers fournis.
4. **N'envoie jamais `prim-key.txt`, `.env` ni le dossier `.venv`.** Le fichier `.gitignore` les exclut avec Git, mais un ajout manuel par le navigateur demande aussi cette vérification. Le fichier de clé est réservé au test sur PC.

### B. Créer le service

1. Connecte-toi sur https://render.com/ .
2. Choisis **New → Web Service** et connecte le dépôt GitHub. Choisis bien un service web Python, pas un Static Site.
3. Renseigne :

| Réglage | Valeur |
|---|---|
| Language / Runtime | Python 3 |
| Root Directory | Laisser vide si les fichiers sont à la racine |
| Build Command | `pip install -r requirements.txt` |
| Start Command | `python server.py` |
| Health Check Path | `/healthz` |

4. Dans **Environment**, ajoute :

| Variable | Valeur |
|---|---|
| `HOST` | `0.0.0.0` |
| `PRIM_API_KEY` | Ta clé PRIM complète, sans guillemets |

Le programme lit automatiquement le `PORT` fourni par Render. La clé doit être saisie dans les variables du service, pas dans le dépôt ni dans le JavaScript.

5. Choisis l'offre adaptée à ton usage puis lance le déploiement. Render fournit une URL HTTPS après réussite.
6. Ouvre cette URL sur le PC puis sur la tablette. Vérifie météo, destinations, prochains départs et indication « actualisation toutes les 15 secondes ».

Un fichier `render.yaml` est aussi fourni pour une création via Blueprint. Il demande la clé au déploiement ; vérifie l'offre et son coût avant validation. La procédure manuelle ci-dessus permet de choisir explicitement l'offre.

L'offre gratuite est adaptée à un premier test. Render documente une mise en veille après 15 minutes sans trafic, des limites d'utilisation et des redémarrages possibles. Pour un affichage permanent, choisis une offre adaptée plutôt que de compter sur une disponibilité continue garantie de l'offre gratuite.

### C. Sur la tablette

Ouvre l'URL HTTPS du site, ajoute un raccourci à l'écran d'accueil et appuie sur **Mode salon**. Autorise le maintien de l'écran actif ou règle la veille dans Android. Le Wi-Fi et l'alimentation suffisent. Le lancement automatique du navigateur après un redémarrage de la tablette dépend toujours du modèle et de ses réglages.

## 3. Autre hébergeur Python

Il doit accepter une application Python persistante, des connexions HTTPS sortantes et des variables d'environnement.

- Installation : `pip install -r requirements.txt`
- Démarrage : `python server.py`
- Variables : `HOST=0.0.0.0`, `PORT` fourni par l'hébergeur, `PRIM_API_KEY` secret.
- Un seul processus / une seule instance pour partager le cache. Waitress utilise déjà plusieurs threads. Plusieurs instances multiplieraient les appels PRIM.
- L'hébergeur ou son reverse proxy doit fournir HTTPS pour les visiteurs. Waitress écoute en HTTP derrière ce proxy.

Un hébergement HTML seul ou un espace PHP sans exécution Python ne peut pas faire tourner cette archive. Elle ne se dépose donc pas simplement sur n'importe quel FTP.

## 4. Docker / VPS

Construis l'image depuis ce dossier :

```sh
docker build -t tableau-salon .
```

Crée sur le serveur un fichier `.env` contenant :

```text
PRIM_API_KEY=COLLER_TA_CLE_ICI
```

Puis :

```sh
docker run -d --name tableau-salon --restart unless-stopped --env-file .env -p 127.0.0.1:8000:8000 tableau-salon
```

Le conteneur écoute sur le port 8000, accessible uniquement depuis le VPS. Configure ensuite ton reverse proxy HTTPS (par exemple celui fourni par ton hébergeur) vers `http://127.0.0.1:8000`. Le Dockerfile ne copie pas de clé. Le fichier `.dockerignore` exclut également les secrets. L'accès distant nécessite la configuration du domaine et du reverse proxy, propre au VPS choisi.

## 5. Quota PRIM : à augmenter pour 15 secondes

Un seul appel récupère la zone d'arrêt commune aux bus 21 et 64. À un appel toutes les 15 secondes, le maximum nominal est **5 760 appels par jour**, hors redémarrages et tes autres usages de la clé. Le quota par défaut publié est **1 000 par jour** : il serait épuisé après environ 4 h 10 de consultation continue.

Sur PRIM, connecte-toi et ouvre **Ma consommation API** pour demander une augmentation. Demande au moins 6 000 appels/jour pour ce tableau seul, avec une marge adaptée si tu utilises la même clé ailleurs. Le code applique déjà 15 secondes ; il ne peut pas augmenter ton quota lui-même.

## Structure et validation

- `server.py` : serveur web de production Waitress, routes Flask et port d'hébergement.
- `services.py` : services météo et bus, filtre des lignes et cache.
- `static/` : HTML, CSS et JavaScript.
- `config.json` : Montsouris, zone 470522, lignes C01073 et C01100, délai de 15 secondes.
- `requirements.txt` : dépendances Python.
- `demarrer-windows.bat` : lancement local par double-clic.
- `Dockerfile`, `render.yaml` : fichiers de déploiement.
- `test_app.py` : tests automatisés ; lancer `python -m unittest -v test_app` après installation des dépendances.

Les tests contrôlent les routes, l'absence d'exposition de la clé, la lecture du fichier de clé, le cache à 15 secondes et les filtres des deux lignes. La connexion PRIM réelle reste à vérifier avec ta clé. L'archive ne contient aucune clé ni aucun horaire inventé pour l'affichage.

Sources consultées le 24 novembre 2026 :
- https://render.com/docs/deploy-flask
- https://render.com/docs/free
- https://flask.palletsprojects.com/en/stable/deploying/waitress/
- https://prim.iledefrance-mobilites.fr/fr/apis/idfm-ivtr-requete_unitaire
