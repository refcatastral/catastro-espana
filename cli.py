# -*- coding: utf-8 -*-
"""
Interfaz de línea de comandos (CLI) para catastro-espana.
"""

import sys
import argparse
from .client import Catastro
from .sigpac import Sigpac


def main():
    parser = argparse.ArgumentParser(
        description="catastro-espana: Consulta el Catastro y SIGPAC en España vía RefCatastral.es"
    )
    parser.add_argument("referencia", nargs="?", help="Referencia catastral (14 o 20 caracteres)")
    parser.add_argument("--sigpac", nargs=4, type=int, metavar=("PROV", "MUN", "POL", "PARC"), help="Consultar parcela en SIGPAC")
    parser.add_argument("--coords", nargs=2, type=float, metavar=("LAT", "LON"), help="Geolocalización inversa de coordenadas GPS a referencia catastral")

    args = parser.parse_args()

    if args.sigpac:
        prov, mun, pol, parc = args.sigpac
        s = Sigpac()
        p = s.consultar_parcela(prov, mun, pol, parc)
        print(f"\n🌾 PARCELA SIGPAC {prov}-{mun}-{pol}-{parc}")
        print(f"Superficie total: {p.superficie_total_ha} ha ({p.superficie_total_m2:,} m²)")
        print(f"Total recintos: {p.total_recintos}")
        for r in p.recintos:
            print(f"  • Recinto {r.recinto}: {r.superficie_ha} ha | {r.descripcion_uso} | Pendiente: {r.pendiente_media_pct}%")
        print(f"\n🌐 Visor SIGPAC: {p.enlace_visor_sigpac}\n")
        return

    if args.coords:
        lat, lon = args.coords
        c = Catastro()
        inm = c.coordenadas_a_referencia(lat, lon)
        print(f"\n📍 COORDENADAS: ({lat}, {lon})")
        print(f"Referencia Catastral: {inm.referencia_catastral}")
        print(f"Dirección: {inm.direccion}")
        print(f"Municipio: {inm.municipio} ({inm.provincia})")
        print(f"\n🌐 Ficha y Visor: {inm.enlace_visor_cartografico}\n")
        return

    if args.referencia:
        c = Catastro()
        inm = c.consultar_referencia(args.referencia)
        print(f"\n🏛️ INMUEBLE CATASTRAL {inm.referencia_catastral}")
        print(f"Dirección: {inm.direccion}")
        print(f"Municipio: {inm.municipio} ({inm.provincia})")
        print(f"Superficie: {inm.superficie_construida_m2} m²" if inm.superficie_construida_m2 else "Superficie: No consta")
        print(f"Año construcción: {inm.ano_construccion}" if inm.ano_construccion else "Año construcción: No consta")
        print(f"Uso principal: {inm.uso_principal}")
        if inm.latitud and inm.longitud:
            print(f"Coordenadas WGS84: {inm.latitud:.6f}, {inm.longitud:.6f}")
        print(f"\n🌐 Explorar en Visor Catastro: {inm.enlace_visor_cartografico}\n")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
