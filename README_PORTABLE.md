# 🚀 Agy Studio Portable — Guide de Déploiement Windows 11

Cette version de **Agy Studio** est 100% autonome et portable. Elle a été préparée pour fonctionner immédiatement sur n'importe quel PC équipé de **Windows 11** sur lequel **Antigravity CLI (`agy`)** est installé.

---

## 📦 Contenu du Package Portable

```text
Agy Studio/
├── AgyStudio.exe                 # ⚡ Lanceur de production ultra-rapide (C# / .NET natif sans dépendance)
├── start-studio.bat              # 🚀 Lanceur alternatif Batch
├── setup-portable.bat            # 🛠️ Configuration en 1 clic pour nouvelle machine
├── AgyStudioFolderPicker.exe     # 📁 Pont natif Win32/WinForms de sélection de dossiers (Port 8001)
├── runtime/
│   └── uv.exe                    # 🐍 Moteur Python autonome Astral UV (zéro installation requise)
├── skills/                       # 🧠 Catalogue complet de 130 compétences agentiques (SKILL.md)
│   ├── cahierdetext/             #    - Cahier de texte officiel ATAM (M1..M22, cantSplit, 0 page blanche)
│   ├── adaptive-suite/           #    - Suite d'ingénierie et mémoire
│   ├── agent-autonomy-kit/       #    - Exécution autonome Queue-First
│   ├── frontend-design/          #    - Design UI/UX moderne Tailwind
│   ├── ui-ux-pro-max/            #    - Directives visuelles avancées
│   ├── vps-manager/              #    - Administration serveurs et cloud
│   └── ... (130 compétences)
├── backend/                      # ⚙️ Serveur FastAPI + adaptateurs multi-agents
├── static/                       # 🎨 Interface Studio Web réactive
├── scripts/                      # 📜 Utilitaires de maintenance et validation
└── data/                         # 💾 Stockage local des sessions, artefacts et configurations
```

---

## 🎯 Prérequis sur la Nouvelle Machine Windows 11

1. **Windows 11** (x64)
2. **Antigravity CLI (`agy`)** installé sur la machine
3. *Aucune installation manuelle de Python ou de bibliothèques n'est requise* (le moteur autonome `runtime\uv.exe` s'occupe de tout).

---

## ⚡ Installation & Démarrage en 1 Clic

### Étape 1 : Copier le dossier
Copiez le dossier `Agy Studio` à l'emplacement de votre choix sur le nouveau PC (par exemple `C:\Agy Studio`, sur le disque `D:\`, ou même sur une clé USB / SSD externe).

### Étape 2 : Initialisation initiale (1 seule fois)
Double-cliquez sur :
```text
setup-portable.bat
```
Ce script effectue automatiquement en quelques secondes :
- ✅ La détection de `agy.exe` et de `runtime\uv.exe`
- ✅ L'enregistrement global des **130 compétences** dans `~/.gemini/config/skills.json` (et jonction NTFS `~/.gemini/skills`)
- ✅ La création du raccourci **Agy Studio** sur votre Bureau Windows
- ✅ La proposition de lancement immédiat de l'application

### Étape 3 : Utilisation quotidienne
Lancez Agy Studio à tout moment en double-cliquant sur :
- Le raccourci sur le Bureau **Agy Studio**
- Ou `AgyStudio.exe`
- Ou `start-studio.bat`

L'application ouvrira automatiquement une fenêtre dédiée en mode application via Google Chrome ou Microsoft Edge (pré-installé sur tout Windows 11).

---

## 🧠 Comment les Skills Fonctionnent sur la Nouvelle Machine

1. **Dans Agy Studio** :
   - Dès qu'un workspace est sélectionné ou qu'une session démarre, Agy Studio injecte automatiquement la configuration `.agents/skills.json` pointant vers le dossier local `skills/`.
   - L'agent IA d'Antigravity détecte et active les compétences appropriées à chaque prompt.
2. **En Ligne de Commande (PowerShell / CMD)** :
   - Grâce à l'enregistrement dans `~/.gemini/config/skills.json`, vous pouvez lancer n'importe quelle commande `agy` n'importe où dans le terminal, et elle aura accès immédiat à toutes vos compétences :
     ```powershell
     agy -p "Utilise cahierdetext pour générer le classeur formateur"
     ```

---

## 🔧 Dépannage Rapide

- **Le navigateur ne s'ouvre pas automatiquement ?**
  Ouvrez manuellement votre navigateur sur `http://127.0.0.1:8000`.
- **Un port est déjà occupé ?**
  Le lanceur nettoie automatiquement les ports orphelins (8000 et 8001) avant le démarrage.
- **Ajout d'une nouvelle compétence ?**
  Déposez simplement le dossier de votre compétence avec son fichier `SKILL.md` dans le répertoire `skills/`. Elle sera immédiatement reconnue par Agy Studio et `agy` CLI !

---

## 🌟 Nouvelles Fonctionnalités Majeures (v2.0)

Agy Studio intègre désormais 8 modules avancés accessibles depuis la barre d'actions supérieure, la barre d'état ou via des raccourcis clavier :

1. **Éditeur de Code Intégré & Visualiseur de Diff (Monaco Editor)**
   - Éditeur natif VS Code (Monaco Editor) avec coloration syntaxique complète, numéros de ligne, minimap et recherche (`Ctrl+F`).
   - Visualiseur Split-Diff côte-à-côte pour inspecter et valider les modifications proposées par l'agent.
   - Sauvegarde directe avec `Ctrl+S`.

2. **Terminal Interactif Web Intégré (xterm.js + WebSocket PTY)**
   - Terminal PowerShell interactif escamotable au bas de l'écran avec le raccourci `Ctrl+\`` ou le bouton dans la barre d'état.
   - Streaming temps réel bidirectionnel, historique des commandes, coloration ANSI complète et redimensionnement dynamique.

3. **Contrôle de Version Git & GitHub Intégré (Visual Git GUI)**
   - Visualisation de l'état des fichiers modifiés, non suivis et indexés.
   - Graphe interactif des branches et commits du workspace.
   - Génération automatique de messages de commit conventionnels (`feat: ...`, `fix: ...`) par IA.
   - Actions 1-clic : Commit, Push, Pull, Création de branches.

4. **File d'Attente d'Autonomie en Tâche de Fond (Background Agent & Ghost Mode)**
   - Basé sur la compétence intégrée `agent-autonomy-kit`.
   - File d'attente de tâches prioritaires avec suivi des statuts (`pending`, `running`, `completed`, `failed`).
   - Notifications Toast Windows 11 natives transmises via WinRT pour avertir l'utilisateur lors de l'achèvement d'une tâche.

5. **Cartographie Visuelle du Projet & Graphe des Dépendances (GraphView / Mermaid)**
   - Analyseur de code AST/Regex scannant l'arborescence des fichiers du workspace (.py, .ts, .js, .json).
   - Rendu visuel interactif en graphe Mermaid des liaisons d'importation et composants d'architecture.

6. **Coffre-fort de Clés & Variables d'Environnement (.env Vault)**
   - Gestionnaire sécurisé des clés d'API globales et par workspace (`GEMINI_API_KEY`, `ANTHROPIC_API_KEY`, `OPENAI_API_KEY`, `TAVILY_API_KEY`, `CLOUDFLARE_API_TOKEN`, etc.).
   - Masquage des secrets par astérisques avec bouton afficher/masquer.
   - Anonymisation automatique dans les flux et logs.

7. **Interface Vocale & Dictée (Voice-to-Prompt & Synthèse Vocale)**
   - Bouton micro intégré directement dans la zone de saisie de prompt (Web Speech API / reconnaissance vocale).
   - Synthèse vocale intégrée pour écouter à haute voix le résumé des réponses et actions de l'agent.

8. **Déploiement Cloud en 1 Clic (Cloudflare Pages, Vercel, Clean ZIP)**
   - Déploiement direct vers Cloudflare Pages avec jeton d'API et identifiant de compte Cloudflare.
   - Exportateur de distribution propre ("Clean Dist ZIP") excluant automatiquement `node_modules`, `.venv`, `.git`, `__pycache__` et fichiers temporaires.

