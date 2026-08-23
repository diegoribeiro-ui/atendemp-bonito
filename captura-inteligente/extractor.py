from __future__ import annotations

import re
from dataclasses import dataclass, asdict


@dataclass
class ExtractedData:
    procedimentos: list[str]
    oficios: list[str]
    cpfs: list[str]
    datas: list[str]
    prazos: list[str]
    legislacao: list[str]
    partes: list[str]
    resumo: str

    def to_dict(self) -> dict:
        return asdict(self)


def unique(values: list[str]) -> list[str]:
    seen = set()
    result = []
    for value in values:
        clean = re.sub(r"\s+", " ", value).strip(" .,:;-")
        key = clean.casefold()
        if clean and key not in seen:
            seen.add(key)
            result.append(clean)
    return result


def extract_information(text: str) -> ExtractedData:
    normalized = text.replace("\r", "\n")
    procedimentos = re.findall(
        r"\b(?:NF|Not[ií]cia\s+de\s+Fato|PA|IC|Procedimento)\s*(?:n[.º°o]*)?\s*[:\-]?\s*"
        r"\d{2}\.\d{4}\.\d{8}-\d\b",
        normalized,
        flags=re.I,
    )
    procedimentos += re.findall(r"\b\d{2}\.\d{4}\.\d{8}-\d\b", normalized)
    oficios = re.findall(
        r"\bOf[ií]cio\s*(?:n[.º°o]*)?\s*[:\-]?\s*\d{1,5}(?:[./-]\d{2,4})?",
        normalized,
        flags=re.I,
    )
    cpfs = re.findall(r"\b\d{3}\.?\d{3}\.?\d{3}[-.]?\d{2}\b", normalized)
    datas = re.findall(r"\b(?:0?[1-9]|[12]\d|3[01])[/.-](?:0?[1-9]|1[0-2])[/.-](?:19|20)?\d{2}\b", normalized)
    prazos = re.findall(
        r"\b(?:prazo\s+(?:de\s+)?|no\s+prazo\s+de\s+)(\d{1,3}\s+dias?(?:\s+(?:corridos|[úu]teis))?)",
        normalized,
        flags=re.I,
    )
    legislacao = re.findall(
        r"\b(?:Lei|Decreto|Resolu[cç][aã]o|Portaria|Constitui[cç][aã]o|CF|ECA|CPP|CPC)"
        r"(?:\s+(?:Federal|Estadual|Municipal))?\s*(?:n[.º°o]*)?\s*[\d.]+(?:/\d{2,4})?",
        normalized,
        flags=re.I,
    )
    legislacao += re.findall(
        r"\barts?\.?(?:\s*\d+[º°]?(?:-[A-Z])?)(?:\s*,\s*\d+[º°]?(?:-[A-Z])?)*(?:\s+da\s+[A-ZÇ][A-Za-zÀ-ÿ\s]+)?",
        normalized,
        flags=re.I,
    )
    partes = []
    for label, name in re.findall(
        r"(?im)^\s*(Requerente|Noticiante|Interessad[oa]|V[ií]tima|Noticiad[oa]|Representante|Destinat[aá]rio|Remetente)\s*:\s*([^\n]{3,120})",
        normalized,
    ):
        partes.append(f"{label}: {name}")
    plain = re.sub(r"\s+", " ", normalized).strip()
    sentences = re.split(r"(?<=[.!?])\s+", plain)
    summary = " ".join(sentences[:3])[:900]
    return ExtractedData(
        procedimentos=unique(procedimentos),
        oficios=unique(oficios),
        cpfs=unique(cpfs),
        datas=unique(datas),
        prazos=unique(prazos),
        legislacao=unique(legislacao),
        partes=unique(partes),
        resumo=summary,
    )

