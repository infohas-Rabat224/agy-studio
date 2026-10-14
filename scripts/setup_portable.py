import os
import sys
import json
import shutil
import subprocess
from pathlib import Path

def main():
    print("=" * 65)
    print("        AGY STUDIO PORTABLE - SETUP & INITIALISATION")
    print("  Configuration automatique pour environnement Windows 11")
    print("=" * 65)
    print()

    app_root = Path(__file__).resolve().parent.parent
    runtime_uv = app_root / "runtime" / "uv.exe"
    skills_dir = app_root / "skills"

    print(f"[*] Dossier Agy Studio Portable : {app_root}")
    print()

    # 1. Vérification UV
    print("[1/4] Vérification du runtime Python autonome (Astral UV)...")
    if runtime_uv.exists():
        print(f"    [OK] UV autonome présent : {runtime_uv}")
        try:
            res = subprocess.run([str(runtime_uv), "--version"], capture_output=True, text=True)
            print(f"    Version : {res.stdout.strip()}")
        except Exception as e:
            print(f"    Note : {e}")
    else:
        print("    [ATTENTION] runtime/uv.exe manquant. Recherche de uv sur le système...")
        found_uv = shutil.which("uv")
        if found_uv:
            print(f"    [OK] UV système trouvé : {found_uv}")
        else:
            print("    [ERREUR] uv.exe introuvable. Installez UV ou replacez runtime/uv.exe.")
    print()

    # 2. Détection agy CLI
    print("[2/4] Détection de Antigravity CLI (agy)...")
    agy_exe = shutil.which("agy")
    if not agy_exe:
        local_app = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData" / "Local"))
        candidates = [
            local_app / "agy" / "bin" / "agy.EXE",
            local_app / "agy" / "bin" / "agy.exe",
            app_root / "runtime" / "agy.EXE",
        ]
        for c in candidates:
            if c.exists():
                agy_exe = str(c)
                break

    if agy_exe:
        print(f"    [OK] agy CLI détecté : {agy_exe}")
        try:
            res = subprocess.run([agy_exe, "--version"], capture_output=True, text=True, timeout=5)
            ver = res.stdout.strip() or res.stderr.strip()
            if ver:
                print(f"    Version agy : {ver}")
        except Exception:
            pass
    else:
        print("    [ATTENTION] agy CLI n'a pas été détecté automatiquement.")
        print("    Assurez-vous que Antigravity CLI est bien installé sur cette machine.")
    print()

    # 3. Liaison globale des compétences (Skills)
    print("[3/4] Enregistrement du catalogue de compétences...")
    if skills_dir.exists():
        skill_count = len(list(skills_dir.glob("**/SKILL.md")))
        print(f"    Dossier de compétences : {skills_dir} ({skill_count} compétences détectées)")

        # Enregistrement dans ~/.gemini/config/skills.json
        gemini_config_dir = Path.home() / ".gemini" / "config"
        gemini_config_dir.mkdir(parents=True, exist_ok=True)
        skills_cfg_file = gemini_config_dir / "skills.json"

        skills_path_normalized = str(skills_dir.resolve()).replace("\\", "/")
        entries = []
        if skills_cfg_file.exists():
            try:
                with open(skills_cfg_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    entries = data.get("entries", [])
            except Exception:
                entries = []

        if not any(e.get("path") == skills_path_normalized for e in entries if isinstance(e, dict)):
            entries.append({"path": skills_path_normalized})
            with open(skills_cfg_file, "w", encoding="utf-8") as f:
                json.dump({"entries": entries}, f, indent=2)
            print(f"    [OK] Compétences enregistrées dans {skills_cfg_file}")
        else:
            print(f"    [OK] Compétences déjà déclarées dans {skills_cfg_file}")

        # Optionnel : jonction NTFS si ~/.gemini/skills n'existe pas
        user_skills_dir = Path.home() / ".gemini" / "skills"
        if not user_skills_dir.exists():
            try:
                user_skills_dir.parent.mkdir(parents=True, exist_ok=True)
                subprocess.run(
                    ["cmd", "/c", "mklink", "/J", str(user_skills_dir), str(skills_dir)],
                    capture_output=True
                )
                if user_skills_dir.exists():
                    print(f"    [OK] Jonction NTFS créée : ~/.gemini/skills -> {skills_dir}")
            except Exception:
                pass
    else:
        print(f"    [ERREUR] Dossier {skills_dir} manquant !")
    print()

    # 4. Création du raccourci sur le Bureau
    print("[4/4] Création du raccourci Bureau pour Agy Studio...")
    desktop_dir = Path.home() / "Desktop"
    shortcut_path = desktop_dir / "Agy Studio.lnk"
    target_exe = app_root / "AgyStudio.exe"
    icon_candidate = app_root / "static" / "favicon.ico"

    if desktop_dir.exists() and target_exe.exists():
        ps_script = f"""
$wsh = New-Object -ComObject WScript.Shell
$sc = $wsh.CreateShortcut('{str(shortcut_path)}')
$sc.TargetPath = '{str(target_exe)}'
$sc.WorkingDirectory = '{str(app_root)}'
$sc.Description = 'Agy Studio - Agentic AI Workspace'
if (Test-Path '{str(icon_candidate)}') {{
    $sc.IconLocation = '{str(icon_candidate)}'
}}
$sc.Save()
"""
        try:
            subprocess.run(["powershell", "-NoProfile", "-Command", ps_script], capture_output=True)
            print(f"    [OK] Raccourci créé sur le Bureau : {shortcut_path}")
        except Exception as e:
            print(f"    [Note] Impossible de créer le raccourci Bureau : {e}")
    print()

    print("=" * 65)
    print("      INITIALISATION PORTABLE TERMINEE AVEC SUCCES !")
    print("=" * 65)
    print()
    print("Vous pouvez lancer l'application avec :")
    print("  - AgyStudio.exe (Lanceur natif production)")
    print("  - start-studio.bat (Script batch)")
    print("  - Le raccourci Bureau 'Agy Studio'")
    print()

if __name__ == "__main__":
    main()
