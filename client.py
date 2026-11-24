# -*- coding: utf-8 -*-
"""
Módulo cliente para la Dirección General del Catastro (DGC) de España.
Desarrollado por RefCatastral.es (https://refcatastral.es)
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET


@dataclass
class InmuebleCatastral:
    referencia_catastral: str
    direccion: str
    municipio: str
    provincia: str
    codigo_postal: Optional[str]
    superficie_construida_m2: Optional[int]
    ano_construccion: Optional[int]
    uso_principal: str
    latitud: Optional[float]
    longitud: Optional[float]
    enlace_refcatastral: str
    enlace_visor_cartografico: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "referencia_catastral": self.referencia_catastral,
            "direccion": self.direccion,
            "municipio": self.municipio,
            "provincia": self.provincia,
            "codigo_postal": self.codigo_postal,
            "superficie_construida_m2": self.superficie_construida_m2,
            "ano_construccion": self.ano_construccion,
            "uso_principal": self.uso_principal,
            "latitud": self.latitud,
            "longitud": self.longitud,
            "enlace_refcatastral": self.enlace_refcatastral,
            "enlace_visor_cartografico": self.enlace_visor_cartografico,
        }


class Catastro:
    """Cliente para consultar datos físicos y cartográficos del Catastro de España."""

    def __init__(self, user_agent: str = "CatastroEspana-Python/1.0 (+https://refcatastral.es)"):
        self.user_agent = user_agent

    def _fetch_xml(self, url: str) -> str:
        req = urllib.request.Request(url, headers={"User-Agent": self.user_agent})
        with urllib.request.urlopen(req, timeout=12) as response:
            return response.read().decode("utf-8")

    def consultar_referencia(self, rc: str) -> InmuebleCatastral:
        """
        Consulta los datos físicos, superficie y dirección de un inmueble a partir de
        su Referencia Catastral oficial (14 o 20 caracteres).
        """
        rc_clean = "".join(c for c in rc if c.isalnum()).upper()
        if len(rc_clean) < 14:
            raise ValueError(f"Referencia catastral inválida: '{rc}'. Debe tener al menos 14 caracteres.")

        # 1. Consulta alfanumérica en OVC
        url_datos = (
            f"https://ovc.catastro.meh.es/ovcservweb/OVCSWLocalizacionRC/OVCCallejero.asmx/Consulta_DNPRC?"
            f"Provincia=&Municipio=&RC={urllib.parse.quote(rc_clean)}"
        )
        xml_datos = self._fetch_xml(url_datos)
        root = ET.fromstring(xml_datos)

        # Comprobar error OVC
        err_node = root.find(".//{http://www.catastro.meh.es/}des")
        if err_node is not None and root.find(".//{http://www.catastro.meh.es/}bico") is None:
            raise RuntimeError(f"Error devuelto por Catastro: {err_node.text}")

        ldt = root.find(".//{http://www.catastro.meh.es/}ldt")
        np = root.find(".//{http://www.catastro.meh.es/}np")
        nm = root.find(".//{http://www.catastro.meh.es/}nm")
        dp = root.find(".//{http://www.catastro.meh.es/}dp")
        luso = root.find(".//{http://www.catastro.meh.es/}luso")
        sfc = root.find(".//{http://www.catastro.meh.es/}sfc")
        ant = root.find(".//{http://www.catastro.meh.es/}ant")

        # 2. Obtener coordenadas geográficas (WGS84)
        prov_code = rc_clean[:2]
        url_coor = (
            f"https://ovc.catastro.meh.es/ovcservweb/OVCSWLocalizacionRC/OVCCoordenadas.asmx/Consulta_CPMRC?"
            f"Provincia={prov_code}&Municipio=&RC={urllib.parse.quote(rc_clean)}&SRS=EPSG:4326"
        )
        lat, lon = None, None
        try:
            xml_coor = self._fetch_xml(url_coor)
            root_c = ET.fromstring(xml_coor)
            ycen = root_c.find(".//{http://www.catastro.meh.es/}coord/{http://www.catastro.meh.es/}geo/{http://www.catastro.meh.es/}ycen")
            xcen = root_c.find(".//{http://www.catastro.meh.es/}coord/{http://www.catastro.meh.es/}geo/{http://www.catastro.meh.es/}xcen")
            if ycen is not None and xcen is not None:
                lat = float(ycen.text)
                lon = float(xcen.text)
        except Exception:
            pass

        return InmuebleCatastral(
            referencia_catastral=rc_clean,
            direccion=ldt.text if ldt is not None else "Dirección no disponible",
            municipio=nm.text if nm is not None else "",
            provincia=np.text if np is not None else "",
            codigo_postal=dp.text if dp is not None else None,
            superficie_construida_m2=int(sfc.text) if sfc is not None and sfc.text and sfc.text.isdigit() else None,
            ano_construccion=int(ant.text) if ant is not None and ant.text and ant.text.isdigit() else None,
            uso_principal=luso.text if luso is not None else "No especificado",
            latitud=lat,
            longitud=lon,
            enlace_refcatastral="https://refcatastral.es",
            enlace_visor_cartografico=f"https://refcatastral.es/visor-catastro/?ref={rc_clean}",
        )

    def coordenadas_a_referencia(self, lat: float, lon: float) -> InmuebleCatastral:
        """
        Geolocalización inversa: Convierte coordenadas GPS (latitud y longitud WGS84)
        en la Referencia Catastral y datos del inmueble correspondiente.
        """
        url = (
            f"https://ovc.catastro.meh.es/ovcservweb/OVCSWLocalizacionRC/OVCCoordenadas.asmx/Consulta_RCCOOR?"
            f"SRS=EPSG:4326&Coordenada_X={lon}&Coordenada_Y={lat}"
        )
        xml_str = self._fetch_xml(url)
        root = ET.fromstring(xml_str)

        pc1 = root.find(".//{http://www.catastro.meh.es/}pc1")
        pc2 = root.find(".//{http://www.catastro.meh.es/}pc2")

        if pc1 is None or pc2 is None:
            raise LookupError(f"No se encontró ningún inmueble catastral en las coordenadas ({lat}, {lon}).")

        rc = f"{pc1.text}{pc2.text}"
        return self.consultar_referencia(rc)
