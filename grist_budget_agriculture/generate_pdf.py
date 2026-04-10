"""
Cette fonction a été expérimentée pour générer des documents PDF à partir de templates ODT
L'idée était de pouvoir générer automatiquement des PV de SF.

Note: Cela a nécessité l'intégration de Libre Office dans l'image Scalingo
cf git log .buildpacks

"""

from dotenv import load_dotenv
import os
import sys
import subprocess

load_dotenv()


def run_cmd(src_path, dst_pdf_path):
    return subprocess.run(
        [
            os.environ["LIBREOFFICE_EXEC"],
            "--headless",
            "--convert-to",
            "pdf",
            "--outdir",
            dst_pdf_path,
            src_path,
        ],
        check=True,
        capture_output=True,
    )


def main():
    run_cmd(os.path.abspath(sys.argv[-2]), os.path.abspath(sys.argv[-1]))


if __name__ == "__main__":
    main()
