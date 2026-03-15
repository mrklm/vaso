import numpy as np
from model import VaseParameters, Profile


def _validate_params(params: VaseParameters) -> None:
    if len(params.profiles) < 2:
        raise ValueError("Il faut au minimum 2 profils.")

    if params.height_mm <= 0:
        raise ValueError("La hauteur totale doit être strictement positive.")

    if params.wall_thickness_mm <= 0:
        raise ValueError("L'épaisseur de coque doit être strictement positive.")

    if params.bottom_thickness_mm < 0:
        raise ValueError("L'épaisseur du fond ne peut pas être négative.")

    if params.radial_samples < 8:
        raise ValueError("radial_samples doit être >= 8.")

    if params.vertical_samples < 2:
        raise ValueError("vertical_samples doit être >= 2.")

    profiles_sorted = sorted(params.profiles, key=lambda p: p.z_ratio)
    for i, profile in enumerate(profiles_sorted):
        if not (0.0 <= profile.z_ratio <= 1.0):
            raise ValueError(f"Le profil {i + 1} a un z_ratio hors limites [0.0 ; 1.0].")
        if profile.diameter <= 0:
            raise ValueError(f"Le profil {i + 1} a un diamètre non valide.")
        if profile.sides < 3:
            raise ValueError(f"Le profil {i + 1} doit avoir au moins 3 côtés.")
        if profile.scale_x <= 0 or profile.scale_y <= 0:
            raise ValueError(f"Le profil {i + 1} a une échelle X/Y non valide.")
        if profile.diameter <= 2.0 * params.wall_thickness_mm:
            raise ValueError(
                f"Le profil {i + 1} est trop petit pour une coque de "
                f"{params.wall_thickness_mm:.2f} mm."
            )


def _regular_polygon_vertices(profile: Profile) -> np.ndarray:
    radius = profile.diameter / 2.0
    rotation = np.radians(profile.rotation_deg)

    angles = np.linspace(0.0, 2.0 * np.pi, profile.sides, endpoint=False) + rotation
    x = np.cos(angles) * radius * profile.scale_x + profile.offset_x
    y = np.sin(angles) * radius * profile.scale_y + profile.offset_y

    return np.column_stack((x, y))


def _resample_closed_contour(vertices: np.ndarray, samples: int) -> np.ndarray:
    pts = np.asarray(vertices, dtype=float)
    n = len(pts)

    if n < 3:
        raise ValueError("Un contour fermé doit contenir au moins 3 points.")

    edges = []
    lengths = []

    for i in range(n):
        a = pts[i]
        b = pts[(i + 1) % n]
        edges.append((a, b))
        lengths.append(np.linalg.norm(b - a))

    lengths = np.array(lengths, dtype=float)
    perimeter = lengths.sum()

    if perimeter <= 0:
        raise ValueError("Périmètre nul détecté sur un contour.")

    cumulative = np.zeros(n + 1, dtype=float)
    cumulative[1:] = np.cumsum(lengths)

    targets = np.linspace(0.0, perimeter, samples, endpoint=False)
    result = []

    edge_index = 0
    for dist in targets:
        while not (cumulative[edge_index] <= dist < cumulative[edge_index + 1]):
            edge_index += 1
            if edge_index >= n:
                edge_index = n - 1
                break

        a, b = edges[edge_index]
        edge_len = lengths[edge_index]

        if edge_len == 0:
            result.append(a.copy())
            continue

        local_t = (dist - cumulative[edge_index]) / edge_len
        p = (1.0 - local_t) * a + local_t * b
        result.append(p)

    return np.asarray(result, dtype=float)


def _build_profile_contour(profile: Profile, samples: int) -> np.ndarray:
    polygon = _regular_polygon_vertices(profile)
    contour = _resample_closed_contour(polygon, samples)
    return contour


def _interpolate_contours(c1: np.ndarray, c2: np.ndarray, t: float) -> np.ndarray:
    return (1.0 - t) * c1 + t * c2


SUPPORTLESS_MAX_OVERHANG_DEG = 42.0


def _texture_zoom_to_params(texture_zoom: str) -> tuple[float, float]:
    mapping = {
        "Très fin": (1.0, 22.0),
        "Fin": (1.8, 14.0),
        "Moyen": (3.0, 9.0),
        "Gros": (4.4, 5.5),
        "Très gros": (6.0, 3.2),
    }
    return mapping.get(texture_zoom, mapping["Moyen"])


def _apply_texture_to_contour(
    contour: np.ndarray,
    z_mm: float,
    params: VaseParameters,
) -> np.ndarray:
    texture_type = getattr(params, "texture_type", "Pas de texture")
    if texture_type == "Pas de texture":
        return contour

    amplitude_mm, base_frequency = _texture_zoom_to_params(
        getattr(params, "texture_zoom", "Moyen")
    )

    pts = np.asarray(contour, dtype=float).copy()
    if len(pts) == 0:
        return pts

    z_ratio = 0.0 if params.height_mm <= 0 else float(z_mm) / float(params.height_mm)

    radii = np.linalg.norm(pts, axis=1)
    safe_radii = np.maximum(radii, 1e-9)
    angles = np.arctan2(pts[:, 1], pts[:, 0])

    envelope = 0.55 + 0.45 * np.sin(np.pi * z_ratio)

    if texture_type == "Cannelures":
        offset = amplitude_mm * envelope * np.cos(base_frequency * angles)

    elif texture_type == "Anneaux":
        offset = amplitude_mm * envelope * np.sin(
            2.0 * np.pi * (base_frequency * 1.55) * z_ratio
        ) * np.ones_like(radii)

    elif texture_type == "Spirale":
        offset = amplitude_mm * envelope * np.sin(
            angles + 2.0 * np.pi * (base_frequency * 0.26) * z_ratio
        )

    elif texture_type == "Double spirale":
        offset = amplitude_mm * envelope * np.sin(
            2.0 * angles + 2.0 * np.pi * (base_frequency * 0.26) * z_ratio
        )

    elif texture_type == "Bulles":
        bubble_field = np.exp(
            -(
                2.8 * np.sin(base_frequency * angles) ** 2
                + 2.2 * np.sin(
                    2.0 * np.pi * max(2.0, base_frequency * 0.62) * z_ratio
                ) ** 2
            )
        )
        offset = amplitude_mm * envelope * (bubble_field - 0.30)

    elif texture_type == "Hexagones":
        cell = (
            np.sin(base_frequency * angles)
            * np.sin(2.0 * np.pi * max(2.0, base_frequency * 0.65) * z_ratio)
        )
        quantized = np.round(cell * 4.0) / 4.0
        offset = amplitude_mm * envelope * quantized

    elif texture_type == "LowPoly":
        step = (2.0 * np.pi) / max(6, int(round(base_frequency)))
        angle_quant = np.round(angles / step) * step
        offset = amplitude_mm * envelope * np.sign(
            np.cos(angle_quant * max(3.0, base_frequency * 0.8))
        )

    elif texture_type == "Martelé":
        offset = amplitude_mm * envelope * (
            0.60 * np.sin(5.3 * angles + 2.0 * np.pi * 3.0 * z_ratio)
            + 0.25 * np.sin(9.7 * angles - 2.0 * np.pi * 1.7 * z_ratio)
            + 0.15 * np.cos(13.1 * angles + 2.0 * np.pi * 4.2 * z_ratio)
        )

    else:
        return pts

    max_safe_offset = np.maximum(0.6, radii - params.wall_thickness_mm - 1.0)
    offset = np.clip(offset, -0.92 * max_safe_offset, 0.92 * max_safe_offset)

    new_radii = np.maximum(radii + offset, params.wall_thickness_mm + 1.0)
    scale = new_radii / safe_radii

    pts[:, 0] *= scale
    pts[:, 1] *= scale

    return pts


def _max_supportless_radial_step(dz_mm: float) -> float:
    return max(
        0.25,
        float(dz_mm) * np.tan(np.radians(SUPPORTLESS_MAX_OVERHANG_DEG)),
    )


def _limit_contour_step_from_previous(
    previous_contour: np.ndarray,
    current_contour: np.ndarray,
    max_radial_step_mm: float,
    wall_thickness_mm: float,
) -> np.ndarray:
    prev = np.asarray(previous_contour, dtype=float)
    curr = np.asarray(current_contour, dtype=float).copy()

    prev_radii = np.linalg.norm(prev, axis=1)
    curr_radii = np.linalg.norm(curr, axis=1)
    safe_curr_radii = np.maximum(curr_radii, 1e-9)

    lower_bound = np.maximum(
        wall_thickness_mm + 1.0,
        prev_radii - max_radial_step_mm,
    )
    upper_bound = prev_radii + max_radial_step_mm

    clamped_radii = np.clip(curr_radii, lower_bound, upper_bound)
    scale = clamped_radii / safe_curr_radii

    curr[:, 0] *= scale
    curr[:, 1] *= scale

    return curr


def _interpolated_outer_contour(params: VaseParameters, z_mm: float) -> np.ndarray:
    profiles = sorted(params.profiles, key=lambda p: p.z_ratio)
    z_positions = [p.z_ratio * params.height_mm for p in profiles]
    contours = [_build_profile_contour(p, params.radial_samples) for p in profiles]

    if z_mm <= z_positions[0]:
        contour = contours[0].copy()
        return _apply_texture_to_contour(contour, z_mm, params)

    if z_mm >= z_positions[-1]:
        contour = contours[-1].copy()
        return _apply_texture_to_contour(contour, z_mm, params)

    for i in range(len(z_positions) - 1):
        z1 = z_positions[i]
        z2 = z_positions[i + 1]
        if z1 <= z_mm <= z2:
            if z2 == z1:
                contour = contours[i].copy()
                return _apply_texture_to_contour(contour, z_mm, params)
            t = (z_mm - z1) / (z2 - z1)
            contour = _interpolate_contours(contours[i], contours[i + 1], t)
            return _apply_texture_to_contour(contour, z_mm, params)

    contour = contours[-1].copy()
    return _apply_texture_to_contour(contour, z_mm, params)


def _generate_support_safe_outer_contours(
    params: VaseParameters,
    z_values: np.ndarray,
) -> list[np.ndarray]:
    contours: list[np.ndarray] = []

    previous_contour: np.ndarray | None = None
    previous_z_mm: float | None = None

    for z_mm in z_values:
        contour = _interpolated_outer_contour(params, float(z_mm))

        if previous_contour is not None and previous_z_mm is not None:
            dz_mm = abs(float(z_mm) - previous_z_mm)
            max_radial_step_mm = _max_supportless_radial_step(dz_mm)
            contour = _limit_contour_step_from_previous(
                previous_contour=previous_contour,
                current_contour=contour,
                max_radial_step_mm=max_radial_step_mm,
                wall_thickness_mm=params.wall_thickness_mm,
            )

        contours.append(contour)
        previous_contour = contour
        previous_z_mm = float(z_mm)

    return contours


def _compute_inner_contour(
    outer_contour: np.ndarray,
    wall_thickness_mm: float,
) -> np.ndarray:
    result = []
    for pt in outer_contour:
        norm = np.linalg.norm(pt)
        if norm <= wall_thickness_mm:
            raise ValueError(
                "Une section intérieure devient invalide : "
                "réduire l'épaisseur ou augmenter le diamètre."
            )

        direction = pt / norm
        inner_pt = pt - direction * wall_thickness_mm
        result.append(inner_pt)

    return np.asarray(result, dtype=float)


def _append_ring_vertices(vertices: list, contour: np.ndarray, z_mm: float) -> None:
    for pt in contour:
        vertices.append([float(pt[0]), float(pt[1]), float(z_mm)])


def _add_quad_strip_faces(
    faces: list,
    start_ring_a: int,
    start_ring_b: int,
    ring_size: int,
    flip: bool = False,
) -> None:
    for i in range(ring_size):
        a = start_ring_a + i
        b = start_ring_a + (i + 1) % ring_size
        c = start_ring_b + i
        d = start_ring_b + (i + 1) % ring_size

        if not flip:
            faces.append([a, b, c])
            faces.append([b, d, c])
        else:
            faces.append([a, c, b])
            faces.append([b, c, d])

def _add_bottom_cap_faces(
    faces: list,
    center_index: int,
    ring_start: int,
    ring_size: int,
    invert: bool = False,
) -> None:
    for i in range(ring_size):
        a = ring_start + i
        b = ring_start + (i + 1) % ring_size
        if not invert:
            faces.append([center_index, b, a])
        else:
            faces.append([center_index, a, b])

def _add_ring_bridge_faces(
    faces: list,
    outer_ring_start: int,
    inner_ring_start: int,
    ring_size: int,
    invert: bool = False,
) -> None:
    for i in range(ring_size):
        o0 = outer_ring_start + i
        o1 = outer_ring_start + (i + 1) % ring_size
        i0 = inner_ring_start + i
        i1 = inner_ring_start + (i + 1) % ring_size

        if not invert:
            faces.append([o0, o1, i0])
            faces.append([o1, i1, i0])
        else:
            faces.append([o0, i0, o1])
            faces.append([o1, i0, i1])

def generate_vase_mesh(params: VaseParameters):
    _validate_params(params)

    vertices = []
    faces = []

    ring_size = params.radial_samples
    layers = params.vertical_samples

    z_outer = np.linspace(0.0, params.height_mm, layers)
    z_inner_bottom = min(params.bottom_thickness_mm, params.height_mm)
    z_inner = np.linspace(z_inner_bottom, params.height_mm, layers)

    outer_ring_starts = []
    inner_ring_starts = []

    outer_contours = _generate_support_safe_outer_contours(params, z_outer)
    inner_source_contours = _generate_support_safe_outer_contours(params, z_inner)

    # ---------------------------
    # Paroi extérieure
    # ---------------------------
    for z_mm, contour in zip(z_outer, outer_contours):
        ring_start = len(vertices)
        _append_ring_vertices(vertices, contour, z_mm)
        outer_ring_starts.append(ring_start)

    # ---------------------------
    # Paroi intérieure
    # ---------------------------
    for z_mm, outer_contour in zip(z_inner, inner_source_contours):
        inner_contour = _compute_inner_contour(outer_contour, params.wall_thickness_mm)
        ring_start = len(vertices)
        _append_ring_vertices(vertices, inner_contour, z_mm)
        inner_ring_starts.append(ring_start)

    # ---------------------------
    # Faces paroi extérieure
    # ---------------------------
    for layer in range(layers - 1):
        _add_quad_strip_faces(
            faces,
            outer_ring_starts[layer],
            outer_ring_starts[layer + 1],
            ring_size,
            flip=False,
        )

    # ---------------------------
    # Faces paroi intérieure
    # ---------------------------
    for layer in range(layers - 1):
        _add_quad_strip_faces(
            faces,
            inner_ring_starts[layer],
            inner_ring_starts[layer + 1],
            ring_size,
            flip=True,
        )

    # ---------------------------
    # Fermeture de la lèvre haute
    # ---------------------------
    outer_top_ring = outer_ring_starts[-1]
    inner_top_ring = inner_ring_starts[-1]
    _add_ring_bridge_faces(
        faces,
        outer_top_ring,
        inner_top_ring,
        ring_size,
        invert=False,
    )

    # ---------------------------
    # Fermeture du fond
    # ---------------------------
    if params.close_bottom:
        # Dessous extérieur du vase à z = 0
        outer_bottom_ring = outer_ring_starts[0]
        outer_center_index = len(vertices)
        vertices.append([0.0, 0.0, 0.0])

        _add_bottom_cap_faces(
            faces,
            outer_center_index,
            outer_bottom_ring,
            ring_size,
            invert=False,
        )

        # Dessus du fond intérieur à z = bottom_thickness
        inner_bottom_ring = inner_ring_starts[0]
        inner_floor_center_index = len(vertices)
        vertices.append([0.0, 0.0, float(z_inner_bottom)])

        _add_bottom_cap_faces(
            faces,
            inner_floor_center_index,
            inner_bottom_ring,
            ring_size,
            invert=True,
        )

    vertices = np.asarray(vertices, dtype=float)
    faces = np.asarray(faces, dtype=int)

    return vertices, faces


def generate_outer_profile_points(
    params: VaseParameters,
    samples_z: int = 200,
) -> tuple[np.ndarray, np.ndarray]:
    _validate_params(params)

    z_values = np.linspace(0.0, params.height_mm, samples_z)
    contours = _generate_support_safe_outer_contours(params, z_values)

    radius_values = []
    for contour in contours:
        radii = np.linalg.norm(contour, axis=1)
        radius_values.append(float(np.max(radii)))

    return z_values, np.asarray(radius_values, dtype=float)


def generate_top_outer_contour(params: VaseParameters) -> np.ndarray:
    _validate_params(params)

    z_values = np.linspace(0.0, params.height_mm, max(2, params.vertical_samples))
    contours = _generate_support_safe_outer_contours(params, z_values)
    return contours[-1].copy()
    