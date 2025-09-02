# GameJam 2k25

Jeu 2D basé sur **Pygame** avec chargement de cartes **Tiled** via **PyTMX**.

**Politique de dépendances** : uniquement la bibliothèque standard Python (hors modules graphiques), **pygame** et **pytmx**.

---

## 1) Prérequis

- Python **3.9 à 3.12** (recommandé : 3.11 ou 3.12)
- Un terminal (PowerShell, Terminal, etc.)

Vérifier Python :
```bash
python --version || python3 --version || py --version
```

---

## 2) Installation (environnement virtuel local)

Exécutez ces commandes **depuis la racine du projet** (là où se trouve ce README).

### macOS / Linux
```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Windows (PowerShell)
```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```
> Si PowerShell refuse l’activation, lancez **cmd.exe** puis :
> ```bat
> .\.venv\Scripts\activate.bat
> ```

---

## 3) Lancer le jeu
Depuis la racine (venv activé) :
```bash
python src/main.py
```

---

## 4) Structure 

---

## 5) Dépendances autorisées
- Standard library (hors modules graphiques)
- `pygame`
- `pytmx`

---
