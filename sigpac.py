# -*- coding: utf-8 -*-
"""
Módulo cliente para el Sistema de Información Geográfica de Parcelas Agrícolas (SIGPAC).
Desarrollado por RefCatastral.es (https://refcatastral.es)
"""

from dataclasses import dataclass
from typing import List, Optional, Dict, Any
import urllib.request
import json
import gzip

USOS_SIGPAC = {
    "TA": "Tierras Arables / Cultivos Herbáceos",
    "TH": "Huerta / Cultivos Hortícolas",
    "VF": "Viñedo en Regadío",
    "VI": "Viñedo en Secano",
    "OF": "Olivar en Regadío",
    "OL": "Olivar en Secano",
    "FY": "Frutales",
    "FF": "Frutales en Regadío",
    "CI": "Cítricos",
    "CF": "Cítricos en Regadío",
    "FS": "Frutos Secos",
    "CS": "Cultivos Subtropicales",
    "PR": "Pastizal / Pastos Permanentes",
    "PS": "Pastizal con Arbolado / Dehesa",
    "PA": "Pastos Arbustivos",
    "MT": "Matorral",
    "FO": "Forestal / Masa Arbolada",
    "AG": "Aguas Corrientes y Embalses",
    "ED": "Edificación / Construcción",
    "ZU": "Zona Urbana",
    "ZV": "Vereda / Vía de Comunicación",
    "IM": "Improductivo",
}


@dataclass
class RecintoSigpac:
    recinto: int
    superficie_ha: float
    superficie_m2: int
    codigo_uso: str
    descripcion_uso: str
    pendiente_media_pct: float
    coeficiente_regadio: float
    altitud_metros: Optional[int]


@dataclass
class ParcelaSigpac:
    provincia: int
    municipio: int
    poligono: int
    parcela: int
    superficie_total_ha: float
    superficie_total_m2: int
    total_recintos: int
    recintos: List[RecintoSigpac]
    enlace_visor_sigpac: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "provincia": self.provincia,
            "municipio": self.municipio,
            "poligono": self.poligono,
            "parcela": self.parcela,
            "superficie_total_ha": self.superficie_total_ha,
            "superficie_total_m2": self.superficie_total_m2,
            "total_recintos": self.total_recintos,
            "enlace_visor_sigpac": self.enlace_visor_sigpac,
            "recintos": [
                {
                    "recinto": r.recinto,
                    "superficie_ha": r.superficie_ha,
                    "superficie_m2": r.superficie_m2,
                    "codigo_uso": r.codigo_uso,
                    "descripcion_uso": r.descripcion_uso,
                    "pendiente_media_pct": r.pendiente_media_pct,
                    "coeficiente_regadio": r.coeficiente_regadio,
                    "altitud_metros": r.altitud_metros,
                }
                for r in self.recintos
            ],
        }


class Sigpac:
    """Cliente oficial para consultas de parcelas rústicas y recintos agrícolas SIGPAC (FEGA / MAPA)."""

    def __init__(self, user_agent: str = "CatastroEspana-Python/1.0 (+https://refcatastral.es)"):
        self.user_agent = user_agent

    def _fetch_json(self, url: str) -> Any:
        req = urllib.request.Request(
            url,
            headers={
                "User-Agent": self.user_agent,
                "Accept": "application/json, text/plain, */*",
                "Accept-Encoding": "gzip, deflate",
            },
        )
        with urllib.request.urlopen(req, timeout=12) as response:
            raw = response.read()
            if len(raw) >= 2 and raw[0] == 0x1F and raw[1] == 0x8B:
                raw = gzip.decompress(raw)
            return json.loads(raw.decode("utf-8"))

    def consultar_parcela(self, provincia: int, municipio: int, poligono: int, parcela: int) -> ParcelaSigpac:
        """
        Consulta todos los recintos, usos del suelo y pendientes de una parcela agrícola en SIGPAC.
        """
        url = (
            f"https://sigpac-hubcloud.es/servicioconsultassigpac/query/recinfoparc/"
            f"{provincia}/{municipio}/0/0/{poligono}/{parcela}.json"
        )
        data = self._fetch_json(url)

        if not isinstance(data, list) or len(data) == 0:
            raise LookupError(
                f"No se encontraron datos en SIGPAC para la parcela Prov:{provincia}, Mun:{municipio}, Pol:{poligono}, Parc:{parcela}."
            )

        total_ha = 0.0
        recintos = []
        for r in data:
            sup_ha = float(r.get("superficie") or 0.0)
            total_ha += sup_ha
            uso_cod = (r.get("uso_sigpac") or "").upper()
            recintos.append(
                RecintoSigpac(
                    recinto=int(r.get("recinto") or 0),
                    superficie_ha=round(sup_ha, 4),
                    superficie_m2=int(round(sup_ha * 10000)),
                    codigo_uso=uso_cod,
                    descripcion_uso=USOS_SIGPAC.get(uso_cod, "Uso agrario específico"),
                    pendiente_media_pct=float(r.get("pendiente_media") or 0.0),
                    coeficiente_regadio=float(r.get("coef_regadio") or 0.0),
                    altitud_metros=int(r.get("altitud")) if r.get("altitud") else None,
                )
            )

        return ParcelaSigpac(
            provincia=provincia,
            municipio=municipio,
            poligono=poligono,
            parcela=parcela,
            superficie_total_ha=round(total_ha, 4),
            superficie_total_m2=int(round(total_ha * 10000)),
            total_recintos=len(recintos),
            recintos=recintos,
            enlace_visor_sigpac="https://refcatastral.es/visor-sigpac/",
        )

    def desglosar_referencia(self, referencia_rustica: str) -> Dict[str, Any]:
        """
        Desglosa una Referencia Catastral rústica oficial de 14 dígitos en los
        parámetros territoriales correspondientes a SIGPAC.
        """
        rc = "".join(c for c in referencia_rustica if c.isalnum()).upper()
        if len(rc) < 14:
            raise ValueError(f"Referencia rústica '{referencia_rustica}' inválida. Debe tener al menos 14 dígitos.")

        prov = int(rc[0:2])
        mun = int(rc[2:5])
        sector = rc[5:6]
        pol = int(rc[6:9])
        parc = int(rc[9:14])

        return {
            "referencia": rc[:14],
            "provincia": prov,
            "municipio": mun,
            "sector": sector,
            "poligono": pol,
            "parcela": parc,
            "enlace_visor_sigpac": "https://refcatastral.es/visor-sigpac/",
        }
