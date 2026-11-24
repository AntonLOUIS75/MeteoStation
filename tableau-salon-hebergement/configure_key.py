from getpass import getpass
from pathlib import Path
import os
key = getpass('Colle ta clé PRIM (elle reste invisible), puis Entrée : ').strip()
if not key:
    raise SystemExit('Clé vide : aucun changement.')
p = Path(__file__).resolve().parent / 'prim-key.txt'
p.write_text(key, encoding='utf-8')
os.chmod(p, 0o600)
print('Clé enregistrée. Tu peux lancer le serveur.')
