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
