"""
craniometrics.py — Motor de Análisis Craniométrico y Generación 3D para CraniumFit
==================================================================================
Implementa algoritmos médicos estandarizados:
- CVAI (Cranial Vault Asymmetry Index): Diferencia relativa de diagonales a 30°.
- Índice Cefálico (CI): Relación ancho / largo biparietal.
- Clasificación Clínica de Argenta (Grados I al V).
- Generador de Malla 3D Paramétrica Craneal para renderizado Three.js / WebGL.
"""

import math
from typing import Dict, Any, List, Tuple

def calculate_cvai(diag_a_mm: float, diag_b_mm: float) -> float:
    """
    Calcula el Cranial Vault Asymmetry Index (CVAI):
    CVAI = (|DiagA - DiagB| / max(DiagA, DiagB)) * 100
    """
    if diag_a_mm <= 0 or diag_b_mm <= 0:
        return 0.0
    diff = abs(diag_a_mm - diag_b_mm)
    max_diag = max(diag_a_mm, diag_b_mm)
    return round((diff / max_diag) * 100.0, 2)

def calculate_cephalic_index(width_mm: float, length_mm: float) -> float:
    """
    Calcula el Índice Cefálico (CI):
    CI = (Ancho / Largo) * 100
    Valores normales en lactantes: 76% - 85% (Mesocéfalo).
    > 85%: Braquicefalia (cabeza ancha y aplanada atrás).
    < 76%: Dolicocefalia / Escafocefalia (cabeza alargada y estrecha).
    """
    if length_mm <= 0:
        return 0.0
    return round((width_mm / length_mm) * 100.0, 1)

def get_argenta_classification(cvai: float, is_brachycephalic: bool = False) -> Dict[str, Any]:
    """
    Clasificación clínica de deformidades posicionales según la escala de Louis Argenta:
    - Normal / Simétrico: CVAI < 3.5%
    - Grado I (Leve): CVAI 3.5% - 6.25% (Aplanamiento occipital aislado)
    - Grado II (Moderado): CVAI 6.25% - 8.75% (Aplanamiento + desplazamiento anterior oreja)
    - Grado III (Severo): CVAI 8.75% - 11.0% (Aplanamiento + oreja + prominencia frontal)
    - Grado IV (Grave): CVAI 11.0% - 13.5% (Asimetría facial visible anterior)
    - Grado V (Muy Grave): CVAI > 13.5% (Elevación vertical parietal / vertex)
    """
    if cvai < 3.5:
        grade = 0
        severity = "Normocefalia / Simétrico"
        recommendation = "No requiere órtesis craneal. Manejo postural y seguimiento preventivo."
        color = "#10B981" # Verde
    elif cvai < 6.25:
        grade = 1
        severity = "Grado I — Leve"
        recommendation = "Terapia posicional guiada y fisioterapia cervical. Posible casco si no mejora tras 6 meses."
        color = "#3B82F6" # Azul
    elif cvai < 8.75:
        grade = 2
        severity = "Grado II — Moderado"
        recommendation = "Candidato a Órtesis Craneal Dinámica CraniumFit. Estimulación y control quincenal."
        color = "#F59E0B" # Ámbar
    elif cvai < 11.0:
        grade = 3
        severity = "Grado III — Severo"
        recommendation = "Tratamiento con Órtesis Craneal Urgente (23h/día). Alta probabilidad de éxito entre 4-8 meses."
        color = "#F97316" # Naranja
    elif cvai < 13.5:
        grade = 4
        severity = "Grado IV — Muy Severo"
        recommendation = "Tratamiento con Órtesis Craneal de Doble Alivio. Seguimiento con neurocirugía y fisioterapia."
        color = "#EF4444" # Rojo
    else:
        grade = 5
        severity = "Grado V — Grave con Deformidad Vertical"
        recommendation = "Intervención ortésica de choque inmediata. Descartar sinostosis mediante tomografía."
        color = "#991B1B" # Rojo Oscuro

    return {
        "grade": grade,
        "severity": severity,
        "recommendation": recommendation,
        "color": color,
        "is_orthosis_indicated": grade >= 2
    }

def generate_cranial_mesh_geometry(cvai: float = 8.5, flat_quadrant: str = "right_posterior") -> Dict[str, Any]:
    """
    Genera un modelo geométrico paramétrico tridimensional de cabeza de infante
    con deformidad controlada por CVAI para ser renderizado en Three.js con mapas de calor.
    Retorna arrays de vértices, normales, índices y mapa de curvatura/asimetría.
    """
    # Generamos una elipsoide semiesférica perturbada por la asimetría
    lat_steps = 32
    lon_steps = 48
    
    vertices = []
    colors = [] # Mapa de calor: Azul (normal), Verde (corrección), Rojo (área plana/presión)
    indices = []
    
    # Radios anatómicos promedio lactante (en cm normalizados)
    rx = 6.4 # Ancho lateral
    ry = 8.0 # Altura craneal
    rz = 7.8 # Longitud anteroposterior
    
    # Cuantificación de distorsión
    distortion_factor = (cvai / 100.0) * 1.8
    
    for i in range(lat_steps + 1):
        v = i / lat_steps
        phi = v * math.pi # 0 a PI (polo norte a base)
        
        for j in range(lon_steps + 1):
            u = j / lon_steps
            theta = u * 2 * math.pi # 0 a 2*PI
            
            # Coordenadas base en elipsoide craneal
            x = rx * math.sin(phi) * math.cos(theta)
            y = ry * math.cos(phi)
            z = rz * math.sin(phi) * math.sin(theta)
            
            # Modulación para simular aplanamiento occipital derecho (Plagiocefalia típica)
            # Occipital derecho: theta entre PI y 1.5*PI, parte posterior inferior
            is_affected = False
            heat = 0.0 # 0.0 (simétrico) a 1.0 (aplanado)
            
            if flat_quadrant == "right_posterior":
                # Cuadrante occipital derecho: x > 0 y z < 0
                if x > 0 and z < 0 and y > -2.0:
                    dist_to_flat_center = math.sqrt((x - 3.5)**2 + (z + 4.0)**2 + (y - 1.0)**2)
                    if dist_to_flat_center < 5.0:
                        flatten_amount = (5.0 - dist_to_flat_center) * distortion_factor * 0.7
                        z += flatten_amount # aplana empujando hacia adelante
                        x -= flatten_amount * 0.4
                        heat = min(1.0, (5.0 - dist_to_flat_center) / 3.5)
                        is_affected = True
                        
                # Compensación frontal contralateral (anterior izquierdo: x < 0 y z > 0)
                elif x < 0 and z > 2.0 and y > 0:
                    dist_frontal = math.sqrt((x + 2.5)**2 + (z - 4.5)**2)
                    if dist_frontal < 4.0:
                        bulge = (4.0 - dist_frontal) * distortion_factor * 0.4
                        z += bulge
                        heat = min(0.6, (4.0 - dist_frontal) / 4.0)

            vertices.extend([round(x, 3), round(y, 3), round(z, 3)])
            
            # Colores del Heatmap en RGB (de Azul/Cian -> Verde -> Naranja -> Rojo)
            if heat < 0.2:
                # Normal / Azul-Cian
                colors.extend([0.05, 0.71, 0.73]) # #0D9488 Teal
            elif heat < 0.5:
                # Leve / Amarillo
                colors.extend([0.96, 0.75, 0.15]) # #F59E0B
            else:
                # Zona de máxima deformidad / Rojo
                colors.extend([0.94, 0.27, 0.27]) # #EF4444

    # Generación de triángulos (índices)
    for i in range(lat_steps):
        for j in range(lon_steps):
            first = i * (lon_steps + 1) + j
            second = first + lon_steps + 1
            
            indices.extend([first, second, first + 1])
            indices.extend([second, second + 1, first + 1])
            
    return {
        "vertices": vertices,
        "colors": colors,
        "indices": indices,
        "cvai": cvai,
        "diagonals": {
            "diag_a": round(142.0, 1),
            "diag_b": round(142.0 - (cvai / 100.0 * 142.0), 1),
            "angle_deg": 30
        }
    }
