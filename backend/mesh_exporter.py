"""
mesh_exporter.py — Exportador de Mallas Craneales 3D a STL y OBJ para CraniumFit
================================================================================
Convierte la geometría paramétrica craniométrica generada por craniometrics.py
a archivos estándar .STL (ASCII) y .OBJ para ser renderizados con Three.js
o descargados por los doctores para diseño CAD de cascos ortésicos.
"""

import math
from pathlib import Path
from typing import Dict, Any, List
from craniometrics import generate_cranial_mesh_geometry

def export_geometry_to_stl(geom: Dict[str, Any], output_path: Path, solid_name: str = "cranial_scan"):
    """Exporta geometría a formato STL ASCII."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    verts = geom["vertices"]
    indices = geom["indices"]

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"solid {solid_name}\n")
        
        for k in range(0, len(indices), 3):
            idx0 = indices[k] * 3
            idx1 = indices[k + 1] * 3
            idx2 = indices[k + 2] * 3

            v0 = (verts[idx0], verts[idx0 + 1], verts[idx0 + 2])
            v1 = (verts[idx1], verts[idx1 + 1], verts[idx1 + 2])
            v2 = (verts[idx2], verts[idx2 + 1], verts[idx2 + 2])

            # Calcular vector normal por producto cruz
            ax, ay, az = v1[0] - v0[0], v1[1] - v0[1], v1[2] - v0[2]
            bx, by, bz = v2[0] - v0[0], v2[1] - v0[1], v2[2] - v0[2]

            nx = ay * bz - az * by
            ny = az * bx - ax * bz
            nz = ax * by - ay * bx
            length = math.sqrt(nx*nx + ny*ny + nz*nz)
            if length > 0.000001:
                nx, ny, nz = nx / length, ny / length, nz / length
            else:
                nx, ny, nz = 0.0, 1.0, 0.0

            f.write(f"  facet normal {nx:.4f} {ny:.4f} {nz:.4f}\n")
            f.write("    outer loop\n")
            f.write(f"      vertex {v0[0]:.4f} {v0[1]:.4f} {v0[2]:.4f}\n")
            f.write(f"      vertex {v1[0]:.4f} {v1[1]:.4f} {v1[2]:.4f}\n")
            f.write(f"      vertex {v2[0]:.4f} {v2[1]:.4f} {v2[2]:.4f}\n")
            f.write("    endloop\n")
            f.write("  endfacet\n")

        f.write(f"endsolid {solid_name}\n")

def export_geometry_to_obj(geom: Dict[str, Any], output_path: Path, object_name: str = "cranial_scan"):
    """Exporta geometría a formato Wavefront OBJ."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    verts = geom["vertices"]
    indices = geom["indices"]

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(f"# CraniumFit Wavefront OBJ File\n")
        f.write(f"o {object_name}\n")

        # Vértices (Three.js espera 1-indexed faces)
        for i in range(0, len(verts), 3):
            f.write(f"v {verts[i]:.4f} {verts[i+1]:.4f} {verts[i+2]:.4f}\n")

        for k in range(0, len(indices), 3):
            f.write(f"f {indices[k]+1} {indices[k+1]+1} {indices[k+2]+1}\n")

def generate_patient_seed_files(base_uploads_dir: Path):
    """Genera archivos de muestra STL y OBJ para pat_lucas (T0 antes y T2 después)."""
    lucas_dir = base_uploads_dir / "scans" / "pat_lucas"
    lucas_dir.mkdir(parents=True, exist_ok=True)

    # 1. Sesión 1 (T0 - Inicial con CVAI 11.2% Severo)
    geom_t0 = generate_cranial_mesh_geometry(cvai=11.2, flat_quadrant="right_posterior")
    stl_t0 = lucas_dir / "lucas_torres_t0_scan.stl"
    obj_t0 = lucas_dir / "lucas_torres_t0_scan.obj"
    export_geometry_to_stl(geom_t0, stl_t0, "lucas_t0_initial")
    export_geometry_to_obj(geom_t0, obj_t0, "lucas_t0_initial")

    # 2. Sesión 3 (T2 - Control 2 Meses con CVAI 5.4% Leve/Corregido)
    geom_t2 = generate_cranial_mesh_geometry(cvai=5.4, flat_quadrant="right_posterior")
    stl_t2 = lucas_dir / "lucas_torres_t2_scan.stl"
    obj_t2 = lucas_dir / "lucas_torres_t2_scan.obj"
    export_geometry_to_stl(geom_t2, stl_t2, "lucas_t2_evolution")
    export_geometry_to_obj(geom_t2, obj_t2, "lucas_t2_evolution")

    # 3. Sesión Sofia (pat_sofia T0 Braquicefalia)
    sofia_dir = base_uploads_dir / "scans" / "pat_sofia"
    sofia_dir.mkdir(parents=True, exist_ok=True)
    geom_sofia = generate_cranial_mesh_geometry(cvai=3.2, flat_quadrant="right_posterior")
    export_geometry_to_stl(geom_sofia, sofia_dir / "sofia_paredes_t0_scan.stl", "sofia_t0")
    export_geometry_to_obj(geom_sofia, sofia_dir / "sofia_paredes_t0_scan.obj", "sofia_t0")

    print(f"✅ Archivos 3D reales .STL y .OBJ generados en: {lucas_dir}")

if __name__ == "__main__":
    uploads = Path(__file__).resolve().parent / "uploads"
    generate_patient_seed_files(uploads)
