"""Verifica che Python, Git e uv siano installati. Non installa e non modifica nulla."""

import shutil
import subprocess
import sys


def versione(comando):
    percorso = shutil.which(comando)
    if not percorso:
        return None
    try:
        esito = subprocess.run([percorso, "--version"], capture_output=True, text=True, timeout=10)
        return (esito.stdout or esito.stderr).strip()
    except (OSError, subprocess.SubprocessError):
        return None


def main():
    print("Verifica dei requisiti del workshop\n")
    ok = True

    py = ".".join(map(str, sys.version_info[:3]))
    if sys.version_info >= (3, 10):
        print(f"[OK]     Python {py}")
    else:
        ok = False
        print(f"[ERRORE] Python {py}: serve la versione 3.10 o successiva")

    for nome, comando in (("Git", "git"), ("uv", "uv")):
        v = versione(comando)
        if v:
            print(f"[OK]     {nome}: {v}")
        else:
            ok = False
            print(f"[ERRORE] {nome} non trovato: installalo seguendo il README, poi riapri VS Code")

    print("\nTutto pronto, buon workshop!" if ok else "\nSistema gli errori e rilancia lo script.")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
