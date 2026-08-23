from __future__ import annotations

import ctypes
from ctypes import wintypes
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
from tkinter import filedialog, messagebox, ttk

from PIL import Image, ImageGrab
from pypdf import PdfReader, PdfWriter
import pytesseract

from extractor import extract_information


APP_NAME = "Captura Inteligente PJ"
BASE_DIR = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
DEFAULT_OUTPUT = Path.home() / "Documents" / "Captura Inteligente PJ"


def configure_tesseract() -> str | None:
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


def active_window_bbox() -> tuple[int, int, int, int] | None:
    if os.name != "nt":
        return None
    hwnd = ctypes.windll.user32.GetForegroundWindow()
    rect = wintypes.RECT()
    if hwnd and ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        return rect.left, rect.top, rect.right, rect.bottom
    return None


class CaptureApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(APP_NAME)
        self.geometry("1180x780")
        self.minsize(980, 650)
        self.images: list[Image.Image] = []
        self.image_names: list[str] = []
        self.ocr_text = ""
        self.output_dir = DEFAULT_OUTPUT
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.tesseract = configure_tesseract()
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.build_ui()
        self.set_status("Pronto. OCR em português disponível." if self.tesseract else "Captura disponível. Instale o Tesseract para habilitar o OCR.")

    def build_ui(self):
        style = ttk.Style(self)
        if "vista" in style.theme_names():
            style.theme_use("vista")
        header = ttk.Frame(self, padding=(18, 14))
        header.pack(fill="x")
        ttk.Label(header, text=APP_NAME, font=("Segoe UI", 20, "bold")).pack(side="left")
        ttk.Label(header, text="Captura, OCR e dados estruturados", foreground="#5f6b7a").pack(side="left", padx=14)
        ttk.Button(header, text="Abrir pasta de resultados", command=self.open_output).pack(side="right")
        body = ttk.Panedwindow(self, orient="horizontal")
        body.pack(fill="both", expand=True, padx=14, pady=(0, 10))
        left = ttk.Frame(body, padding=10)
        right = ttk.Frame(body, padding=10)
        body.add(left, weight=1)
        body.add(right, weight=2)
        self.build_capture_panel(left)
        self.build_result_panel(right)
        self.status = ttk.Label(self, text="", relief="sunken", anchor="w", padding=6)
        self.status.pack(fill="x", side="bottom")

    def build_capture_panel(self, parent):
        ttk.Label(parent, text="1. Capturar conteúdo", font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(0, 10))
        ttk.Button(parent, text="Capturar tela visível", command=self.capture_screen).pack(fill="x", pady=4)
        ttk.Button(parent, text="Capturar janela ativa", command=self.capture_active_window).pack(fill="x", pady=4)
        roll = ttk.LabelFrame(parent, text="Captura assistida com rolagem", padding=10)
        roll.pack(fill="x", pady=10)
        ttk.Label(roll, text="Quantidade de telas:").grid(row=0, column=0, sticky="w")
        self.roll_count = tk.IntVar(value=5)
        ttk.Spinbox(roll, from_=2, to=30, textvariable=self.roll_count, width=8).grid(row=0, column=1, padx=6)
        ttk.Label(roll, text="Intervalo (segundos):").grid(row=1, column=0, sticky="w", pady=6)
        self.roll_interval = tk.DoubleVar(value=2.5)
        ttk.Spinbox(roll, from_=1.0, to=10.0, increment=.5, textvariable=self.roll_interval, width=8).grid(row=1, column=1, padx=6)
        ttk.Button(roll, text="Iniciar captura e rolar manualmente", command=self.capture_scroll).grid(row=2, column=0, columnspan=2, sticky="ew")
        ttk.Button(parent, text="Importar imagens", command=self.import_images).pack(fill="x", pady=4)
        ttk.Separator(parent).pack(fill="x", pady=12)
        ttk.Label(parent, text="Capturas desta sessão", font=("Segoe UI", 11, "bold")).pack(anchor="w")
        self.capture_list = tk.Listbox(parent, height=12)
        self.capture_list.pack(fill="both", expand=True, pady=6)
        ttk.Button(parent, text="Remover selecionada", command=self.remove_selected).pack(fill="x")
        ttk.Button(parent, text="Limpar todas", command=self.clear_all).pack(fill="x", pady=4)
        ttk.Separator(parent).pack(fill="x", pady=12)
        self.process_btn = ttk.Button(parent, text="2. Executar OCR e analisar", command=self.process_ocr)
        self.process_btn.pack(fill="x", ipady=5)

    def build_result_panel(self, parent):
        notebook = ttk.Notebook(parent)
        notebook.pack(fill="both", expand=True)
        text_tab = ttk.Frame(notebook, padding=8)
        data_tab = ttk.Frame(notebook, padding=8)
        notebook.add(text_tab, text="Texto extraído")
        notebook.add(data_tab, text="Informações identificadas")
        self.text_output = tk.Text(text_tab, wrap="word", font=("Consolas", 10))
        self.text_output.pack(fill="both", expand=True)
        fields = [
            ("procedimentos", "Procedimentos"), ("oficios", "Ofícios"), ("partes", "Partes e qualificações"),
            ("cpfs", "CPFs"), ("datas", "Datas"), ("prazos", "Prazos"),
            ("legislacao", "Legislação citada"), ("resumo", "Resumo automático"),
        ]
        self.data_widgets = {}
        for row, (key, label) in enumerate(fields):
            ttk.Label(data_tab, text=label).grid(row=row * 2, column=0, sticky="w", pady=(7, 2))
            widget = tk.Text(data_tab, height=3 if key != "resumo" else 6, wrap="word")
            widget.grid(row=row * 2 + 1, column=0, sticky="nsew")
            self.data_widgets[key] = widget
            data_tab.rowconfigure(row * 2 + 1, weight=2 if key == "resumo" else 1)
        data_tab.columnconfigure(0, weight=1)
        actions = ttk.Frame(parent)
        actions.pack(fill="x", pady=(8, 0))
        ttk.Button(actions, text="Salvar PNGs", command=self.save_pngs).pack(side="left")
        ttk.Button(actions, text="Gerar PDF", command=self.save_image_pdf).pack(side="left", padx=5)
        ttk.Button(actions, text="Gerar PDF pesquisável", command=self.save_searchable_pdf).pack(side="left", padx=5)
        ttk.Button(actions, text="Salvar texto e dados", command=self.save_data).pack(side="right")

    def set_status(self, message: str):
        self.status.configure(text=message)
        self.update_idletasks()

    def add_image(self, image: Image.Image, name: str | None = None):
        image = image.convert("RGB")
        self.images.append(image)
        label = name or f"Captura {len(self.images)} - {datetime.now():%H:%M:%S}"
        self.image_names.append(label)
        self.capture_list.insert("end", label)
        self.set_status(f"{len(self.images)} captura(s) adicionada(s).")

    def capture_screen(self):
        self.iconify()
        self.after(800, self._capture_screen_after_hide)

    def _capture_screen_after_hide(self):
        try:
            self.add_image(ImageGrab.grab(all_screens=True), "Tela completa")
        except Exception as exc:
            messagebox.showerror("Captura", str(exc))
        self.deiconify()

    def capture_active_window(self):
        messagebox.showinfo("Janela ativa", "Após confirmar, clique na janela desejada. A captura será feita em 3 segundos.")
        self.withdraw()
        threading.Thread(target=self._delayed_active_capture, daemon=True).start()

    def _delayed_active_capture(self):
        time.sleep(3)
        try:
            bbox = active_window_bbox()
            image = ImageGrab.grab(bbox=bbox, all_screens=True) if bbox else ImageGrab.grab(all_screens=True)
            self.after(0, lambda: self.add_image(image, "Janela ativa"))
        except Exception as exc:
            self.after(0, lambda: messagebox.showerror("Captura", str(exc)))
        finally:
            self.after(0, self.deiconify)

    def capture_scroll(self):
        count = max(2, min(30, int(self.roll_count.get())))
        interval = max(1.0, float(self.roll_interval.get()))
        messagebox.showinfo("Captura com rolagem", f"Clique na janela desejada. Em 3 segundos começarão {count} capturas. Role a tela entre cada captura.")
        self.withdraw()
        threading.Thread(target=self._scroll_worker, args=(count, interval), daemon=True).start()

    def _scroll_worker(self, count: int, interval: float):
        time.sleep(3)
        try:
            bbox = active_window_bbox()
            batch = []
            for index in range(count):
                batch.append(ImageGrab.grab(bbox=bbox, all_screens=True) if bbox else ImageGrab.grab(all_screens=True))
                time.sleep(interval)
            for index, image in enumerate(batch, 1):
                self.after(0, lambda img=image, i=index: self.add_image(img, f"Rolagem {i}/{count}"))
        except Exception as exc:
            self.after(0, lambda: messagebox.showerror("Captura", str(exc)))
        finally:
            self.after(0, self.deiconify)

    def import_images(self):
        paths = filedialog.askopenfilenames(filetypes=[("Imagens", "*.png *.jpg *.jpeg *.bmp *.tif *.tiff"), ("Todos", "*.*")])
        for path in paths:
            try:
                self.add_image(Image.open(path), Path(path).name)
            except Exception as exc:
                messagebox.showwarning("Importação", f"Não foi possível abrir {path}: {exc}")

    def remove_selected(self):
        selection = self.capture_list.curselection()
        if not selection:
            return
        index = selection[0]
        self.capture_list.delete(index)
        self.images.pop(index)
        self.image_names.pop(index)

    def clear_all(self):
        self.images.clear(); self.image_names.clear(); self.capture_list.delete(0, "end")
        self.text_output.delete("1.0", "end")
        for widget in self.data_widgets.values(): widget.delete("1.0", "end")

    def process_ocr(self):
        if not self.images:
            messagebox.showwarning("OCR", "Faça ou importe ao menos uma captura.")
            return
        if not self.tesseract:
            messagebox.showerror("OCR indisponível", "O Tesseract OCR não foi localizado. Consulte o arquivo LEIA-ME.txt para instalar.")
            return
        self.process_btn.configure(state="disabled")
        self.set_status("Executando OCR local. Aguarde...")
        threading.Thread(target=self._ocr_worker, daemon=True).start()

    def _ocr_worker(self):
        texts = []
        try:
            for index, image in enumerate(self.images, 1):
                self.after(0, lambda i=index: self.set_status(f"OCR da captura {i}/{len(self.images)}..."))
                try:
                    text = pytesseract.image_to_string(image, lang="por")
                except pytesseract.TesseractError:
                    text = pytesseract.image_to_string(image, lang="eng")
                texts.append(f"\n===== {self.image_names[index-1]} =====\n{text.strip()}")
            self.ocr_text = "\n".join(texts).strip()
            info = extract_information(self.ocr_text).to_dict()
            self.after(0, lambda: self.show_results(info))
        except Exception as exc:
            self.after(0, lambda: messagebox.showerror("OCR", str(exc)))
        finally:
            self.after(0, lambda: self.process_btn.configure(state="normal"))

    def show_results(self, info: dict):
        self.text_output.delete("1.0", "end"); self.text_output.insert("1.0", self.ocr_text)
        for key, widget in self.data_widgets.items():
            widget.delete("1.0", "end")
            value = info.get(key, "")
            widget.insert("1.0", "\n".join(value) if isinstance(value, list) else value)
        self.set_status("OCR concluído. Revise as informações antes de salvar.")

    def choose_prefix(self) -> Path | None:
        folder = filedialog.askdirectory(initialdir=self.output_dir, title="Escolha a pasta de destino")
        if not folder: return None
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return Path(folder) / f"Captura_PJ_{timestamp}"

    def save_pngs(self):
        if not self.images: return
        prefix = self.choose_prefix()
        if not prefix: return
        for index, image in enumerate(self.images, 1): image.save(f"{prefix}_{index:02d}.png")
        messagebox.showinfo("Imagens", f"{len(self.images)} imagem(ns) salva(s).")

    def save_image_pdf(self):
        if not self.images: return
        prefix = self.choose_prefix()
        if not prefix: return
        self.images[0].save(f"{prefix}.pdf", save_all=True, append_images=self.images[1:], resolution=150)
        messagebox.showinfo("PDF", f"PDF salvo em:\n{prefix}.pdf")

    def save_searchable_pdf(self):
        if not self.images: return
        if not self.tesseract:
            messagebox.showerror("PDF pesquisável", "Instale o Tesseract OCR primeiro."); return
        prefix = self.choose_prefix()
        if not prefix: return
        self.set_status("Gerando PDF pesquisável...")
        threading.Thread(target=self._searchable_pdf_worker, args=(prefix,), daemon=True).start()

    def _searchable_pdf_worker(self, prefix: Path):
        writer = PdfWriter()
        temp_paths = []
        try:
            for image in self.images:
                try: raw = pytesseract.image_to_pdf_or_hocr(image, lang="por", extension="pdf")
                except pytesseract.TesseractError: raw = pytesseract.image_to_pdf_or_hocr(image, lang="eng", extension="pdf")
                handle, temp_name = tempfile.mkstemp(suffix=".pdf")
                os.close(handle); Path(temp_name).write_bytes(raw); temp_paths.append(temp_name)
                for page in PdfReader(temp_name).pages: writer.add_page(page)
            output = Path(f"{prefix}_pesquisavel.pdf")
            with output.open("wb") as stream: writer.write(stream)
            self.after(0, lambda: messagebox.showinfo("PDF pesquisável", f"Arquivo salvo em:\n{output}"))
        except Exception as exc:
            self.after(0, lambda: messagebox.showerror("PDF pesquisável", str(exc)))
        finally:
            for path in temp_paths:
                try: Path(path).unlink()
                except OSError: pass
            self.after(0, lambda: self.set_status("Pronto."))

    def save_data(self):
        if not self.ocr_text:
            messagebox.showwarning("Dados", "Execute o OCR antes de salvar."); return
        prefix = self.choose_prefix()
        if not prefix: return
        Path(f"{prefix}.txt").write_text(self.text_output.get("1.0", "end").strip(), encoding="utf-8")
        data = {key: widget.get("1.0", "end").strip() for key, widget in self.data_widgets.items()}
        data.update(criado_em=datetime.now().isoformat(), capturas=self.image_names)
        Path(f"{prefix}_dados.json").write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        messagebox.showinfo("Dados", f"Texto e ficha estruturada salvos com o prefixo:\n{prefix}")

    def open_output(self):
        self.output_dir.mkdir(parents=True, exist_ok=True)
        if os.name == "nt": os.startfile(self.output_dir)
        else: messagebox.showinfo("Pasta", str(self.output_dir))


def report_error(exc: BaseException):
    log = BASE_DIR / "erro_captura_inteligente.log"
    log.write_text("".join(traceback.format_exception(type(exc), exc, exc.__traceback__)), encoding="utf-8")
    try:
        root = tk.Tk(); root.withdraw(); messagebox.showerror(APP_NAME, f"Erro ao iniciar: {exc}\n\nDetalhes: {log}"); root.destroy()
    except Exception: pass


if __name__ == "__main__":
    try:
        CaptureApp().mainloop()
    except BaseException as error:
        report_error(error)
