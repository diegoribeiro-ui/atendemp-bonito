from __future__ import annotations

import os
import sys
import tkinter as tk
import traceback
from datetime import datetime
from pathlib import Path
from tkinter import filedialog, messagebox, ttk

from database import Database


APP_TITLE = "AtendeMP Bonito"
BASE_DIR = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path(__file__).resolve().parent
DB_PATH = BASE_DIR / "dados" / "atendemp_bonito.db"


def labeled_entry(parent, label, row, col=0, width=28, colspan=1):
    ttk.Label(parent, text=label).grid(row=row, column=col, sticky="w", padx=6, pady=(6, 2))
    var = tk.StringVar()
    entry = ttk.Entry(parent, textvariable=var, width=width)
    entry.grid(row=row + 1, column=col, columnspan=colspan, sticky="ew", padx=6, pady=(0, 5))
    return var


class LoginDialog(tk.Toplevel):
    def __init__(self, parent, db: Database):
        super().__init__(parent)
        self.db = db
        self.ok = False
        self.title("Acesso seguro")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()
        frame = ttk.Frame(self, padding=24)
        frame.pack(fill="both", expand=True)
        first = not db.has_password()
        ttk.Label(frame, text=APP_TITLE, font=("Segoe UI", 18, "bold")).pack(pady=(0, 8))
        ttk.Label(frame, text="Crie a senha inicial" if first else "Informe sua senha").pack(pady=(0, 10))
        self.password = tk.StringVar()
        ttk.Entry(frame, textvariable=self.password, show="•", width=34).pack(pady=4)
        self.confirm = tk.StringVar()
        if first:
            ttk.Label(frame, text="Confirme a senha").pack(pady=(8, 0))
            ttk.Entry(frame, textvariable=self.confirm, show="•", width=34).pack(pady=4)
        ttk.Button(frame, text="Entrar" if not first else "Criar senha e entrar", command=self.submit).pack(pady=(16, 0))
        self.bind("<Return>", lambda _e: self.submit())
        self.protocol("WM_DELETE_WINDOW", self.cancel)
        self.after(100, lambda: self.focus_force())

    def submit(self):
        password = self.password.get()
        if not self.db.has_password():
            if password != self.confirm.get():
                messagebox.showerror("Senha", "As senhas não conferem.", parent=self)
                return
            try:
                self.db.set_password(password)
            except ValueError as exc:
                messagebox.showerror("Senha", str(exc), parent=self)
                return
        elif not self.db.verify_password(password):
            messagebox.showerror("Acesso negado", "Senha incorreta.", parent=self)
            return
        self.ok = True
        self.destroy()

    def cancel(self):
        self.destroy()


class PersonDialog(tk.Toplevel):
    FIELDS = [
        ("nome_completo", "Nome completo *"), ("nome_social", "Nome social"),
        ("cpf", "CPF"), ("rg", "RG"), ("orgao_expedidor", "Órgão expedidor"),
        ("data_nascimento", "Nascimento (AAAA-MM-DD)"), ("genero", "Gênero"),
        ("estado_civil", "Estado civil"), ("profissao", "Profissão"), ("escolaridade", "Escolaridade"),
        ("telefone", "Telefone"), ("telefone_alternativo", "Telefone alternativo"), ("email", "E-mail"),
        ("cep", "CEP"), ("endereco", "Endereço"), ("numero", "Número"), ("complemento", "Complemento"),
        ("bairro", "Bairro"), ("municipio", "Município"), ("uf", "UF"),
        ("representante_nome", "Representante/acompanhante"),
        ("representante_parentesco", "Vínculo/parentesco"), ("representante_contato", "Contato do representante"),
    ]

    def __init__(self, parent, db: Database, person_id=None):
        super().__init__(parent)
        self.db, self.person_id, self.saved = db, person_id, False
        self.title("Cadastro da pessoa atendida")
        self.geometry("940x760")
        self.transient(parent)
        self.grab_set()
        outer = ttk.Frame(self, padding=10)
        outer.pack(fill="both", expand=True)
        canvas = tk.Canvas(outer, highlightthickness=0)
        scroll = ttk.Scrollbar(outer, orient="vertical", command=canvas.yview)
        form = ttk.Frame(canvas)
        form.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=form, anchor="nw", width=890)
        canvas.configure(yscrollcommand=scroll.set)
        canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.vars = {}
        for i, (key, label) in enumerate(self.FIELDS):
            self.vars[key] = labeled_entry(form, label, (i // 3) * 2, i % 3)
        self.vars["municipio"].set("Bonito")
        self.vars["uf"].set("PA")
        base_row = ((len(self.FIELDS) + 2) // 3) * 2
        self.texts = {}
        for offset, (key, label, height) in enumerate([
            ("acessibilidade", "Necessidades de acessibilidade", 3),
            ("vulnerabilidades", "Vulnerabilidades identificadas", 3),
            ("resumo_caso", "Resumo do caso *", 6),
            ("observacoes", "Observações", 4),
        ]):
            row = base_row + offset * 2
            ttk.Label(form, text=label).grid(row=row, column=0, columnspan=3, sticky="w", padx=6, pady=(8, 2))
            widget = tk.Text(form, height=height, wrap="word")
            widget.grid(row=row + 1, column=0, columnspan=3, sticky="ew", padx=6)
            self.texts[key] = widget
        self.active = tk.BooleanVar(value=True)
        ttk.Checkbutton(form, text="Cadastro ativo", variable=self.active).grid(row=base_row + 8, column=0, sticky="w", padx=6, pady=10)
        ttk.Button(form, text="Salvar cadastro", command=self.save).grid(row=base_row + 9, column=2, sticky="e", padx=6, pady=12)
        for col in range(3): form.columnconfigure(col, weight=1)
        if person_id:
            self.load()

    def load(self):
        row = self.db.get_person(self.person_id)
        if not row: return
        for key in self.vars: self.vars[key].set(row[key] or "")
        for key, widget in self.texts.items(): widget.insert("1.0", row[key] or "")
        self.active.set(bool(row["ativo"]))

    def save(self):
        data = {key: var.get().strip() for key, var in self.vars.items()}
        data.update({key: widget.get("1.0", "end").strip() for key, widget in self.texts.items()})
        data["ativo"] = self.active.get()
        try:
            self.person_id = self.db.save_person(data, self.person_id)
        except (ValueError, Exception) as exc:
            messagebox.showerror("Não foi possível salvar", str(exc), parent=self)
            return
        self.saved = True
        messagebox.showinfo("Cadastro", "Dados salvos com sucesso.", parent=self)
        self.destroy()


class AppointmentDialog(tk.Toplevel):
    def __init__(self, parent, db: Database, person_id=None):
        super().__init__(parent)
        self.db, self.saved = db, False
        self.title("Novo atendimento")
        self.geometry("900x760")
        self.transient(parent)
        self.grab_set()
        form = ttk.Frame(self, padding=16)
        form.pack(fill="both", expand=True)
        people = db.list_people()
        self.people_map = {f"{r['nome_completo']} — CPF {r['cpf'] or 'não informado'}": r["id"] for r in people}
        ttk.Label(form, text="Pessoa atendida *").grid(row=0, column=0, sticky="w", padx=5)
        self.person = tk.StringVar()
        combo = ttk.Combobox(form, textvariable=self.person, values=list(self.people_map), state="readonly")
        combo.grid(row=1, column=0, columnspan=2, sticky="ew", padx=5, pady=(2, 8))
        if person_id:
            for name, pid in self.people_map.items():
                if pid == person_id: self.person.set(name); break
        self.vars = {
            "protocolo": labeled_entry(form, "Protocolo", 2, 0),
            "data_atendimento": labeled_entry(form, "Data e hora * (AAAA-MM-DD HH:MM)", 2, 1),
            "canal": labeled_entry(form, "Canal *", 4, 0),
            "area": labeled_entry(form, "Área *", 4, 1),
            "assunto": labeled_entry(form, "Assunto *", 6, 0, colspan=2),
            "retorno_em": labeled_entry(form, "Retorno (AAAA-MM-DD)", 8, 0),
        }
        self.vars["protocolo"].set(db.next_protocol())
        self.vars["data_atendimento"].set(datetime.now().strftime("%Y-%m-%d %H:%M"))
        self.vars["canal"].set("Presencial")
        self.vars["area"].set("Atendimento ao público")
        ttk.Label(form, text="Prioridade").grid(row=8, column=1, sticky="w", padx=5)
        self.priority = tk.StringVar(value="Normal")
        ttk.Combobox(form, textvariable=self.priority, values=["Baixa", "Normal", "Alta", "Urgente"], state="readonly").grid(row=9, column=1, sticky="ew", padx=5)
        self.texts = {}
        for index, (key, label) in enumerate([
            ("relato", "Relato/demanda apresentada *"), ("providencias", "Providências adotadas"),
            ("encaminhamentos", "Encaminhamentos"), ("resultado", "Resultado/observações"),
        ]):
            row = 10 + index * 2
            ttk.Label(form, text=label).grid(row=row, column=0, columnspan=2, sticky="w", padx=5, pady=(7, 2))
            text = tk.Text(form, height=4, wrap="word")
            text.grid(row=row + 1, column=0, columnspan=2, sticky="nsew", padx=5)
            self.texts[key] = text
        self.status = tk.StringVar(value="Em acompanhamento")
        ttk.Label(form, text="Status").grid(row=18, column=0, sticky="w", padx=5, pady=(8, 2))
        ttk.Combobox(form, textvariable=self.status, values=["Em acompanhamento", "Aguardando retorno", "Concluído", "Arquivado"], state="readonly").grid(row=19, column=0, sticky="ew", padx=5)
        self.reminder = tk.StringVar(value="0")
        ttk.Label(form, text="Avisar com antecedência (dias)").grid(row=18, column=1, sticky="w", padx=5, pady=(8, 2))
        ttk.Spinbox(form, from_=0, to=30, textvariable=self.reminder).grid(row=19, column=1, sticky="ew", padx=5)
        self.confidential = tk.BooleanVar()
        ttk.Checkbutton(form, text="Atendimento sigiloso", variable=self.confidential).grid(row=20, column=0, sticky="w", padx=5, pady=10)
        ttk.Button(form, text="Salvar atendimento", command=self.save).grid(row=20, column=1, sticky="e", padx=5, pady=10)
        form.columnconfigure(0, weight=1); form.columnconfigure(1, weight=1)

    def save(self):
        if self.person.get() not in self.people_map:
            messagebox.showerror("Pessoa", "Selecione a pessoa atendida.", parent=self); return
        data = {key: var.get().strip() for key, var in self.vars.items()}
        data.update({key: widget.get("1.0", "end").strip() for key, widget in self.texts.items()})
        data.update(pessoa_id=self.people_map[self.person.get()], prioridade=self.priority.get(),
                    sigiloso=self.confidential.get(), status=self.status.get(),
                    lembrete_antecedencia=self.reminder.get(), concluido_em="")
        try:
            self.db.save_appointment(data)
        except Exception as exc:
            messagebox.showerror("Não foi possível salvar", str(exc), parent=self); return
        self.saved = True
        messagebox.showinfo("Atendimento", "Atendimento registrado com sucesso.", parent=self)
        self.destroy()


class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.withdraw()
        self.db = Database(DB_PATH)
        login = LoginDialog(self, self.db)
        self.wait_window(login)
        if not login.ok:
            self.db.close(); self.destroy(); return
        self.deiconify()
        self.title(APP_TITLE)
        self.geometry("1180x760")
        self.minsize(980, 640)
        self.protocol("WM_DELETE_WINDOW", self.close)
        self.style = ttk.Style(self)
        if "vista" in self.style.theme_names(): self.style.theme_use("vista")
        self.build_ui()
        self.refresh_all()
        self.after(500, self.show_due_reminders)

    def build_ui(self):
        header = ttk.Frame(self, padding=(16, 12))
        header.pack(fill="x")
        ttk.Label(header, text=APP_TITLE, font=("Segoe UI", 20, "bold")).pack(side="left")
        ttk.Label(header, text="Promotoria de Justiça de Bonito/PA").pack(side="left", padx=14)
        ttk.Button(header, text="Fazer backup", command=self.backup).pack(side="right")
        self.tabs = ttk.Notebook(self)
        self.tabs.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.dashboard_tab = ttk.Frame(self.tabs, padding=18)
        self.people_tab = ttk.Frame(self.tabs, padding=12)
        self.appointments_tab = ttk.Frame(self.tabs, padding=12)
        self.reminders_tab = ttk.Frame(self.tabs, padding=12)
        self.tabs.add(self.dashboard_tab, text="Painel")
        self.tabs.add(self.people_tab, text="Pessoas")
        self.tabs.add(self.appointments_tab, text="Atendimentos")
        self.tabs.add(self.reminders_tab, text="Agenda e lembretes")
        self.build_dashboard(); self.build_people(); self.build_appointments(); self.build_reminders()

    def build_dashboard(self):
        self.cards = {}
        for i, (key, label) in enumerate([("pessoas", "Pessoas ativas"), ("atendimentos", "Atendimentos"), ("abertos", "Em acompanhamento"), ("lembretes", "Lembretes pendentes")]):
            frame = ttk.LabelFrame(self.dashboard_tab, text=label, padding=18)
            frame.grid(row=0, column=i, sticky="nsew", padx=6, pady=6)
            value = ttk.Label(frame, text="0", font=("Segoe UI", 28, "bold"))
            value.pack(); self.cards[key] = value
            self.dashboard_tab.columnconfigure(i, weight=1)
        ttk.Label(self.dashboard_tab, text="Ações rápidas", font=("Segoe UI", 14, "bold")).grid(row=1, column=0, columnspan=4, sticky="w", pady=(28, 8))
        ttk.Button(self.dashboard_tab, text="Cadastrar pessoa", command=self.new_person).grid(row=2, column=0, sticky="ew", padx=6)
        ttk.Button(self.dashboard_tab, text="Registrar atendimento", command=self.new_appointment).grid(row=2, column=1, sticky="ew", padx=6)
        ttk.Button(self.dashboard_tab, text="Ver lembretes", command=lambda: self.tabs.select(self.reminders_tab)).grid(row=2, column=2, sticky="ew", padx=6)

    def build_people(self):
        tools = ttk.Frame(self.people_tab); tools.pack(fill="x", pady=(0, 8))
        self.people_query = tk.StringVar()
        ttk.Entry(tools, textvariable=self.people_query, width=50).pack(side="left")
        ttk.Button(tools, text="Pesquisar", command=self.refresh_people).pack(side="left", padx=5)
        ttk.Button(tools, text="Novo cadastro", command=self.new_person).pack(side="right")
        columns = ("nome", "cpf", "telefone", "municipio", "resumo", "situacao")
        self.people_tree = ttk.Treeview(self.people_tab, columns=columns, show="headings")
        headings = ["Nome", "CPF", "Telefone", "Município", "Resumo do caso", "Situação"]
        widths = [220, 120, 120, 120, 360, 80]
        for c, h, w in zip(columns, headings, widths): self.people_tree.heading(c, text=h); self.people_tree.column(c, width=w)
        self.people_tree.pack(fill="both", expand=True)
        self.people_tree.bind("<Double-1>", lambda _e: self.edit_person())
        buttons = ttk.Frame(self.people_tab); buttons.pack(fill="x", pady=8)
        ttk.Button(buttons, text="Editar cadastro", command=self.edit_person).pack(side="left")
        ttk.Button(buttons, text="Novo atendimento para a pessoa", command=self.appointment_for_selected).pack(side="left", padx=6)

    def build_appointments(self):
        tools = ttk.Frame(self.appointments_tab); tools.pack(fill="x", pady=(0, 8))
        self.appointment_query = tk.StringVar()
        ttk.Entry(tools, textvariable=self.appointment_query, width=50).pack(side="left")
        ttk.Button(tools, text="Pesquisar", command=self.refresh_appointments).pack(side="left", padx=5)
        ttk.Button(tools, text="Novo atendimento", command=self.new_appointment).pack(side="right")
        columns = ("protocolo", "data", "pessoa", "area", "assunto", "prioridade", "status", "retorno")
        self.appointment_tree = ttk.Treeview(self.appointments_tab, columns=columns, show="headings")
        for c, h, w in zip(columns, ["Protocolo", "Data", "Pessoa", "Área", "Assunto", "Prioridade", "Status", "Retorno"], [130, 130, 190, 140, 220, 80, 130, 100]):
            self.appointment_tree.heading(c, text=h); self.appointment_tree.column(c, width=w)
        self.appointment_tree.pack(fill="both", expand=True)

    def build_reminders(self):
        ttk.Label(self.reminders_tab, text="Retornos vencidos ou próximos", font=("Segoe UI", 14, "bold")).pack(anchor="w", pady=(0, 8))
        columns = ("retorno", "pessoa", "protocolo", "assunto", "prioridade")
        self.reminder_tree = ttk.Treeview(self.reminders_tab, columns=columns, show="headings")
        for c, h, w in zip(columns, ["Data do retorno", "Pessoa", "Protocolo", "Assunto", "Prioridade"], [120, 240, 140, 370, 90]):
            self.reminder_tree.heading(c, text=h); self.reminder_tree.column(c, width=w)
        self.reminder_tree.pack(fill="both", expand=True)
        ttk.Button(self.reminders_tab, text="Atualizar lembretes", command=self.refresh_reminders).pack(anchor="e", pady=8)

    def selected_person_id(self):
        selected = self.people_tree.selection()
        return int(selected[0]) if selected else None

    def new_person(self):
        dialog = PersonDialog(self, self.db); self.wait_window(dialog)
        if dialog.saved: self.refresh_all()

    def edit_person(self):
        pid = self.selected_person_id()
        if not pid: messagebox.showwarning("Seleção", "Selecione uma pessoa."); return
        dialog = PersonDialog(self, self.db, pid); self.wait_window(dialog)
        if dialog.saved: self.refresh_all()

    def appointment_for_selected(self):
        pid = self.selected_person_id()
        if not pid: messagebox.showwarning("Seleção", "Selecione uma pessoa."); return
        self.new_appointment(pid)

    def new_appointment(self, person_id=None):
        if not self.db.list_people():
            messagebox.showwarning("Cadastro necessário", "Cadastre uma pessoa antes do atendimento."); return
        dialog = AppointmentDialog(self, self.db, person_id); self.wait_window(dialog)
        if dialog.saved: self.refresh_all()

    def refresh_all(self):
        self.refresh_dashboard(); self.refresh_people(); self.refresh_appointments(); self.refresh_reminders()

    def refresh_dashboard(self):
        for key, value in self.db.dashboard().items(): self.cards[key].configure(text=str(value))

    def refresh_people(self):
        self.people_tree.delete(*self.people_tree.get_children())
        for row in self.db.list_people(self.people_query.get()):
            summary = (row["resumo_caso"] or "").replace("\n", " ")
            self.people_tree.insert("", "end", iid=str(row["id"]), values=(row["nome_completo"], row["cpf"], row["telefone"], row["municipio"], summary[:90], "Ativo" if row["ativo"] else "Inativo"))

    def refresh_appointments(self):
        self.appointment_tree.delete(*self.appointment_tree.get_children())
        for row in self.db.list_appointments(self.appointment_query.get()):
            self.appointment_tree.insert("", "end", iid=str(row["id"]), values=(row["protocolo"], row["data_atendimento"], row["nome_completo"], row["area"], row["assunto"], row["prioridade"], row["status"], row["retorno_em"]))

    def refresh_reminders(self):
        self.reminder_tree.delete(*self.reminder_tree.get_children())
        for row in self.db.due_reminders():
            self.reminder_tree.insert("", "end", iid=str(row["id"]), values=(row["retorno_em"], row["nome_completo"], row["protocolo"], row["assunto"], row["prioridade"]))

    def show_due_reminders(self):
        reminders = self.db.due_reminders()
        if reminders:
            messagebox.showinfo("Lembretes", f"Há {len(reminders)} retorno(s) vencido(s) ou próximo(s). Consulte a aba Agenda e lembretes.")

    def backup(self):
        folder = filedialog.askdirectory(title="Escolha a pasta segura para o backup")
        if folder:
            try: path = self.db.backup(folder)
            except Exception as exc: messagebox.showerror("Backup", str(exc)); return
            messagebox.showinfo("Backup concluído", f"Backup salvo em:\n{path}")

    def close(self):
        self.db.close(); self.destroy()


def report_startup_error(exc: BaseException) -> None:
    """Registra falhas de inicialização mesmo na versão sem console."""
    log_path = BASE_DIR / "erro_atendemp.log"
    details = "".join(traceback.format_exception(type(exc), exc, exc.__traceback__))
    try:
        log_path.write_text(
            f"AtendeMP Bonito - erro em {datetime.now():%Y-%m-%d %H:%M:%S}\n\n{details}",
            encoding="utf-8",
        )
    except OSError:
        pass
    try:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror(
            "AtendeMP Bonito - erro ao iniciar",
            f"O programa não conseguiu iniciar.\n\n{exc}\n\n"
            f"Detalhes foram registrados em:\n{log_path}",
            parent=root,
        )
        root.destroy()
    except Exception:
        pass
    print(details, file=sys.stderr)


if __name__ == "__main__":
    try:
        app = MainApp()
        try:
            exists = bool(app.winfo_exists())
        except tk.TclError:
            exists = False
        if exists:
            app.mainloop()
    except BaseException as error:
        report_startup_error(error)
