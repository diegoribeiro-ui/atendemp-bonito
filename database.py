from __future__ import annotations

import hashlib
import hmac
import os
import secrets
import shutil
import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any


SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS configuracao (
    chave TEXT PRIMARY KEY,
    valor TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS pessoas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome_completo TEXT NOT NULL,
    nome_social TEXT,
    cpf TEXT,
    rg TEXT,
    orgao_expedidor TEXT,
    data_nascimento TEXT,
    genero TEXT,
    estado_civil TEXT,
    profissao TEXT,
    escolaridade TEXT,
    telefone TEXT,
    telefone_alternativo TEXT,
    email TEXT,
    cep TEXT,
    endereco TEXT,
    numero TEXT,
    complemento TEXT,
    bairro TEXT,
    municipio TEXT DEFAULT 'Bonito',
    uf TEXT DEFAULT 'PA',
    representante_nome TEXT,
    representante_parentesco TEXT,
    representante_contato TEXT,
    acessibilidade TEXT,
    vulnerabilidades TEXT,
    resumo_caso TEXT NOT NULL,
    observacoes TEXT,
    ativo INTEGER NOT NULL DEFAULT 1,
    criado_em TEXT NOT NULL,
    atualizado_em TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_pessoas_nome ON pessoas(nome_completo);
CREATE INDEX IF NOT EXISTS idx_pessoas_cpf ON pessoas(cpf);
CREATE TABLE IF NOT EXISTS atendimentos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    pessoa_id INTEGER NOT NULL REFERENCES pessoas(id) ON DELETE RESTRICT,
    protocolo TEXT NOT NULL UNIQUE,
    data_atendimento TEXT NOT NULL,
    canal TEXT NOT NULL,
    area TEXT NOT NULL,
    assunto TEXT NOT NULL,
    relato TEXT NOT NULL,
    providencias TEXT,
    encaminhamentos TEXT,
    resultado TEXT,
    prioridade TEXT NOT NULL DEFAULT 'Normal',
    sigiloso INTEGER NOT NULL DEFAULT 0,
    status TEXT NOT NULL DEFAULT 'Em acompanhamento',
    retorno_em TEXT,
    lembrete_antecedencia INTEGER NOT NULL DEFAULT 0,
    concluido_em TEXT,
    criado_em TEXT NOT NULL,
    atualizado_em TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_atendimentos_pessoa ON atendimentos(pessoa_id);
CREATE INDEX IF NOT EXISTS idx_atendimentos_retorno ON atendimentos(retorno_em, status);
CREATE TABLE IF NOT EXISTS auditoria (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data_hora TEXT NOT NULL,
    acao TEXT NOT NULL,
    entidade TEXT NOT NULL,
    entidade_id INTEGER,
    detalhes TEXT
);
"""


class Database:
    def __init__(self, path: str | Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(self.path)
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.conn.execute("PRAGMA journal_mode = WAL")
        self.conn.executescript(SCHEMA)
        self.conn.commit()

    def close(self) -> None:
        self.conn.close()

    def has_password(self) -> bool:
        return self.get_config("password_hash") is not None

    def set_password(self, password: str) -> None:
        if len(password) < 8:
            raise ValueError("A senha deve ter pelo menos 8 caracteres.")
        salt = secrets.token_bytes(16)
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 310_000)
        self.set_config("password_salt", salt.hex())
        self.set_config("password_hash", digest.hex())
        self.audit("ALTERAR_SENHA", "configuracao", None, "Senha local definida/alterada")

    def verify_password(self, password: str) -> bool:
        salt_hex = self.get_config("password_salt")
        expected_hex = self.get_config("password_hash")
        if not salt_hex or not expected_hex:
            return False
        digest = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt_hex), 310_000)
        return hmac.compare_digest(digest.hex(), expected_hex)

    def get_config(self, key: str) -> str | None:
        row = self.conn.execute("SELECT valor FROM configuracao WHERE chave = ?", (key,)).fetchone()
        return row["valor"] if row else None

    def set_config(self, key: str, value: str) -> None:
        self.conn.execute(
            "INSERT INTO configuracao(chave, valor) VALUES(?, ?) ON CONFLICT(chave) DO UPDATE SET valor=excluded.valor",
            (key, value),
        )
        self.conn.commit()

    @staticmethod
    def now() -> str:
        return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def audit(self, action: str, entity: str, entity_id: int | None, details: str = "") -> None:
        self.conn.execute(
            "INSERT INTO auditoria(data_hora, acao, entidade, entidade_id, detalhes) VALUES(?,?,?,?,?)",
            (self.now(), action, entity, entity_id, details),
        )
        self.conn.commit()

    def save_person(self, data: dict[str, Any], person_id: int | None = None) -> int:
        now = self.now()
        allowed = [
            "nome_completo", "nome_social", "cpf", "rg", "orgao_expedidor", "data_nascimento",
            "genero", "estado_civil", "profissao", "escolaridade", "telefone", "telefone_alternativo",
            "email", "cep", "endereco", "numero", "complemento", "bairro", "municipio", "uf",
            "representante_nome", "representante_parentesco", "representante_contato", "acessibilidade",
            "vulnerabilidades", "resumo_caso", "observacoes", "ativo",
        ]
        clean = {key: data.get(key, "") for key in allowed}
        clean["ativo"] = int(bool(data.get("ativo", 1)))
        if not str(clean["nome_completo"]).strip() or not str(clean["resumo_caso"]).strip():
            raise ValueError("Nome completo e resumo do caso são obrigatórios.")
        if person_id:
            assignments = ", ".join(f"{key} = ?" for key in allowed)
            self.conn.execute(
                f"UPDATE pessoas SET {assignments}, atualizado_em = ? WHERE id = ?",
                (*[clean[key] for key in allowed], now, person_id),
            )
            action = "ATUALIZAR"
        else:
            cols = ",".join(allowed + ["criado_em", "atualizado_em"])
            marks = ",".join("?" for _ in allowed + ["criado_em", "atualizado_em"])
            cur = self.conn.execute(
                f"INSERT INTO pessoas({cols}) VALUES({marks})",
                (*[clean[key] for key in allowed], now, now),
            )
            person_id = int(cur.lastrowid)
            action = "CRIAR"
        self.conn.commit()
        self.audit(action, "pessoa", person_id, str(clean["nome_completo"]))
        return person_id

    def get_person(self, person_id: int) -> sqlite3.Row | None:
        return self.conn.execute("SELECT * FROM pessoas WHERE id = ?", (person_id,)).fetchone()

    def list_people(self, query: str = "") -> list[sqlite3.Row]:
        like = f"%{query.strip()}%"
        return self.conn.execute(
            """SELECT id, nome_completo, cpf, telefone, municipio, resumo_caso, ativo
               FROM pessoas WHERE nome_completo LIKE ? OR COALESCE(cpf,'') LIKE ?
               OR COALESCE(telefone,'') LIKE ? ORDER BY nome_completo COLLATE NOCASE""",
            (like, like, like),
        ).fetchall()

    def next_protocol(self) -> str:
        year = datetime.now().year
        prefix = f"ATD-{year}-"
        row = self.conn.execute(
            "SELECT protocolo FROM atendimentos WHERE protocolo LIKE ? ORDER BY id DESC LIMIT 1",
            (prefix + "%",),
        ).fetchone()
        sequence = int(row["protocolo"].split("-")[-1]) + 1 if row else 1
        return f"{prefix}{sequence:05d}"

    def save_appointment(self, data: dict[str, Any], appointment_id: int | None = None) -> int:
        now = self.now()
        allowed = [
            "pessoa_id", "protocolo", "data_atendimento", "canal", "area", "assunto", "relato",
            "providencias", "encaminhamentos", "resultado", "prioridade", "sigiloso", "status",
            "retorno_em", "lembrete_antecedencia", "concluido_em",
        ]
        clean = {key: data.get(key, "") for key in allowed}
        clean["sigiloso"] = int(bool(data.get("sigiloso", 0)))
        clean["lembrete_antecedencia"] = int(data.get("lembrete_antecedencia", 0) or 0)
        required = ("pessoa_id", "protocolo", "data_atendimento", "canal", "area", "assunto", "relato")
        if any(not str(clean[key]).strip() for key in required):
            raise ValueError("Pessoa, data, canal, área, assunto e relato são obrigatórios.")
        if appointment_id:
            assignments = ", ".join(f"{key} = ?" for key in allowed)
            self.conn.execute(
                f"UPDATE atendimentos SET {assignments}, atualizado_em = ? WHERE id = ?",
                (*[clean[key] for key in allowed], now, appointment_id),
            )
            action = "ATUALIZAR"
        else:
            cols = ",".join(allowed + ["criado_em", "atualizado_em"])
            marks = ",".join("?" for _ in allowed + ["criado_em", "atualizado_em"])
            cur = self.conn.execute(
                f"INSERT INTO atendimentos({cols}) VALUES({marks})",
                (*[clean[key] for key in allowed], now, now),
            )
            appointment_id = int(cur.lastrowid)
            action = "CRIAR"
        self.conn.commit()
        self.audit(action, "atendimento", appointment_id, str(clean["protocolo"]))
        return appointment_id

    def list_appointments(self, query: str = "", person_id: int | None = None) -> list[sqlite3.Row]:
        sql = """SELECT a.*, p.nome_completo FROM atendimentos a
                 JOIN pessoas p ON p.id = a.pessoa_id WHERE 1=1"""
        params: list[Any] = []
        if query:
            sql += " AND (a.protocolo LIKE ? OR a.assunto LIKE ? OR p.nome_completo LIKE ?)"
            like = f"%{query}%"
            params.extend([like, like, like])
        if person_id:
            sql += " AND a.pessoa_id = ?"
            params.append(person_id)
        sql += " ORDER BY a.data_atendimento DESC, a.id DESC"
        return self.conn.execute(sql, params).fetchall()

    def due_reminders(self) -> list[sqlite3.Row]:
        today = datetime.now().strftime("%Y-%m-%d")
        return self.conn.execute(
            """SELECT a.id, a.protocolo, a.retorno_em, a.assunto, a.prioridade, p.nome_completo
               FROM atendimentos a JOIN pessoas p ON p.id=a.pessoa_id
               WHERE a.retorno_em <> '' AND a.retorno_em IS NOT NULL
               AND date(a.retorno_em, '-' || a.lembrete_antecedencia || ' day') <= date(?)
               AND a.status NOT IN ('Concluído','Arquivado')
               ORDER BY date(a.retorno_em), a.prioridade DESC""",
            (today,),
        ).fetchall()

    def dashboard(self) -> dict[str, int]:
        result = {}
        result["pessoas"] = self.conn.execute("SELECT COUNT(*) FROM pessoas WHERE ativo=1").fetchone()[0]
        result["atendimentos"] = self.conn.execute("SELECT COUNT(*) FROM atendimentos").fetchone()[0]
        result["abertos"] = self.conn.execute(
            "SELECT COUNT(*) FROM atendimentos WHERE status NOT IN ('Concluído','Arquivado')"
        ).fetchone()[0]
        result["lembretes"] = len(self.due_reminders())
        return result

    def backup(self, destination_dir: str | Path) -> Path:
        dest = Path(destination_dir)
        dest.mkdir(parents=True, exist_ok=True)
        self.conn.commit()
        backup_path = dest / f"atendemp_backup_{datetime.now():%Y%m%d_%H%M%S}.db"
        target = sqlite3.connect(backup_path)
        try:
            self.conn.backup(target)
        finally:
            target.close()
        self.audit("BACKUP", "sistema", None, str(backup_path))
        return backup_path

