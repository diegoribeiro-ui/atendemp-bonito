from __future__ import annotations

import json
import os
import shutil
import sys
import tempfile
import threading
import time
import traceback
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import messagebox, ttk

from PIL import ImageGrab
import pytesseract

from extractor import extract_information


APP_NAME = "Captura de Tela PJ"
BASE_DIR = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
OUTPUT_DIR = Path.home() / "Documents" / "Capturas PJ"


def find_tesseract() -> str | None:
    candidates = [
        shutil.which("tesseract"),
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
        str(BASE_DIR / "Tesseract-OCR" / "tesseract.exe"),
    ]
    for candidate in candidates:
        if candidate and Path(candidate).exists():
            pytesseract.pytesseract.tesseract_cmd = candidate
            return candidate
    return None


def rtf_escape(text: str) -> str:
    parts = []
    for char in text:
        code = ord(char)
        if char in "\\{}":
            parts.append("\\" + char)
        elif char == "\n":
            parts.append("\\par\n")
        elif code > 127:
            signed = code if code < 32768 else code - 65536
            parts.append(f"\\u{signed}?")
        else:
            parts.append(char)
    return "".join(parts)


def write_rtf(path: Path, text: str, data: dict) -> None:
    sections = [
        ("TEXTO EXTRAÍDO", text),
        ("PROCEDIMENTOS", "\n".join(data["procedimentos"])),
        ("OFÍCIOS", "\n".join(data["oficios"])),
        ("PARTES E QUALIFICAÇÕES", "\n".join(data["partes"])),
        ("DATAS", "\n".join(data["datas"])),
        ("PRAZOS", "\n".join(data["prazos"])),
        ("LEGISLAÇÃO", "\n".join(data["legislacao"])),
        ("RESUMO AUTOMÁTICO", data["resumo"]),
    ]
    body = [r"{\rtf1\ansi\deff0{\fonttbl{\f0 Segoe UI;}}\fs22"]
    body.append(r"\b Captura de Tela PJ\b0\par ")
    body.append(rtf_escape(f"Gerado em {datetime.now():%d/%m/%Y às %H:%M:%S}\n\n"))
    for title, content in sections:
        body.append(r"\b " + rtf_escape(title) + r"\b0\par ")
        body.append(rtf_escape(content or "Não identificado") + r"\par\par ")
    body.append("}")
    path.write_text("".join(body), encoding="ascii", errors="ignore")


class SimpleCapture(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("430x310")
        self.resizable(False, False)
        self.attributes("-topmost", True)
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        self.tesseract = find_tesseract()
        self.build_ui()

    def build_ui(self):
        frame = ttk.Frame(self, padding=24)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text=APP_NAME, font=("Segoe UI", 20, "bold")).pack(pady=(0, 5))
        ttk.Label(frame, text="Abra a tela desejada e clique no botão abaixo.", foreground="#5f6b7a").pack()
        self.button = tk.Button(
            frame,
            text="CAPTURAR TELA\nE CONVERTER",
            command=self.capture,
            bg="#245c9f",
            fg="white",
            activebackground="#173f72",
            activeforeground="white",
            font=("Segoe UI", 15, "bold"),
            relief="flat",
            cursor="hand2",
            height=3,
        )
        self.button.pack(fill="x", pady=22)
        self.status = ttk.Label(frame, text="", anchor="center", wraplength=370)
        self.status.pack(fill="x")
        ttk.Button(frame, text="Abrir pasta das capturas", command=self.open_folder).pack(pady=(12, 0))
        self.set_status("Pronto para capturar." if self.tesseract else "OCR não encontrado. Consulte LEIA-ME.txt.")

    def set_status(self, message: str):
        self.status.configure(text=message)
        self.update_idletasks()

    def capture(self):
        if not self.tesseract:
            messagebox.showerror(
                "OCR necessário",
                "O Tesseract OCR não foi localizado. Instale-o conforme o arquivo LEIA-ME.txt e abra novamente o programa.",
            )
            return
        self.button.configure(state="disabled")
        self.set_status("A captura ocorrerá em 2 segundos...")
        self.withdraw()
        threading.Thread(target=self._worker, daemon=True).start()

    def _worker(self):
        try:
            time.sleep(2)
            image = ImageGrab.grab(all_screens=True).convert("RGB")
            stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base = OUTPUT_DIR / f"Captura_PJ_{stamp}"
            png_path = base.with_suffix(".png")
            pdf_path = Path(f"{base}_pesquisavel.pdf")
            rtf_path = base.with_suffix(".rtf")
            json_path = Path(f"{base}_dados.json")
            image.save(png_path)
            try:
                text = pytesseract.image_to_string(image, lang="por")
                pdf = pytesseract.image_to_pdf_or_hocr(image, lang="por", extension="pdf")
            except pytesseract.TesseractError:
                text = pytesseract.image_to_string(image, lang="eng")
                pdf = pytesseract.image_to_pdf_or_hocr(image, lang="eng", extension="pdf")
            pdf_path.write_bytes(pdf)
            data = extract_information(text).to_dict()
            data.update(gerado_em=datetime.now().isoformat(), imagem=str(png_path), pdf=str(pdf_path))
            write_rtf(rtf_path, text, data)
            json_path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
            self.after(0, lambda: self._success(pdf_path, rtf_path))
        except Exception as exc:
            self.after(0, lambda: self._failure(exc))

    def _success(self, pdf_path: Path, rtf_path: Path):
        self.deiconify(); self.lift(); self.attributes("-topmost", True)
        self.button.configure(state="normal")
        self.set_status("Concluído: PDF pesquisável e RTF editável foram gerados.")
        messagebox.showinfo("Captura concluída", f"Arquivos criados:\n\n{pdf_path.name}\n{rtf_path.name}\n\nPasta: {OUTPUT_DIR}")

    def _failure(self, exc: Exception):
        self.deiconify(); self.lift(); self.button.configure(state="normal")
        self.set_status("Não foi possível concluir a captura.")
        messagebox.showerror("Erro", str(exc))

    def open_folder(self):
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        if os.name == "nt": os.startfile(OUTPUT_DIR)
        else: messagebox.showinfo("Pasta", str(OUTPUT_DIR))


def report_error(exc: BaseException):
    log = BASE_DIR / "erro_captura_tela.log"
    log.write_text("".join(traceback.format_exception(type(exc), exc, exc.__traceback__)), encoding="utf-8")


if __name__ == "__main__":
    try:
        SimpleCapture().mainloop()
    except BaseException as error:
        report_error(error)

