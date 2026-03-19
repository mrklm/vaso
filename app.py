from pathlib import Path
from datetime import datetime
import json
import os
import random
import sys
import tkinter as tk
import numpy as np
from tkinter import ttk, messagebox, filedialog, scrolledtext, simpledialog


from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from matplotlib import colors as mcolors
from mpl_toolkits.mplot3d.art3d import Poly3DCollection


from model import Profile, VaseParameters
from generator import (
    generate_vase_mesh,
    generate_outer_profile_points,
    generate_top_outer_contour,
)
from exporter import export_stl

APP_VERSION = "1.0.13"
APP_NAME = "Vaso"
SETTINGS_FILE = "vaso_settings.json"


THEMES = {
    # ===== Thèmes sombres (sobres / quotidiens) =====
    "[Sombre] Midnight Garage": dict(
        BG="#151515", PANEL="#1F1F1F", FIELD="#2A2A2A",
        FG="#EAEAEA", FIELD_FG="#F0F0F0", ACCENT="#FF9800"
    ),
    "[Sombre] AIR-KLM Night flight": dict(
        BG="#0B1E2D", PANEL="#102A3D", FIELD="#16384F",
        FG="#EAF6FF", FIELD_FG="#FFFFFF", ACCENT="#00A1DE"
    ),
    "[Sombre] Café Serré": dict(
        BG="#1B120C", PANEL="#2A1C14", FIELD="#3A281D",
        FG="#F2E6D8", FIELD_FG="#FFF4E6", ACCENT="#C28E5C"
    ),
    "[Sombre] Matrix Déjà Vu": dict(
        BG="#000A00", PANEL="#001F00", FIELD="#003300",
        FG="#00FF66", FIELD_FG="#66FF99", ACCENT="#00FF00"
    ),
    "[Sombre] Miami Vice 1987": dict(
        BG="#14002E", PANEL="#2B0057", FIELD="#004D4D",
        FG="#FFF0FF", FIELD_FG="#FFFFFF", ACCENT="#00FFD5"
    ),
    "[Sombre] Cyber Licorne": dict(
        BG="#1A0026", PANEL="#2E004F", FIELD="#3D0066",
        FG="#F6E7FF", FIELD_FG="#FFFFFF", ACCENT="#FF2CF7"
    ),
    # ===== Thèmes clairs =====
    "[Clair] AIR-KLM Day flight": dict(
        BG="#EAF6FF", PANEL="#D6EEF9", FIELD="#FFFFFF",
        FG="#0B2A3F", FIELD_FG="#0B2A3F", ACCENT="#00A1DE"
    ),
    "[Clair] Matin Brumeux": dict(
        BG="#E6E7E8", PANEL="#D4D7DB", FIELD="#FFFFFF",
        FG="#1E1F22", FIELD_FG="#1E1F22", ACCENT="#6B7C93"
    ),
    "[Clair] Latte Vanille": dict(
        BG="#FAF6F1", PANEL="#EFE6DC", FIELD="#FFFFFF",
        FG="#3D2E22", FIELD_FG="#3D2E22", ACCENT="#D8B892"
    ),
    "[Clair] Miellerie La Divette": dict(
        BG="#E6B65C", PANEL="#F5E6CC", FIELD="#FFFFFF",
        FG="#50371A", FIELD_FG="#50371A", ACCENT="#F2B705"
    ),
    # ===== Thèmes Pouêt-Pouêt =====
    "[Pouêt] Chewing-gum Océan": dict(
        BG="#00A6C8", PANEL="#0083A1", FIELD="#00C7B7",
        FG="#082026", FIELD_FG="#082026", ACCENT="#FF4FD8"
    ),
    "[Pouêt] Pamplemousse": dict(
        BG="#FF4A1C", PANEL="#E63B10", FIELD="#FF7A00",
        FG="#1A0B00", FIELD_FG="#1A0B00", ACCENT="#00E5FF"
    ),
    "[Pouêt] Raisin Toxique": dict(
        BG="#7A00FF", PANEL="#5B00C9", FIELD="#B000FF",
        FG="#0F001A", FIELD_FG="#0F001A", ACCENT="#39FF14"
    ),
    "[Pouêt] Citron qui pique": dict(
        BG="#FFF200", PANEL="#E6D800", FIELD="#FFF7A6",
        FG="#1A1A00", FIELD_FG="#1A1A00", ACCENT="#0066FF"
    ),
    "[Pouêt] Barbie Apocalypse": dict(
        BG="#FF1493", PANEL="#004D40", FIELD="#1B5E20",
        FG="#E8FFF8", FIELD_FG="#FFFFFF", ACCENT="#FFEB3B"
    ),
    "[Pouêt] Compagnie Créole": dict(
        BG="#8B3A1A", PANEL="#F2C94C", FIELD="#FFFFFF",
        FG="#5A2E0C", FIELD_FG="#5A2E0C", ACCENT="#8B3A1A"
    ),
}

DEFAULT_PRINTER_PROFILES = [
    {"name": "Profil par défaut", "width": 220.0, "depth": 220.0, "height": 250.0},
    {"name": "Ender 5 Pro", "width": 220.0, "depth": 220.0, "height": 300.0},
    {"name": "Bambu A1 Mini", "width": 180.0, "depth": 180.0, "height": 180.0},
]

RANDOM_STYLE_NAMES = [
    "Pur aléatoire",
    "Forme douce",
    "Forme brute",
    "Forme torsadée",
    "Architecturée",
    "Organique",
    "Fuselée",
    "Bulbeuse",
]

RANDOM_STYLE_RULES = {
    "Pur aléatoire": {
        "profiles": "2-10",
        "diam_delta": "X",
        "sides": "3-12",
        "rot": "0-90",
        "shape": "X",
    },
    "Forme douce": {
        "profiles": "5-10",
        "diam_delta": "4-12",
        "sides": "5-9",
        "rot": "0-28",
        "shape": "douce",
    },
    "Forme brute": {
        "profiles": "3-8",
        "diam_delta": "18-42",
        "sides": "3-12",
        "rot": "0-90",
        "shape": "brute",
    },
    "Forme torsadée": {
        "profiles": "5-10",
        "diam_delta": "6-16",
        "sides": "4-8",
        "rot": "12-90",
        "shape": "torsade",
    },
    "Architecturée": {
        "profiles": "3-6",
        "diam_delta": "10-24",
        "sides": "4-8",
        "rot": "0-24",
        "shape": "geo",
    },
    "Organique": {
        "profiles": "6-10",
        "diam_delta": "8-18",
        "sides": "5-9",
        "rot": "0-36",
        "shape": "orga",
    },
    "Fuselée": {
        "profiles": "4-8",
        "diam_delta": "6-18",
        "sides": "4-8",
        "rot": "0-30",
        "shape": "fusee",
    },
    "Bulbeuse": {
        "profiles": "4-8",
        "diam_delta": "10-28",
        "sides": "4-9",
        "rot": "0-32",
        "shape": "bulbe",
    },
}

TEXTURE_TYPE_NAMES = [
    "Pas de texture",
    "Cannelures",
    "Anneaux",
    "Spirale",
    "Double spirale",
    "Triple spirale",
    "Bulles",
    "Hexagones",
    "LowPoly",
    "Martelé",
    "Écailles",
    "Diamants",
    "Tressage",
    "Vagues",
]

TEXTURE_ZOOM_NAMES = [
    "Très fin",
    "Fin",
    "Moyen",
    "Gros",
    "Très gros",
]

TEXTURE_MODE_NAMES = [
    "Pas de texture",
    "Texture aléatoire",
    "Texture imposée",
    "Double texture",
    "Double texture aléatoire",
]

PREVIEW_3D_MODE_NAMES = [
    "Normal",
    "Relief renforcé",
]

RANDOM_COMPLEXITY_NAMES = [
    "Sobre",
    "Moyen",
    "Complexe",
]

RANDOM_COMPLEXITY_RULES = {
    "Sobre": {
        "height_ratio_min": 0.34,
        "height_ratio_mode": 0.50,
        "height_ratio_max": 0.72,
        "profile_min": 2,
        "profile_mode": 3,
        "profile_max": 5,
    },
    "Moyen": {
        "height_ratio_min": 0.46,
        "height_ratio_mode": 0.63,
        "height_ratio_max": 0.84,
        "profile_min": 4,
        "profile_mode": 5,
        "profile_max": 7,
    },
    "Complexe": {
        "height_ratio_min": 0.58,
        "height_ratio_mode": 0.76,
        "height_ratio_max": 0.96,
        "profile_min": 6,
        "profile_mode": 7,
        "profile_max": 10,
    },
}


def get_user_settings_dir() -> Path:
    if sys.platform == "win32":
        appdata = os.environ.get("APPDATA")
        if appdata:
            return Path(appdata) / APP_NAME
        return Path.home() / "AppData" / "Roaming" / APP_NAME

    if sys.platform == "darwin":
        return Path.home() / "Library" / "Application Support" / APP_NAME

    xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
    if xdg_config_home:
        return Path(xdg_config_home) / APP_NAME

    return Path.home() / ".config" / APP_NAME


def get_legacy_settings_path(base_dir: Path) -> Path:
    return base_dir / SETTINGS_FILE


def get_settings_path(base_dir: Path) -> Path:
    return get_user_settings_dir() / SETTINGS_FILE


def load_settings(base_dir: Path) -> dict:
    settings_candidates = [
        get_settings_path(base_dir),
        get_legacy_settings_path(base_dir),
    ]

    for settings_path in settings_candidates:
        if not settings_path.exists():
            continue

        try:
            data = json.loads(settings_path.read_text(encoding="utf-8"))
        except Exception:
            continue

        if isinstance(data, dict):
            return data

    return {}


def save_settings(base_dir: Path, payload: dict) -> None:
    settings_dir = get_user_settings_dir()
    settings_dir.mkdir(parents=True, exist_ok=True)

    settings_path = settings_dir / SETTINGS_FILE
    settings_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


def _normalize_printer_profiles(raw_profiles) -> list[dict]:
    profiles: list[dict] = []

    if isinstance(raw_profiles, list):
        for item in raw_profiles:
            if not isinstance(item, dict):
                continue

            name = item.get("name")
            width = item.get("width")
            depth = item.get("depth")
            height = item.get("height")

            if not isinstance(name, str) or not name.strip():
                continue

            try:
                width = float(width)
                depth = float(depth)
                height = float(height)
            except Exception:
                continue

            if width <= 0 or depth <= 0 or height <= 0:
                continue

            profiles.append(
                {
                    "name": name.strip(),
                    "width": width,
                    "depth": depth,
                    "height": height,
                }
            )

    if not profiles:
        profiles = [dict(profile) for profile in DEFAULT_PRINTER_PROFILES]

    return profiles


def load_saved_theme(base_dir: Path) -> str | None:
    data = load_settings(base_dir)
    theme_name = data.get("theme")
    if isinstance(theme_name, str) and theme_name in THEMES:
        return theme_name
    return None


def save_selected_theme(base_dir: Path, theme_name: str) -> None:
    data = load_settings(base_dir)
    data["theme"] = theme_name
    save_settings(base_dir, data)


def load_printer_profiles(base_dir: Path) -> tuple[list[dict], str]:
    data = load_settings(base_dir)

    profiles = _normalize_printer_profiles(data.get("printer_profiles"))
    profile_names = [profile["name"] for profile in profiles]

    active_name = data.get("active_printer_profile")
    if not isinstance(active_name, str) or active_name not in profile_names:
        active_name = profiles[0]["name"]

    return profiles, active_name


def save_printer_profiles(base_dir: Path, profiles: list[dict], active_name: str) -> None:
    data = load_settings(base_dir)
    data["printer_profiles"] = profiles
    data["active_printer_profile"] = active_name
    save_settings(base_dir, data)


def get_desktop_dir() -> Path:
    home = Path.home()
    desktop = home / "Desktop"
    if desktop.exists() and desktop.is_dir():
        return desktop
    return home


def get_default_export_dir() -> Path:
    today = datetime.now().strftime("%y-%m-%d")
    return get_desktop_dir() / f"Vaso-{today}"


def get_next_export_path(export_dir: Path) -> Path:
    export_dir.mkdir(parents=True, exist_ok=True)

    index = 0
    while True:
        candidate = export_dir / f"vaso_export_{index}.stl"
        if not candidate.exists():
            return candidate
        index += 1


def get_random_style_rules(style_name: str) -> dict:
    return RANDOM_STYLE_RULES.get(style_name, RANDOM_STYLE_RULES["Pur aléatoire"])


def load_help_text(base_dir: Path) -> str:
    help_path = base_dir / "assets" / "aide.md"
    if help_path.exists():
        try:
            return help_path.read_text(encoding="utf-8")
        except Exception as exc:
            return f"Impossible de lire le fichier d'aide :\n{exc}"
    return (
        "Fichier d'aide introuvable.\n\n"
        "Créez le fichier : assets/aide.md\n"
        "pour afficher l'aide dans cet onglet."
    )

def render_markdown_into_text(widget: scrolledtext.ScrolledText, markdown_text: str) -> None:
    widget.configure(state="normal")
    widget.delete("1.0", "end")

    for line in markdown_text.splitlines(keepends=True):
        if line.startswith("### "):
            widget.insert("end", line[4:], ("h3",))
        elif line.startswith("## "):
            widget.insert("end", line[3:], ("h2",))
        elif line.startswith("# "):
            widget.insert("end", line[2:], ("h1",))
        elif line.startswith("- "):
            widget.insert("end", f"• {line[2:]}", ("bullet",))
        else:
            widget.insert("end", line, ("body",))

    widget.configure(state="disabled")    


def _build_profiles_from_explicit_ui(
    profile_count: int,
    profile_enabled_vars: list[tk.BooleanVar],
    z_ratio_vars: list[tk.StringVar],
    diameter_vars: list[tk.StringVar],
    sides_vars: list[tk.StringVar],
    rotation_vars: list[tk.StringVar],
) -> list[Profile]:
    if profile_count < 2 or profile_count > 10:
        raise ValueError("Le nombre de profils doit être compris entre 2 et 10.")

    active_indices = [0]

    for i in range(1, profile_count - 1):
        if profile_enabled_vars[i].get():
            active_indices.append(i)

    active_indices.append(profile_count - 1)

    profiles: list[Profile] = []
    previous_z_ratio = -1.0

    for ui_index in active_indices:
        z_ratio = float(z_ratio_vars[ui_index].get()) / 100.0
        diameter = float(diameter_vars[ui_index].get())
        sides = int(sides_vars[ui_index].get())
        rotation_deg = float(rotation_vars[ui_index].get())

        if not (0.0 <= z_ratio <= 1.0):
            raise ValueError(
                f"Le profil {ui_index + 1} doit avoir une hauteur comprise entre 0 et 100 %."
            )

        if diameter <= 0:
            raise ValueError(f"Le diamètre du profil {ui_index + 1} doit être > 0.")

        if sides < 3:
            raise ValueError(f"Le nombre de côtés du profil {ui_index + 1} doit être >= 3.")

        if z_ratio <= previous_z_ratio:
            raise ValueError(
                f"Les hauteurs de profils doivent être strictement croissantes (profil {ui_index + 1})."
            )

        previous_z_ratio = z_ratio

        profiles.append(
            Profile(
                z_ratio=z_ratio,
                diameter=diameter,
                sides=sides,
                rotation_deg=rotation_deg,
                offset_x=0.0,
                offset_y=0.0,
            )
        )

    if len(profiles) < 2:
        raise ValueError("Il faut au minimum 2 profils actifs.")

    if abs(profiles[0].z_ratio - 0.0) > 1e-9:
        raise ValueError("Le profil 1 = 0 %.")

    if abs(profiles[-1].z_ratio - 1.0) > 1e-9:
        raise ValueError("Le dernier profil = 100 %.")

    return profiles


def build_params_from_ui(
    height_var: tk.StringVar,
    wall_var: tk.StringVar,
    bottom_var: tk.StringVar,
    radial_var: tk.StringVar,
    vertical_var: tk.StringVar,
    profile_count_var: tk.StringVar,
    profile_enabled_vars: list[tk.BooleanVar],
    z_ratio_vars: list[tk.StringVar],
    diameter_vars: list[tk.StringVar],
    sides_vars: list[tk.StringVar],
    rotation_vars: list[tk.StringVar],
) -> VaseParameters:
    params = VaseParameters(
        height_mm=float(height_var.get()),
        wall_thickness_mm=float(wall_var.get()),
        bottom_thickness_mm=float(bottom_var.get()),
        radial_samples=int(radial_var.get()),
        vertical_samples=int(vertical_var.get()),
        open_top=True,
        close_bottom=True,
    )

    profile_count = int(profile_count_var.get())
    if profile_count < 2 or profile_count > 10:
        raise ValueError("Le nombre de profils doit être compris entre 2 et 10.")

    params.profiles = _build_profiles_from_explicit_ui(
        profile_count=profile_count,
        profile_enabled_vars=profile_enabled_vars,
        z_ratio_vars=z_ratio_vars,
        diameter_vars=diameter_vars,
        sides_vars=sides_vars,
        rotation_vars=rotation_vars,
    )

    return params


def build_preview_params(params: VaseParameters) -> VaseParameters:
    preview_params = VaseParameters(
        height_mm=params.height_mm,
        wall_thickness_mm=params.wall_thickness_mm,
        bottom_thickness_mm=params.bottom_thickness_mm,
        radial_samples=min(params.radial_samples, 72),
        vertical_samples=min(params.vertical_samples, 96),
        open_top=params.open_top,
        close_bottom=params.close_bottom,
        texture_mode=params.texture_mode,
        texture_type=params.texture_type,
        texture_zoom=params.texture_zoom,
        texture_type_2=params.texture_type_2,
        texture_zoom_2=params.texture_zoom_2,
        profiles=[
            Profile(
                z_ratio=p.z_ratio,
                diameter=p.diameter,
                sides=p.sides,
                rotation_deg=p.rotation_deg,
                scale_x=p.scale_x,
                scale_y=p.scale_y,
                offset_x=p.offset_x,
                offset_y=p.offset_y,
            )
            for p in params.profiles
        ],
    )
    return preview_params


def apply_theme(
    root: tk.Tk,
    style: ttk.Style,
    theme_name: str,
    figure_side: Figure,
    figure_top: Figure,
    ax_side,
    ax_top,
    canvas_side: FigureCanvasTkAgg,
    canvas_top: FigureCanvasTkAgg,
    help_text_widget: scrolledtext.ScrolledText,
) -> None:

    colors = THEMES[theme_name]

    bg = colors["BG"]
    panel = colors["PANEL"]
    field = colors["FIELD"]
    fg = colors["FG"]
    field_fg = colors["FIELD_FG"]
    accent = colors["ACCENT"]

    root.configure(bg=bg)

    style.theme_use("clam")

    style.configure("Vaso.TFrame", background=bg)

    style.configure(
        "Vaso.TLabel",
        background=bg,
        foreground=fg,
    )

    style.configure(
        "Vaso.TLabelframe",
        background=panel,
        bordercolor=accent,
        relief="solid",
    )
    style.configure(
        "Vaso.TLabelframe.Label",
        background=bg,
        foreground=accent,
        font=("Segoe UI", 10, "bold"),
    )

    style.configure(
        "Vaso.TEntry",
        fieldbackground=field,
        foreground=field_fg,
        bordercolor=accent,
        insertcolor=field_fg,
        padding=4,
    )
    style.map(
        "Vaso.TEntry",
        fieldbackground=[("disabled", field)],
        foreground=[("disabled", field_fg)],
    )

    style.configure(
        "Vaso.TCombobox",
        fieldbackground=field,
        background=field,
        foreground=field_fg,
        arrowcolor=accent,
        bordercolor=accent,
        padding=4,
    )
    style.map(
        "Vaso.TCombobox",
        fieldbackground=[("readonly", field)],
        foreground=[("readonly", field_fg)],
        selectbackground=[("readonly", field)],
        selectforeground=[("readonly", field_fg)],
    )

    style.configure(
        "Vaso.TButton",
        background=panel,
        foreground=fg,
        bordercolor=accent,
        focusthickness=1,
        focuscolor=accent,
        padding=6,
    )

    style.configure(
        "Vaso.TCheckbutton",
        background=bg,
        foreground=fg,
    )
    style.map(
        "Vaso.TCheckbutton",
        background=[("active", bg)],
        foreground=[("active", fg)],
    )

    style.map(
        "Vaso.TButton",
        background=[("active", accent), ("pressed", accent)],
        foreground=[("active", bg), ("pressed", bg)],
    )

    style.configure(
        "Vaso.TNotebook",
        background=bg,
        borderwidth=0,
    )
    style.configure(
        "Vaso.TNotebook.Tab",
        background=panel,
        foreground=fg,
        padding=(12, 6),
    )
    style.map(
        "Vaso.TNotebook.Tab",
        background=[("selected", accent)],
        foreground=[("selected", bg)],
    )

    figure_side.patch.set_facecolor(panel)
    figure_top.patch.set_facecolor(panel)

    for ax in (ax_side, ax_top):
        ax.set_facecolor(field)
        ax.tick_params(colors=fg)
        ax.xaxis.label.set_color(fg)
        ax.yaxis.label.set_color(fg)
        ax.title.set_color(accent)
        ax.grid(True, color=accent, alpha=0.25)
        for spine in ax.spines.values():
            spine.set_color(accent)

    help_text_widget.configure(
        bg=field,
        fg=field_fg,
        insertbackground=field_fg,
        selectbackground=accent,
        selectforeground=bg,
    )

    help_text_widget.tag_configure("body", foreground=field_fg)
    help_text_widget.tag_configure("h1", foreground=accent)
    help_text_widget.tag_configure("h2", foreground=accent)
    help_text_widget.tag_configure("h3", foreground=accent)
    help_text_widget.tag_configure("bullet", foreground=field_fg)

    canvas_side.draw_idle()
    canvas_top.draw_idle()

def apply_theme_to_3d_axes(ax_3d, theme_name: str) -> None:
    colors = THEMES[theme_name]

    field = colors["FIELD"]
    fg = colors["FG"]
    accent = colors["ACCENT"]

    ax_3d.set_facecolor(field)

    ax_3d.set_xlabel("X", color=fg, fontsize=9, labelpad=6)
    ax_3d.set_ylabel("Y", color=fg, fontsize=9, labelpad=6)
    ax_3d.set_zlabel("Z", color=fg, fontsize=9, labelpad=6)

    ax_3d.tick_params(colors=fg, labelsize=8, pad=1)

    try:
        ax_3d.xaxis.pane.set_facecolor(field)
        ax_3d.yaxis.pane.set_facecolor(field)
        ax_3d.zaxis.pane.set_facecolor(field)

        ax_3d.xaxis.pane.set_edgecolor(accent)
        ax_3d.yaxis.pane.set_edgecolor(accent)
        ax_3d.zaxis.pane.set_edgecolor(accent)
    except Exception:
        pass

    try:
        ax_3d.xaxis.line.set_color(accent)
        ax_3d.yaxis.line.set_color(accent)
        ax_3d.zaxis.line.set_color(accent)
    except Exception:
        pass

    ax_3d.grid(False)

    ax_3d.set_xticks([])
    ax_3d.set_yticks([])
    ax_3d.set_zticks([])


def build_shaded_facecolors(
    triangles: np.ndarray,
    base_hex_color: str,
    shading_strength: float,
    light_dir: tuple[float, float, float] = (-0.9, -1.0, 1.8),
    ambient: float = 0.16,
    alpha: float = 0.98,
    specular_strength: float = 0.22,
    rim_strength: float = 0.18,
    contrast_center: float = 0.72,
    contrast_gain: float = 1.55,
) -> np.ndarray:
    base_rgb = np.array(mcolors.to_rgb(base_hex_color), dtype=float)

    light = np.array(light_dir, dtype=float)
    light_norm = np.linalg.norm(light)
    if light_norm == 0:
        light = np.array([0.0, 0.0, 1.0], dtype=float)
    else:
        light = light / light_norm

    view_dir = np.array([0.0, 0.0, 1.0], dtype=float)

    v1 = triangles[:, 1, :] - triangles[:, 0, :]
    v2 = triangles[:, 2, :] - triangles[:, 0, :]
    normals = np.cross(v1, v2)

    normal_norms = np.linalg.norm(normals, axis=1, keepdims=True)
    normal_norms[normal_norms == 0] = 1.0
    normals = normals / normal_norms

    diffuse = np.clip(np.sum(normals * light, axis=1), 0.0, 1.0)

    half_vec = light + view_dir
    half_norm = np.linalg.norm(half_vec)
    if half_norm == 0:
        half_vec = np.array([0.0, 0.0, 1.0], dtype=float)
    else:
        half_vec = half_vec / half_norm

    specular = np.clip(np.sum(normals * half_vec, axis=1), 0.0, 1.0) ** 18
    rim = (1.0 - np.clip(np.sum(normals * view_dir, axis=1), 0.0, 1.0)) ** 1.8

    lambert = np.clip(ambient + 0.92 * diffuse, 0.0, 1.0)
    lighting = np.clip(
        lambert + specular_strength * specular + rim_strength * rim,
        0.0,
        1.50,
    )

    shading_strength = float(np.clip(shading_strength, 0.0, 1.0))
    lighting = 1.0 + (lighting - 1.0) * shading_strength

    lighting = np.clip(
        contrast_center + (lighting - contrast_center) * contrast_gain,
        0.0,
        1.60,
    )

    face_rgb = np.clip(base_rgb[None, :] * lighting[:, None], 0.0, 1.0)

    facecolors = np.empty((len(triangles), 4), dtype=float)
    facecolors[:, :3] = face_rgb
    facecolors[:, 3] = alpha

    return facecolors


def get_preview_3d_render_config(mode_name: str) -> dict:
    if mode_name == "Relief renforcé":
        return {
            "light_dir": (-1.25, -1.35, 1.45),
            "ambient": 0.08,
            "alpha": 0.995,
            "specular_strength": 0.30,
            "rim_strength": 0.28,
            "contrast_center": 0.68,
            "contrast_gain": 1.95,
            "linewidths": 0.0,
            "edgecolors": "none",
            "antialiased": False,
            "view_elev": 26,
            "view_azim": 42,
            "status_label": "Relief renforcé",
        }

    return {
        "light_dir": (-0.9, -1.0, 1.8),
        "ambient": 0.16,
        "alpha": 0.98,
        "specular_strength": 0.22,
        "rim_strength": 0.18,
        "contrast_center": 0.72,
        "contrast_gain": 1.55,
        "linewidths": 0.0,
        "edgecolors": "none",
        "antialiased": False,
        "view_elev": 24,
        "view_azim": 38,
        "status_label": "Normal",
    }

def configure_main_window(root: tk.Tk) -> None:
    screen_w = max(800, int(root.winfo_screenwidth()))
    screen_h = max(600, int(root.winfo_screenheight()))

    target_w = min(1280, max(980, screen_w - 80))
    target_h = min(760, max(620, screen_h - 100))

    min_w = min(1160, target_w)
    min_h = min(700, target_h)

    root.geometry(f"{target_w}x{target_h}")
    root.minsize(min_w, min_h)
    root.maxsize(screen_w, screen_h)    


def main() -> None:
    root = tk.Tk()
    root.title(f"{APP_NAME} — v{APP_VERSION}")
    configure_main_window(root)

    base_dir = Path(__file__).resolve().parent
    ico_path = base_dir / "assets" / "vaso.ico"

    if ico_path.exists():
        try:
            root.iconbitmap(default=str(ico_path))
        except Exception as exc:
            print(f"Impossible de charger l'icône Windows : {exc}")
    else:
        print(f"Icône introuvable : {ico_path}")

    style = ttk.Style()

    main_frame = ttk.Frame(root, padding=16, style="Vaso.TFrame")
    main_frame.pack(fill="both", expand=True)

    theme_names = list(THEMES.keys())
    saved_theme = load_saved_theme(base_dir)
    startup_theme = saved_theme if saved_theme is not None else random.choice(theme_names)
    theme_var = tk.StringVar(value=startup_theme)

    printer_profiles, active_printer_profile_name = load_printer_profiles(base_dir)
    active_printer_profile = next(
        (profile for profile in printer_profiles if profile["name"] == active_printer_profile_name),
        printer_profiles[0],
    )

    status_var = tk.StringVar(value="Prêt.")
    export_path_var = tk.StringVar(value=str(get_default_export_dir()))
    seed_var = tk.StringVar(value="")
    random_style_var = tk.StringVar(value="Pur aléatoire")
    texture_mode_var = tk.StringVar(value="Pas de texture")
    texture_type_var = tk.StringVar(value="Cannelures")
    texture_zoom_var = tk.StringVar(value="Moyen")
    texture_type_2_var = tk.StringVar(value="Anneaux")
    texture_zoom_2_var = tk.StringVar(value="Moyen")
    preview_3d_mode_var = tk.StringVar(value="Normal")
    shading_var = tk.DoubleVar(value=68.0)
    shading_label_var = tk.StringVar(value="68 %")

    random_complexity_enabled_var = tk.BooleanVar(value=False)
    random_complexity_var = tk.StringVar(value="Moyen")

    printer_profile_var = tk.StringVar(value=active_printer_profile["name"])
    build_width_max_var = tk.StringVar(value=f'{active_printer_profile["width"]:.1f}'.rstrip("0").rstrip("."))
    build_depth_max_var = tk.StringVar(value=f'{active_printer_profile["depth"]:.1f}'.rstrip("0").rstrip("."))
    build_height_max_var = tk.StringVar(value=f'{active_printer_profile["height"]:.1f}'.rstrip("0").rstrip("."))

    height_var = tk.StringVar(value="180")
    wall_var = tk.StringVar(value="2.4")
    bottom_var = tk.StringVar(value="3.0")
    radial_var = tk.StringVar(value="96")
    vertical_var = tk.StringVar(value="120")
    profile_count_var = tk.StringVar(value="2")

    profile_enabled_vars = [
        tk.BooleanVar(value=True),
        tk.BooleanVar(value=True),
        tk.BooleanVar(value=False),
        tk.BooleanVar(value=False),
        tk.BooleanVar(value=False),
        tk.BooleanVar(value=False),
        tk.BooleanVar(value=False),
        tk.BooleanVar(value=False),
        tk.BooleanVar(value=False),
        tk.BooleanVar(value=False),
    ]

    z_ratio_vars = [
        tk.StringVar(value="0"),
        tk.StringVar(value="20"),
        tk.StringVar(value="35"),
        tk.StringVar(value="50"),
        tk.StringVar(value="62"),
        tk.StringVar(value="72"),
        tk.StringVar(value="80"),
        tk.StringVar(value="88"),
        tk.StringVar(value="94"),
        tk.StringVar(value="100"),
    ]

    diameter_vars = [
        tk.StringVar(value="40"),
        tk.StringVar(value="55"),
        tk.StringVar(value="72"),
        tk.StringVar(value="90"),
        tk.StringVar(value="82"),
        tk.StringVar(value="74"),
        tk.StringVar(value="66"),
        tk.StringVar(value="60"),
        tk.StringVar(value="55"),
        tk.StringVar(value="50"),
    ]

    sides_vars = [
        tk.StringVar(value="6"),
        tk.StringVar(value="6"),
        tk.StringVar(value="7"),
        tk.StringVar(value="8"),
        tk.StringVar(value="8"),
        tk.StringVar(value="8"),
        tk.StringVar(value="7"),
        tk.StringVar(value="7"),
        tk.StringVar(value="6"),
        tk.StringVar(value="6"),
    ]

    rotation_vars = [
        tk.StringVar(value="0"),
        tk.StringVar(value="4"),
        tk.StringVar(value="8"),
        tk.StringVar(value="15"),
        tk.StringVar(value="20"),
        tk.StringVar(value="24"),
        tk.StringVar(value="28"),
        tk.StringVar(value="30"),
        tk.StringVar(value="30"),
        tk.StringVar(value="30"),
    ]


    notebook = ttk.Notebook(main_frame, style="Vaso.TNotebook")
    notebook.grid(row=0, column=0, sticky="nsew")

    main_frame.columnconfigure(0, weight=1)
    main_frame.rowconfigure(0, weight=1)

    general_tab = ttk.Frame(notebook, style="Vaso.TFrame")
    options_tab = ttk.Frame(notebook, style="Vaso.TFrame")
    help_tab = ttk.Frame(notebook, style="Vaso.TFrame")

    notebook.add(general_tab, text="Général")
    notebook.add(options_tab, text="Options")
    notebook.add(help_tab, text="Aide")

    # Général
    general_tab.columnconfigure(0, weight=0)
    general_tab.columnconfigure(1, weight=1)
    general_tab.columnconfigure(2, weight=0)

    general_tab.rowconfigure(0, weight=1)
    general_tab.rowconfigure(1, weight=1)
    general_tab.rowconfigure(2, weight=0)

    left_panel_frame = ttk.LabelFrame(
        general_tab,
        text="Paramètres",
        padding=8,
        style="Vaso.TLabelframe",
    )
    left_panel_frame.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(0, 12), pady=(0, 12))

    left_panel_frame.columnconfigure(0, weight=1)
    left_panel_frame.rowconfigure(0, weight=1)

    left_notebook = ttk.Notebook(left_panel_frame, style="Vaso.TNotebook")
    left_notebook.grid(row=0, column=0, sticky="nsew")

    general_form_tab = ttk.Frame(left_notebook, style="Vaso.TFrame")
    shape_form_tab = ttk.Frame(left_notebook, style="Vaso.TFrame")

    left_notebook.add(general_form_tab, text="Paramètres généraux")
    left_notebook.add(shape_form_tab, text="Profils du vase")

    general_form_tab.columnconfigure(0, weight=0)
    general_form_tab.columnconfigure(1, weight=0)

    shape_form_tab.columnconfigure(0, weight=0)
    shape_form_tab.rowconfigure(0, weight=1)

    preview_3d_frame = ttk.LabelFrame(
        general_tab,
        text="Aperçu 3D",
        padding=12,
        style="Vaso.TLabelframe",
    )
    preview_3d_frame.grid(row=0, column=1, rowspan=2, sticky="nsew", padx=(0, 12), pady=(0, 12))

    side_preview_frame = ttk.LabelFrame(
        general_tab,
        text="Silhouette",
        padding=12,
        style="Vaso.TLabelframe",
    )
    side_preview_frame.grid(row=0, column=2, sticky="nsew", pady=(0, 12))

    top_preview_frame = ttk.LabelFrame(
        general_tab,
        text="Vue du haut",
        padding=12,
        style="Vaso.TLabelframe",
    )
    top_preview_frame.grid(row=1, column=2, sticky="nsew", pady=(0, 12))

    buttons_frame = ttk.Frame(general_tab, style="Vaso.TFrame")
    buttons_frame.grid(row=2, column=0, columnspan=3, sticky="ew", pady=(2, 0))

    buttons_frame.columnconfigure(0, weight=1)
    buttons_frame.columnconfigure(1, weight=0)
    buttons_frame.columnconfigure(2, weight=1)

    buttons_inner_frame = ttk.Frame(buttons_frame, style="Vaso.TFrame")
    buttons_inner_frame.grid(row=0, column=1)



    ttk.Label(general_form_tab, text="Hauteur (mm)", style="Vaso.TLabel").grid(row=0, column=0, sticky="w", pady=4)
    ttk.Entry(general_form_tab, textvariable=height_var, width=6, style="Vaso.TEntry").grid(row=0, column=1, sticky="w", pady=4)

    ttk.Label(general_form_tab, text="Épaisseur coque (mm)", style="Vaso.TLabel").grid(row=1, column=0, sticky="w", pady=4)
    ttk.Entry(general_form_tab, textvariable=wall_var, width=6, style="Vaso.TEntry").grid(row=1, column=1, sticky="w", pady=4)

    ttk.Label(general_form_tab, text="Épaisseur fond (mm)", style="Vaso.TLabel").grid(row=2, column=0, sticky="w", pady=4)
    ttk.Entry(general_form_tab, textvariable=bottom_var, width=6, style="Vaso.TEntry").grid(row=2, column=1, sticky="w", pady=4)

    ttk.Label(general_form_tab, text="Résolution circulaire", style="Vaso.TLabel").grid(row=3, column=0, sticky="w", pady=4)
    ttk.Entry(general_form_tab, textvariable=radial_var, width=6, style="Vaso.TEntry").grid(row=3, column=1, sticky="w", pady=4)

    ttk.Label(general_form_tab, text="Résolution verticale", style="Vaso.TLabel").grid(row=4, column=0, sticky="w", pady=4)
    ttk.Entry(general_form_tab, textvariable=vertical_var, width=6, style="Vaso.TEntry").grid(row=4, column=1, sticky="w", pady=4)

    ttk.Label(general_form_tab, text="Nombre de profils (2-10)", style="Vaso.TLabel").grid(row=5, column=0, sticky="w", pady=4)
    ttk.Entry(general_form_tab, textvariable=profile_count_var, width=6, style="Vaso.TEntry").grid(row=5, column=1, sticky="w", pady=4)

    ttk.Label(general_form_tab, text="Seed", style="Vaso.TLabel").grid(row=6, column=0, sticky="w", pady=4)
    ttk.Entry(general_form_tab, textvariable=seed_var, width=6, style="Vaso.TEntry").grid(row=6, column=1, sticky="w", pady=4)

    ttk.Label(general_form_tab, text="Style aléatoire", style="Vaso.TLabel").grid(row=7, column=0, sticky="w", pady=4)
    random_style_combo = ttk.Combobox(
        general_form_tab,
        textvariable=random_style_var,
        values=RANDOM_STYLE_NAMES,
        state="readonly",
        width=18,
        style="Vaso.TCombobox",
    )
    random_style_combo.grid(row=7, column=1, sticky="w", pady=4)

    ttk.Label(general_form_tab, text="Complexité", style="Vaso.TLabel").grid(row=8, column=0, sticky="w", pady=4)

    complexity_row_frame = ttk.Frame(general_form_tab, style="Vaso.TFrame")
    complexity_row_frame.grid(row=8, column=1, sticky="w", pady=4)

    random_complexity_check = ttk.Checkbutton(
        complexity_row_frame,
        variable=random_complexity_enabled_var,
        style="Vaso.TCheckbutton",
        command=lambda: update_random_complexity_state(),
    )
    random_complexity_check.grid(row=0, column=0, sticky="w", padx=(0, 6))

    random_complexity_combo = ttk.Combobox(
        complexity_row_frame,
        textvariable=random_complexity_var,
        values=RANDOM_COMPLEXITY_NAMES,
        state="readonly",
        width=15,
        style="Vaso.TCombobox",
    )
    random_complexity_combo.grid(row=0, column=1, sticky="w")

    ttk.Label(general_form_tab, text="Textures", style="Vaso.TLabel").grid(row=9, column=0, sticky="w", pady=4)
    texture_mode_combo = ttk.Combobox(
        general_form_tab,
        textvariable=texture_mode_var,
        values=TEXTURE_MODE_NAMES,
        state="readonly",
        width=18,
        style="Vaso.TCombobox",
    )
    texture_mode_combo.grid(row=9, column=1, sticky="w", pady=4)

    ttk.Label(general_form_tab, text="Texture / Zoom #1", style="Vaso.TLabel").grid(row=10, column=0, sticky="w", pady=4)

    texture_row_1_frame = ttk.Frame(general_form_tab, style="Vaso.TFrame")
    texture_row_1_frame.grid(row=10, column=1, sticky="w", pady=4)

    texture_type_combo = ttk.Combobox(
        texture_row_1_frame,
        textvariable=texture_type_var,
        values=TEXTURE_TYPE_NAMES,
        state="readonly",
        width=11,
        style="Vaso.TCombobox",
    )
    texture_type_combo.grid(row=0, column=0, sticky="w")

    texture_zoom_combo = ttk.Combobox(
        texture_row_1_frame,
        textvariable=texture_zoom_var,
        values=TEXTURE_ZOOM_NAMES,
        state="readonly",
        width=6,
        style="Vaso.TCombobox",
    )
    texture_zoom_combo.grid(row=0, column=1, sticky="w", padx=(8, 0))

    ttk.Label(general_form_tab, text="Texture / Zoom #2", style="Vaso.TLabel").grid(row=11, column=0, sticky="w", pady=4)

    texture_row_2_frame = ttk.Frame(general_form_tab, style="Vaso.TFrame")
    texture_row_2_frame.grid(row=11, column=1, sticky="w", pady=4)

    texture_type_2_combo = ttk.Combobox(
        texture_row_2_frame,
        textvariable=texture_type_2_var,
        values=TEXTURE_TYPE_NAMES,
        state="readonly",
        width=11,
        style="Vaso.TCombobox",
    )
    texture_type_2_combo.grid(row=0, column=0, sticky="w")

    texture_zoom_2_combo = ttk.Combobox(
        texture_row_2_frame,
        textvariable=texture_zoom_2_var,
        values=TEXTURE_ZOOM_NAMES,
        state="readonly",
        width=6,
        style="Vaso.TCombobox",
    )
    texture_zoom_2_combo.grid(row=0, column=1, sticky="w", padx=(8, 0))

    general_form_tab.columnconfigure(1, weight=0)
    general_form_tab.columnconfigure(1, minsize=0)

    profiles_table_frame = ttk.Frame(shape_form_tab, style="Vaso.TFrame")
    profiles_table_frame.grid(row=0, column=0, sticky="nw")

    ttk.Label(profiles_table_frame, text="Profil", style="Vaso.TLabel").grid(row=0, column=1, sticky="w", padx=(0, 8), pady=(0, 6))
    ttk.Label(profiles_table_frame, text="Hauteur (%)", style="Vaso.TLabel").grid(row=0, column=2, sticky="w", padx=4, pady=(0, 6))
    ttk.Label(profiles_table_frame, text="Diamètre (mm)", style="Vaso.TLabel").grid(row=0, column=3, sticky="w", padx=4, pady=(0, 6))
    ttk.Label(profiles_table_frame, text="Côtés", style="Vaso.TLabel").grid(row=0, column=4, sticky="w", padx=4, pady=(0, 6))
    ttk.Label(profiles_table_frame, text="Rotation (°)", style="Vaso.TLabel").grid(row=0, column=5, sticky="w", padx=4, pady=(0, 6))

    profile_enable_checks = []
    profile_row_labels = []
    profile_z_entries = []
    profile_diameter_entries = []
    profile_sides_entries = []
    profile_rotation_entries = []

    for i in range(10):
        row_index = i + 1

        enable_check = ttk.Checkbutton(
            profiles_table_frame,
            variable=profile_enabled_vars[i],
            style="Vaso.TCheckbutton",
            command=lambda idx=i: on_profile_enabled_change(idx),
        )
        enable_check.grid(row=row_index, column=0, sticky="w", padx=(0, 4), pady=3)
        profile_enable_checks.append(enable_check)

        row_label = ttk.Label(
            profiles_table_frame,
            text=f"P{i + 1}",
            style="Vaso.TLabel",
        )
        row_label.grid(row=row_index, column=1, sticky="w", padx=(0, 8), pady=3)
        profile_row_labels.append(row_label)

        z_entry = ttk.Entry(
            profiles_table_frame,
            textvariable=z_ratio_vars[i],
            width=4,
            style="Vaso.TEntry",
        )
        z_entry.grid(row=row_index, column=2, sticky="w", padx=4, pady=3)
        profile_z_entries.append(z_entry)

        diameter_entry = ttk.Entry(
            profiles_table_frame,
            textvariable=diameter_vars[i],
            width=5,
            style="Vaso.TEntry",
        )
        diameter_entry.grid(row=row_index, column=3, sticky="w", padx=4, pady=3)
        profile_diameter_entries.append(diameter_entry)

        sides_entry = ttk.Entry(
            profiles_table_frame,
            textvariable=sides_vars[i],
            width=4,
            style="Vaso.TEntry",
        )
        sides_entry.grid(row=row_index, column=4, sticky="w", padx=4, pady=3)
        profile_sides_entries.append(sides_entry)

        rotation_entry = ttk.Entry(
            profiles_table_frame,
            textvariable=rotation_vars[i],
            width=5,
            style="Vaso.TEntry",
        )
        rotation_entry.grid(row=row_index, column=5, sticky="w", padx=4, pady=3)
        profile_rotation_entries.append(rotation_entry)

    ttk.Label(
        shape_form_tab,
        text="Le profil 1 = à 0 % et le dernier profil = 100 %.",
        style="Vaso.TLabel",
        justify="left",
    ).grid(row=1, column=0, sticky="w", pady=(8, 2))

    ttk.Label(
        shape_form_tab,
        text="",
        style="Vaso.TLabel",
        justify="left",
    ).grid(row=2, column=0, sticky="w", pady=(0, 0))

    profiles_table_frame.columnconfigure(0, weight=0)
    profiles_table_frame.columnconfigure(1, weight=0)
    profiles_table_frame.columnconfigure(2, weight=0)
    profiles_table_frame.columnconfigure(3, weight=0)
    profiles_table_frame.columnconfigure(4, weight=0)
    profiles_table_frame.columnconfigure(5, weight=0)


    def update_profile_fields_state(*_args) -> None:
        try:
            active_count = int(profile_count_var.get())
        except Exception:
            active_count = 2

        clamped_count = max(2, min(10, active_count))
        active_count = clamped_count

        active_entries = (
            profile_z_entries,
            profile_diameter_entries,
            profile_sides_entries,
            profile_rotation_entries,
        )

        active_vars = (
            z_ratio_vars,
            diameter_vars,
            sides_vars,
            rotation_vars,
        )

        for i in range(10):
            profile_row_labels[i].configure(text=f"P{i + 1}")

            if i < active_count:
                if i == 0 or i == active_count - 1:
                    profile_enabled_vars[i].set(True)
                    profile_enable_checks[i].configure(state="disabled")
                    entry_state = "normal"
                else:
                    profile_enable_checks[i].configure(state="normal")
                    entry_state = "normal" if profile_enabled_vars[i].get() else "disabled"
            else:
                profile_enabled_vars[i].set(False)
                profile_enable_checks[i].configure(state="disabled")

                for vars_list in active_vars:
                    vars_list[i].set("X")

                entry_state = "disabled"

            for entry_list in active_entries:
                entry_list[i].configure(state=entry_state)

        z_ratio_vars[0].set("0")
        z_ratio_vars[active_count - 1].set("100")


    def normalize_active_profile_heights(active_count: int) -> None:
        if active_count < 2:
            return

        if active_count == 2:
            z_ratio_vars[0].set("0")
            z_ratio_vars[1].set("100")
            return

        step = 100.0 / float(active_count - 1)

        for i in range(active_count):
            value = int(round(i * step))

            if i == 0:
                value = 0
            elif i == active_count - 1:
                value = 100

            z_ratio_vars[i].set(str(value))


    def update_random_complexity_state() -> None:
        if random_complexity_enabled_var.get():
            random_complexity_combo.configure(state="readonly")
        else:
            random_complexity_combo.configure(state="disabled")

    def update_texture_mode_state() -> None:
        mode = texture_mode_var.get()

        if mode == "Pas de texture":
            texture_type_combo.configure(state="disabled")
            texture_zoom_combo.configure(state="disabled")
            texture_type_2_combo.configure(state="disabled")
            texture_zoom_2_combo.configure(state="disabled")

        elif mode == "Texture aléatoire":
            texture_type_combo.configure(state="disabled")
            texture_zoom_combo.configure(state="disabled")
            texture_type_2_combo.configure(state="disabled")
            texture_zoom_2_combo.configure(state="disabled")

        elif mode == "Texture imposée":
            texture_type_combo.configure(state="readonly")
            texture_zoom_combo.configure(state="readonly")
            texture_type_2_combo.configure(state="disabled")
            texture_zoom_2_combo.configure(state="disabled")

        elif mode == "Double texture":
            texture_type_combo.configure(state="readonly")
            texture_zoom_combo.configure(state="readonly")
            texture_type_2_combo.configure(state="readonly")
            texture_zoom_2_combo.configure(state="readonly")

        elif mode == "Double texture aléatoire":
            texture_type_combo.configure(state="disabled")
            texture_zoom_combo.configure(state="disabled")
            texture_type_2_combo.configure(state="disabled")
            texture_zoom_2_combo.configure(state="disabled")

        else:
            texture_type_combo.configure(state="disabled")
            texture_zoom_combo.configure(state="disabled")
            texture_type_2_combo.configure(state="disabled")
            texture_zoom_2_combo.configure(state="disabled")

    def on_texture_controls_change(event=None) -> None:
        try:
            update_texture_mode_state()
            params = build_current_params()
            draw_preview(params)
            status_var.set(
                f"Mode textures : {texture_mode_var.get()}."
            )
        except Exception:
            pass

    def on_preview_3d_mode_change(event=None) -> None:
        try:
            params = build_current_params()
            draw_preview(params)
            status_var.set(f"Mode 3D : {preview_3d_mode_var.get()}.")
        except Exception:
            pass
        
    def on_shading_change(value: str) -> None:
        try:
            shading_percent = float(value)
            shading_label_var.set(f"{int(round(shading_percent))} %")

            params = build_current_params()
            draw_preview(params)
            status_var.set("Shading 3D mis à jour.")
        except Exception:
            pass    

    def on_profile_enabled_change(_index: int) -> None:
        try:
            update_profile_fields_state()
            params = build_current_params()
            draw_preview(params)
            status_var.set("Profils actifs mis à jour.")
        except Exception:
            update_profile_fields_state()

    last_profile_count = {"value": 2}

    def on_profile_count_change(*_args) -> None:
        try:
            raw_value = profile_count_var.get().strip()
            if raw_value == "":
                update_profile_fields_state()
                return

            new_count = int(raw_value)
        except Exception:
            update_profile_fields_state()
            return

        new_count = max(2, min(10, new_count))
        old_count = last_profile_count["value"]

        update_profile_fields_state()

        if new_count != old_count:
            normalize_active_profile_heights(new_count)
            last_profile_count["value"] = new_count

    profile_count_var.trace_add("write", on_profile_count_change)

    preview_3d_controls = ttk.Frame(preview_3d_frame, style="Vaso.TFrame")
    preview_3d_controls.pack(fill="x", pady=(0, 8))

    preview_3d_mode_row = ttk.Frame(preview_3d_controls, style="Vaso.TFrame")
    preview_3d_mode_row.pack(fill="x", pady=(0, 6))

    ttk.Label(preview_3d_mode_row, text="Mode 3D", style="Vaso.TLabel").pack(side="left")

    preview_3d_mode_combo = ttk.Combobox(
        preview_3d_mode_row,
        textvariable=preview_3d_mode_var,
        values=PREVIEW_3D_MODE_NAMES,
        state="readonly",
        width=18,
        style="Vaso.TCombobox",
    )
    preview_3d_mode_combo.pack(side="left", padx=(8, 0))

    preview_3d_shading_row = ttk.Frame(preview_3d_controls, style="Vaso.TFrame")
    preview_3d_shading_row.pack(fill="x")

    ttk.Label(preview_3d_shading_row, text="Ombrage", style="Vaso.TLabel").pack(side="left")

    shading_scale = ttk.Scale(
        preview_3d_shading_row,
        from_=0.0,
        to=100.0,
        orient="horizontal",
        variable=shading_var,
        command=on_shading_change,
    )

    shading_scale.pack(side="left", fill="x", expand=True, padx=(8, 8))

    shading_value_label = ttk.Label(
        preview_3d_shading_row,
        textvariable=shading_label_var,
        style="Vaso.TLabel",
        width=6,
        anchor="e",
    )
    shading_value_label.pack(side="left")

    figure_3d = Figure(figsize=(6.8, 6.2), dpi=100)
    ax_3d = figure_3d.add_subplot(111, projection="3d")
    canvas_3d = FigureCanvasTkAgg(figure_3d, master=preview_3d_frame)
    canvas_3d_widget = canvas_3d.get_tk_widget()
    canvas_3d_widget.pack(fill="both", expand=True)


    figure_side = Figure(figsize=(2.65, 3.0), dpi=100)
    ax_side = figure_side.add_subplot(111)
    canvas_side = FigureCanvasTkAgg(figure_side, master=side_preview_frame)
    canvas_side_widget = canvas_side.get_tk_widget()
    canvas_side_widget.pack(fill="both", expand=True)

    figure_top = Figure(figsize=(2.65, 3.0), dpi=100)
    ax_top = figure_top.add_subplot(111)
    canvas_top = FigureCanvasTkAgg(figure_top, master=top_preview_frame)
    canvas_top_widget = canvas_top.get_tk_widget()
    canvas_top_widget.pack(fill="both", expand=True)


    # Options
    options_tab.columnconfigure(0, weight=1)
    options_tab.rowconfigure(0, weight=1)

    options_row_frame = ttk.Frame(options_tab, style="Vaso.TFrame")
    options_row_frame.grid(row=0, column=0, sticky="nsew")

    options_row_frame.columnconfigure(0, weight=1, uniform="options_cols")
    options_row_frame.columnconfigure(1, weight=1, uniform="options_cols")
    options_row_frame.columnconfigure(2, weight=1, uniform="options_cols")
    options_row_frame.rowconfigure(0, weight=1)

    theme_frame = ttk.LabelFrame(
        options_row_frame,
        text="Thème",
        padding=12,
        style="Vaso.TLabelframe",
    )
    theme_frame.grid(row=0, column=0, sticky="nsew", padx=(0, 8), pady=(0, 0))

    ttk.Label(theme_frame, text="Thème actif", style="Vaso.TLabel").grid(row=0, column=0, sticky="w", pady=4)

    theme_combo = ttk.Combobox(
        theme_frame,
        textvariable=theme_var,
        values=theme_names,
        state="readonly",
        width=36,
        style="Vaso.TCombobox",
    )
    theme_combo.grid(row=1, column=0, sticky="ew", pady=(0, 4))

    ttk.Label(
        theme_frame,
        text="Le dernier thème sélectionné est mémorisé.",
        style="Vaso.TLabel",
        justify="left",
        wraplength=260,
    ).grid(row=2, column=0, sticky="w", pady=(4, 0))

    theme_frame.columnconfigure(0, weight=1)
    theme_frame.rowconfigure(3, weight=1)

    build_volume_frame = ttk.LabelFrame(
        options_row_frame,
        text="Volume imprimante",
        padding=12,
        style="Vaso.TLabelframe",
    )
    build_volume_frame.grid(row=0, column=1, sticky="nsew", padx=8, pady=(0, 0))

    export_frame = ttk.LabelFrame(
        options_row_frame,
        text="Export STL",
        padding=12,
        style="Vaso.TLabelframe",
    )
    export_frame.grid(row=0, column=2, sticky="nsew", padx=(8, 0), pady=(0, 0))

    ttk.Label(export_frame, text="Dossier d’export STL", style="Vaso.TLabel").grid(row=0, column=0, sticky="w", pady=4)
    ttk.Entry(export_frame, textvariable=export_path_var, width=32, style="Vaso.TEntry").grid(row=1, column=0, sticky="ew", pady=(0, 8))

    def on_browse_click() -> None:
        current_dir = Path(export_path_var.get()).expanduser()
        initial_dir = current_dir if current_dir.exists() and current_dir.is_dir() else get_desktop_dir()

        selected = filedialog.askdirectory(
            title="Choisir le dossier d’export STL",
            initialdir=str(initial_dir),
            mustexist=False,
        )

        if selected:
            export_path_var.set(selected)

    ttk.Button(
        export_frame,
        text="Parcourir...",
        command=on_browse_click,
        style="Vaso.TButton",
    ).grid(row=2, column=0, sticky="w", pady=(0, 8))

    ttk.Label(
        export_frame,
        text=(
            "Par défaut, l’export crée un dossier daté sur le Bureau.\n"
            "Exemple : Vaso-26-03-14 puis vaso_export_0.stl,\n"
            "vaso_export_1.stl, etc."
        ),
        justify="left",
        wraplength=280,
        style="Vaso.TLabel",
    ).grid(row=3, column=0, sticky="w", pady=(8, 0))

    ttk.Label(build_volume_frame, text="Profil actif", style="Vaso.TLabel").grid(row=0, column=0, sticky="w", pady=4)

    printer_profile_combo = ttk.Combobox(
        build_volume_frame,
        textvariable=printer_profile_var,
        values=[profile["name"] for profile in printer_profiles],
        state="readonly",
        width=28,
        style="Vaso.TCombobox",
    )
    printer_profile_combo.grid(row=0, column=1, columnspan=2, sticky="ew", pady=4)

    ttk.Button(
        build_volume_frame,
        text="Nouveau",
        command=lambda: on_new_printer_profile(),
        style="Vaso.TButton",
    ).grid(row=1, column=0, sticky="ew", pady=(4, 8), padx=(0, 4))

    ttk.Button(
        build_volume_frame,
        text="Enregistrer",
        command=lambda: on_save_printer_profile(),
        style="Vaso.TButton",
    ).grid(row=1, column=1, sticky="ew", pady=(4, 8), padx=4)

    ttk.Button(
        build_volume_frame,
        text="Supprimer",
        command=lambda: on_delete_printer_profile(),
        style="Vaso.TButton",
    ).grid(row=1, column=2, sticky="ew", pady=(4, 8), padx=(4, 0))

    ttk.Label(build_volume_frame, text="Largeur max (mm)", style="Vaso.TLabel").grid(row=2, column=0, sticky="w", pady=4)
    ttk.Entry(build_volume_frame, textvariable=build_width_max_var, width=12, style="Vaso.TEntry").grid(row=2, column=1, columnspan=2, sticky="ew", pady=4)

    ttk.Label(build_volume_frame, text="Profondeur max (mm)", style="Vaso.TLabel").grid(row=3, column=0, sticky="w", pady=4)
    ttk.Entry(build_volume_frame, textvariable=build_depth_max_var, width=12, style="Vaso.TEntry").grid(row=3, column=1, columnspan=2, sticky="ew", pady=4)

    ttk.Label(build_volume_frame, text="Hauteur max (mm)", style="Vaso.TLabel").grid(row=4, column=0, sticky="w", pady=4)
    ttk.Entry(build_volume_frame, textvariable=build_height_max_var, width=12, style="Vaso.TEntry").grid(row=4, column=1, columnspan=2, sticky="ew", pady=4)

    ttk.Label(
        build_volume_frame,
        text=(
            "Le profil sélectionné définit les limites utilisées\n"
            "pour contraindre la génération aléatoire."
        ),
        justify="left",
        wraplength=280,
        style="Vaso.TLabel",
    ).grid(row=5, column=0, columnspan=3, sticky="w", pady=(8, 0))

    build_volume_frame.columnconfigure(0, weight=0)
    build_volume_frame.columnconfigure(1, weight=1)
    build_volume_frame.columnconfigure(2, weight=1) 

    export_frame.columnconfigure(0, weight=1)

    # Aide
    help_tab.columnconfigure(0, weight=1)
    help_tab.rowconfigure(0, weight=1)

    help_text = scrolledtext.ScrolledText(
        help_tab,
        wrap="word",
        relief="flat",
        borderwidth=0,
    )
    help_text.grid(row=0, column=0, sticky="nsew")

    help_text.tag_configure(
        "body",
        font=("Segoe UI", 10),
        justify="center",
        spacing1=2,
        spacing3=2,
    )

    help_text.tag_configure(
        "h1",
        font=("Segoe UI", 16, "bold"),
        spacing1=12,
        spacing3=10,
        justify="center",
    )

    help_text.tag_configure(
        "h2",
        font=("Segoe UI", 13, "bold"),
        spacing1=10,
        spacing3=8,
        justify="center",
    )

    help_text.tag_configure(
        "h3",
        font=("Segoe UI", 11, "bold"),
        spacing1=8,
        spacing3=6,
        justify="center",
    )

    help_text.tag_configure(
        "bullet",
        font=("Segoe UI", 10),
        spacing1=2,
        spacing3=2,
        justify="center",
    )

    render_markdown_into_text(help_text, load_help_text(base_dir))

    def draw_preview(params: VaseParameters) -> None:
        preview_params = build_preview_params(params)

        z_values, radius_values = generate_outer_profile_points(params, samples_z=180)
        top_contour = generate_top_outer_contour(params)
        vertices, faces = generate_vase_mesh(preview_params)

        if len(top_contour) >= 2:
            top_contour_closed = np.vstack([top_contour, top_contour[0]])
        else:
            top_contour_closed = top_contour

        colors = THEMES[theme_var.get()]

        ax_side.clear()
        ax_top.clear()
        ax_3d.clear()

        # --- Silhouette
        ax_side.plot(-radius_values, z_values, linewidth=1.4)
        ax_side.plot(radius_values, z_values, linewidth=1.4)
        ax_side.fill_betweenx(z_values, -radius_values, radius_values, alpha=0.12)

        ax_side.set_xlabel("Largeur (mm)", fontsize=9)
        ax_side.set_ylabel("Hauteur (mm)", fontsize=9)

        ax_side.set_aspect("equal", adjustable="box")

        ax_side.locator_params(axis="x", nbins=5)
        ax_side.locator_params(axis="y", nbins=6)
        ax_side.tick_params(labelsize=8)

        # --- Vue du haut
        ax_top.plot(top_contour_closed[:, 0], top_contour_closed[:, 1], linewidth=1.4)
        ax_top.fill(top_contour_closed[:, 0], top_contour_closed[:, 1], alpha=0.12)

        ax_top.set_xlabel("X (mm)", fontsize=9)
        ax_top.set_ylabel("Y (mm)", fontsize=9)

        ax_top.set_aspect("equal", adjustable="box")

        ax_top.locator_params(axis="x", nbins=5)
        ax_top.locator_params(axis="y", nbins=5)
        ax_top.tick_params(labelsize=8)

        # --- Aperçu 3D : mode configurable
        render_cfg = get_preview_3d_render_config(preview_3d_mode_var.get())

        triangles = vertices[faces]
        shaded_facecolors = build_shaded_facecolors(
            triangles=triangles,
            base_hex_color=colors["ACCENT"],
            shading_strength=float(shading_var.get()) / 100.0,
            light_dir=render_cfg["light_dir"],
            ambient=render_cfg["ambient"],
            alpha=render_cfg["alpha"],
            specular_strength=render_cfg["specular_strength"],
            rim_strength=render_cfg["rim_strength"],
            contrast_center=render_cfg["contrast_center"],
            contrast_gain=render_cfg["contrast_gain"],
        )

        mesh = Poly3DCollection(
            triangles,
            linewidths=render_cfg["linewidths"],
            edgecolors=render_cfg["edgecolors"],
            antialiased=render_cfg["antialiased"],
        )
        mesh.set_facecolors(shaded_facecolors)
        mesh.set_edgecolor(render_cfg["edgecolors"])
        ax_3d.add_collection3d(mesh)



        x_min = float(vertices[:, 0].min())
        x_max = float(vertices[:, 0].max())
        y_min = float(vertices[:, 1].min())
        y_max = float(vertices[:, 1].max())
        z_min = float(vertices[:, 2].min())
        z_max = float(vertices[:, 2].max())

        x_center = (x_min + x_max) / 2.0
        y_center = (y_min + y_max) / 2.0
        z_center = (z_min + z_max) / 2.0

        x_size = x_max - x_min
        y_size = y_max - y_min
        z_size = z_max - z_min

        half_range = max(x_size, y_size, z_size) / 2.0
        if half_range <= 0:
            half_range = 1.0

        padding = half_range * 0.08

        ax_3d.set_xlim(x_center - half_range - padding, x_center + half_range + padding)
        ax_3d.set_ylim(y_center - half_range - padding, y_center + half_range + padding)
        ax_3d.set_zlim(z_center - half_range - padding, z_center + half_range + padding)

        try:
            ax_3d.set_box_aspect((
                max(x_size, 1.0),
                max(y_size, 1.0),
                max(z_size, 1.0),
            ))
        except Exception:
            pass

        ax_3d.view_init(
            elev=render_cfg["view_elev"],
            azim=render_cfg["view_azim"],
        )

        apply_theme(
            root=root,
            style=style,
            theme_name=theme_var.get(),
            figure_side=figure_side,
            figure_top=figure_top,
            ax_side=ax_side,
            ax_top=ax_top,
            canvas_side=canvas_side,
            canvas_top=canvas_top,
            help_text_widget=help_text,
        )

        figure_3d.patch.set_facecolor(colors["PANEL"])
        apply_theme_to_3d_axes(ax_3d, theme_var.get())

        figure_side.tight_layout(pad=1.0)
        figure_top.tight_layout(pad=1.0)
        figure_3d.tight_layout(pad=0.8)

        canvas_side.draw()
        canvas_top.draw()
        canvas_3d.draw()



    def read_seed() -> int | None:
        raw = seed_var.get().strip()
        if raw == "":
            return None
        return int(raw)

    def read_build_volume_limits() -> tuple[float, float, float]:
        width_max = float(build_width_max_var.get())
        depth_max = float(build_depth_max_var.get())
        height_max = float(build_height_max_var.get())

        if width_max <= 0:
            raise ValueError("La largeur max d’impression doit être > 0.")
        if depth_max <= 0:
            raise ValueError("La profondeur max d’impression doit être > 0.")
        if height_max <= 0:
            raise ValueError("La hauteur max d’impression doit être > 0.")

        return width_max, depth_max, height_max

    def refresh_printer_profile_combo_values() -> None:
        printer_profile_combo["values"] = [profile["name"] for profile in printer_profiles]

    def get_printer_profile_index(profile_name: str) -> int | None:
        for index, profile in enumerate(printer_profiles):
            if profile["name"] == profile_name:
                return index
        return None

    def apply_printer_profile_to_fields(profile: dict) -> None:
        build_width_max_var.set(f'{profile["width"]:.1f}'.rstrip("0").rstrip("."))
        build_depth_max_var.set(f'{profile["depth"]:.1f}'.rstrip("0").rstrip("."))
        build_height_max_var.set(f'{profile["height"]:.1f}'.rstrip("0").rstrip("."))

    def on_printer_profile_selected(event=None) -> None:
        profile_name = printer_profile_var.get()
        profile_index = get_printer_profile_index(profile_name)
        if profile_index is None:
            return

        profile = printer_profiles[profile_index]
        apply_printer_profile_to_fields(profile)
        save_printer_profiles(base_dir, printer_profiles, profile["name"])
        status_var.set(f"Profil imprimante actif : {profile['name']}.")

    def on_save_printer_profile() -> None:
        profile_name = printer_profile_var.get().strip()
        if not profile_name:
            messagebox.showerror(APP_NAME, "Aucun profil imprimante sélectionné.")
            return

        profile_index = get_printer_profile_index(profile_name)
        if profile_index is None:
            messagebox.showerror(APP_NAME, "Le profil sélectionné est introuvable.")
            return

        width_max, depth_max, height_max = read_build_volume_limits()

        printer_profiles[profile_index] = {
            "name": profile_name,
            "width": width_max,
            "depth": depth_max,
            "height": height_max,
        }

        refresh_printer_profile_combo_values()
        save_printer_profiles(base_dir, printer_profiles, profile_name)
        status_var.set(f"Profil imprimante enregistré : {profile_name}.")

    def on_new_printer_profile() -> None:
        new_name = simpledialog.askstring(
            APP_NAME,
            "Nom du nouveau profil imprimante :",
            parent=root,
        )

        if new_name is None:
            return

        new_name = new_name.strip()
        if not new_name:
            messagebox.showerror(APP_NAME, "Le nom du profil ne peut pas être vide.")
            return

        if get_printer_profile_index(new_name) is not None:
            messagebox.showerror(APP_NAME, f"Le profil « {new_name} » existe déjà.")
            return

        width_max, depth_max, height_max = read_build_volume_limits()

        printer_profiles.append(
            {
                "name": new_name,
                "width": width_max,
                "depth": depth_max,
                "height": height_max,
            }
        )

        printer_profile_var.set(new_name)
        refresh_printer_profile_combo_values()
        save_printer_profiles(base_dir, printer_profiles, new_name)
        status_var.set(f"Nouveau profil imprimante créé : {new_name}.")

    def on_delete_printer_profile() -> None:
        profile_name = printer_profile_var.get().strip()
        profile_index = get_printer_profile_index(profile_name)

        if profile_index is None:
            messagebox.showerror(APP_NAME, "Le profil sélectionné est introuvable.")
            return

        if len(printer_profiles) <= 1:
            messagebox.showerror(APP_NAME, "Impossible de supprimer le dernier profil imprimante.")
            return

        confirmed = messagebox.askyesno(
            APP_NAME,
            f"Supprimer le profil imprimante « {profile_name} » ?",
            parent=root,
        )
        if not confirmed:
            return

        del printer_profiles[profile_index]

        new_active_name = printer_profiles[0]["name"]
        printer_profile_var.set(new_active_name)
        apply_printer_profile_to_fields(printer_profiles[0])
        refresh_printer_profile_combo_values()
        save_printer_profiles(base_dir, printer_profiles, new_active_name)
        status_var.set(f"Profil imprimante supprimé : {profile_name}.")       

    def randomize_fields() -> None:
        seed_value = read_seed()
        if seed_value is None:
            seed_value = random.randint(0, 999999999)
            seed_var.set(str(seed_value))

        width_max, depth_max, height_max = read_build_volume_limits()
        rng = random.Random(seed_value)

        usable_diameter_max = min(width_max, depth_max)
        if usable_diameter_max < 40:
            raise ValueError("Le volume imprimante est trop petit pour générer un vase aléatoire exploitable.")

        style_name = random_style_var.get()


        if random_complexity_enabled_var.get():
            complexity_name = random_complexity_var.get()
        else:
            complexity_name = rng.choices(
                RANDOM_COMPLEXITY_NAMES,
                weights=[4, 4, 2],
                k=1,
            )[0]

        complexity = RANDOM_COMPLEXITY_RULES.get(
            complexity_name,
            RANDOM_COMPLEXITY_RULES["Moyen"],
        )

        if style_name == "Pur aléatoire":
            style_profile_min, style_profile_max = 2, 10
            delta_min, delta_max = None, None
            sides_min, sides_max = 3, 12
            rot_min, rot_max = 0, 90
            z_pool_start, z_pool_end = 8, 99
        elif style_name == "Forme douce":
            style_profile_min, style_profile_max = 5, 10
            delta_min, delta_max = 4, 12
            sides_min, sides_max = 5, 9
            rot_min, rot_max = 0, 28
            z_pool_start, z_pool_end = 10, 97
        elif style_name == "Forme brute":
            style_profile_min, style_profile_max = 3, 8
            delta_min, delta_max = 18, 42
            sides_min, sides_max = 3, 12
            rot_min, rot_max = 0, 90
            z_pool_start, z_pool_end = 8, 99
        elif style_name == "Forme torsadée":
            style_profile_min, style_profile_max = 5, 10
            delta_min, delta_max = 6, 16
            sides_min, sides_max = 4, 8
            rot_min, rot_max = 12, 90
            z_pool_start, z_pool_end = 10, 98
        elif style_name == "Architecturée":
            style_profile_min, style_profile_max = 3, 6
            delta_min, delta_max = 10, 24
            sides_min, sides_max = 4, 8
            rot_min, rot_max = 0, 24
            z_pool_start, z_pool_end = 14, 96
        elif style_name == "Organique":
            style_profile_min, style_profile_max = 6, 10
            delta_min, delta_max = 8, 18
            sides_min, sides_max = 5, 9
            rot_min, rot_max = 0, 36
            z_pool_start, z_pool_end = 10, 98
        elif style_name == "Fuselée":
            style_profile_min, style_profile_max = 4, 8
            delta_min, delta_max = 6, 18
            sides_min, sides_max = 4, 8
            rot_min, rot_max = 0, 30
            z_pool_start, z_pool_end = 12, 98
        elif style_name == "Bulbeuse":
            style_profile_min, style_profile_max = 4, 8
            delta_min, delta_max = 10, 28
            sides_min, sides_max = 4, 9
            rot_min, rot_max = 0, 32
            z_pool_start, z_pool_end = 12, 98
        else:
            style_profile_min, style_profile_max = 3, 10
            delta_min, delta_max = None, None
            sides_min, sides_max = 3, 12
            rot_min, rot_max = 0, 90
            z_pool_start, z_pool_end = 8, 99

        profile_min = max(style_profile_min, complexity["profile_min"])
        profile_max = min(style_profile_max, complexity["profile_max"])

        if profile_min > profile_max:
            profile_min = style_profile_min
            profile_max = style_profile_max

        profile_mode = min(
            profile_max,
            max(profile_min, complexity["profile_mode"]),
        )

        profile_count = int(round(rng.triangular(profile_min, profile_max, profile_mode)))
        profile_count = max(2, min(10, profile_count))

        profile_count_var.set(str(profile_count))
        update_profile_fields_state()


        height_max_int = max(60, int(height_max))
        height_ratio_min = complexity["height_ratio_min"]
        height_ratio_mode = complexity["height_ratio_mode"]
        height_ratio_max = complexity["height_ratio_max"]

        height_min = max(60, int(round(height_max_int * height_ratio_min)))
        height_mode = max(height_min, int(round(height_max_int * height_ratio_mode)))
        height_upper = max(height_min, int(round(height_max_int * height_ratio_max)))

        height = int(round(rng.triangular(height_min, height_upper, height_mode)))
        height = max(60, min(height_max_int, height))

        wall = round(rng.uniform(2.0, 3.6), 1)
        bottom = round(rng.uniform(max(wall, 2.5), 6.0), 1)

        radial = rng.choice([72, 84, 96, 108, 120])
        vertical = max(64, min(180, int(height * rng.uniform(0.45, 0.75))))

        height_var.set(str(height))
        wall_var.set(f"{wall:.1f}")
        bottom_var.set(f"{bottom:.1f}")
        radial_var.set(str(radial))
        vertical_var.set(str(vertical))

        min_diameter = 24
        max_diameter = max(min_diameter + 8, int(usable_diameter_max * 0.78))

        if profile_count == 2:
            active_z_values = [0, 100]
        elif profile_count == 3:
            active_z_values = [0, rng.randint(35, 65), 100]
        else:
            inner_count = profile_count - 2
            z_candidates = list(range(z_pool_start, z_pool_end))
            selected = sorted(rng.sample(z_candidates, inner_count))
            active_z_values = [0] + selected + [100]

        base_diameter = rng.randint(
            max(min_diameter, int(max_diameter * 0.34)),
            max(min_diameter + 6, int(max_diameter * 0.52)),
        )

        diameters: list[int] = []
        sides_values: list[int] = []
        rotations: list[int] = []

        current_sides = rng.randint(sides_min, sides_max)

        for i in range(profile_count):
            if style_name == "Pur aléatoire":
                diameter = rng.randint(min_diameter, max_diameter)
                sides = rng.randint(3, 12)
                rotation = 0 if i == 0 else rng.randint(rot_min, rot_max)

            elif style_name == "Forme douce":
                phase = i / max(1, profile_count - 1)
                curve = np.sin(phase * np.pi)
                target = int(base_diameter + curve * rng.randint(18, 34))
                jitter = rng.randint(-delta_max, delta_max)
                diameter = max(min_diameter, min(max_diameter, target + jitter))
                sides = current_sides if i == 0 else max(sides_min, min(sides_max, current_sides + rng.choice([0, 0, 1, -1])))
                current_sides = sides
                rotation = 0 if i == 0 else min(rot_max, max(rot_min, rotations[-1] + rng.randint(0, 4)))

            elif style_name == "Forme brute":
                target = rng.randint(min_diameter, max_diameter)
                jitter = rng.randint(-delta_max, delta_max)
                diameter = max(min_diameter, min(max_diameter, target + jitter))
                sides = rng.randint(sides_min, sides_max)
                rotation = 0 if i == 0 else rng.randint(rot_min, rot_max)

            elif style_name == "Forme torsadée":
                phase = i / max(1, profile_count - 1)
                curve = np.sin(phase * np.pi)
                target = int(base_diameter + curve * rng.randint(14, 30))
                jitter = rng.randint(-delta_max, delta_max)
                diameter = max(min_diameter, min(max_diameter, target + jitter))
                sides = current_sides if i == 0 else max(sides_min, min(sides_max, current_sides + rng.choice([0, 0, 1, -1])))
                current_sides = sides
                rotation = 0 if i == 0 else min(rot_max, max(rot_min, rotations[-1] + rng.randint(8, 18)))

            elif style_name == "Architecturée":
                phase = i / max(1, profile_count - 1)
                band = 1.0 if phase < 0.34 else (0.72 if phase < 0.67 else 0.90)
                target = int(base_diameter * band + rng.randint(8, 18))
                jitter = rng.randint(-delta_max, delta_max)
                diameter = max(min_diameter, min(max_diameter, target + jitter))
                sides = current_sides if i == 0 else max(sides_min, min(sides_max, current_sides + rng.choice([0, 1, -1])))
                current_sides = sides
                rotation = 0 if i == 0 else min(rot_max, max(rot_min, rotations[-1] + rng.randint(0, 6)))

            elif style_name == "Organique":
                phase = i / max(1, profile_count - 1)
                wave = np.sin(phase * np.pi)
                target = int(base_diameter + wave * rng.randint(22, 40))
                jitter = rng.randint(-delta_max, delta_max)
                diameter = max(min_diameter, min(max_diameter, target + jitter))
                sides = current_sides if i == 0 else max(sides_min, min(sides_max, current_sides + rng.choice([0, 0, 1, -1])))
                current_sides = sides
                rotation = 0 if i == 0 else min(rot_max, max(rot_min, rotations[-1] + rng.randint(0, 7)))

            elif style_name == "Fuselée":
                phase = i / max(1, profile_count - 1)
                taper = 1.0 - 0.55 * phase
                target = int(base_diameter * taper + rng.randint(16, 38))
                jitter = rng.randint(-delta_max, delta_max)
                diameter = max(min_diameter, min(max_diameter, target + jitter))
                sides = current_sides if i == 0 else max(sides_min, min(sides_max, current_sides + rng.choice([0, 0, 1, -1])))
                current_sides = sides
                rotation = 0 if i == 0 else min(rot_max, max(rot_min, rotations[-1] + rng.randint(0, 7)))

            elif style_name == "Bulbeuse":
                phase = i / max(1, profile_count - 1)
                wave = np.sin(phase * np.pi)
                target = int(base_diameter + wave * rng.randint(24, 48))
                jitter = rng.randint(-delta_max, delta_max)
                diameter = max(min_diameter, min(max_diameter, target + jitter))
                sides = current_sides if i == 0 else max(sides_min, min(sides_max, current_sides + rng.choice([0, 0, 1, -1])))
                current_sides = sides
                rotation = 0 if i == 0 else min(rot_max, max(rot_min, rotations[-1] + rng.randint(0, 8)))

            else:
                diameter = rng.randint(min_diameter, max_diameter)
                sides = rng.randint(3, 12)
                rotation = 0 if i == 0 else rng.randint(0, 90)

            diameters.append(int(diameter))
            sides_values.append(int(sides))
            rotations.append(int(rotation))

        for i in range(profile_count):
            profile_enabled_vars[i].set(True)
            z_ratio_vars[i].set(str(active_z_values[i]))
            diameter_vars[i].set(str(diameters[i]))
            sides_vars[i].set(str(sides_values[i]))
            rotation_vars[i].set(str(rotations[i]))
            
        profile_enabled_vars[0].set(True)
        profile_enabled_vars[profile_count - 1].set(True)    
            
        for i in range(profile_count, 10):
            profile_enabled_vars[i].set(False)

        if texture_mode_var.get() == "Texture aléatoire":
            random_texture_name = rng.choices(
                [name for name in TEXTURE_TYPE_NAMES if name != "Pas de texture"],
                weights=[1] * (len(TEXTURE_TYPE_NAMES) - 1),
                k=1,
            )[0]
            random_zoom_name = rng.choices(
                TEXTURE_ZOOM_NAMES,
                weights=[1, 2, 3, 2, 1],
                k=1,
            )[0]

            texture_type_var.set(random_texture_name)
            texture_zoom_var.set(random_zoom_name)
            texture_type_2_var.set("Pas de texture")
            texture_zoom_2_var.set("Moyen")

        elif texture_mode_var.get() == "Double texture aléatoire":
            random_texture_names = rng.sample(
                [name for name in TEXTURE_TYPE_NAMES if name != "Pas de texture"],
                2,
            )

            random_zoom_name_1 = rng.choices(
                TEXTURE_ZOOM_NAMES,
                weights=[1, 2, 3, 2, 1],
                k=1,
            )[0]
            random_zoom_name_2 = rng.choices(
                TEXTURE_ZOOM_NAMES,
                weights=[1, 2, 3, 2, 1],
                k=1,
            )[0]

            texture_type_var.set(random_texture_names[0])
            texture_zoom_var.set(random_zoom_name_1)
            texture_type_2_var.set(random_texture_names[1])
            texture_zoom_2_var.set(random_zoom_name_2)


    def build_current_params() -> VaseParameters:
        params = build_params_from_ui(
            height_var=height_var,
            wall_var=wall_var,
            bottom_var=bottom_var,
            radial_var=radial_var,
            vertical_var=vertical_var,
            profile_count_var=profile_count_var,
            profile_enabled_vars=profile_enabled_vars,
            z_ratio_vars=z_ratio_vars,
            diameter_vars=diameter_vars,
            sides_vars=sides_vars,
            rotation_vars=rotation_vars,
        )

        params.texture_mode = texture_mode_var.get()

        if params.texture_mode == "Pas de texture":
            params.texture_type = "Pas de texture"
            params.texture_zoom = "Moyen"
            params.texture_type_2 = "Pas de texture"
            params.texture_zoom_2 = "Moyen"

        elif params.texture_mode == "Texture aléatoire":
            params.texture_type = texture_type_var.get()
            params.texture_zoom = texture_zoom_var.get()
            params.texture_type_2 = "Pas de texture"
            params.texture_zoom_2 = "Moyen"

        elif params.texture_mode == "Texture imposée":
            params.texture_type = texture_type_var.get()
            params.texture_zoom = texture_zoom_var.get()
            params.texture_type_2 = "Pas de texture"
            params.texture_zoom_2 = "Moyen"

        elif params.texture_mode == "Double texture":
            params.texture_type = texture_type_var.get()
            params.texture_zoom = texture_zoom_var.get()
            params.texture_type_2 = texture_type_2_var.get()
            params.texture_zoom_2 = texture_zoom_2_var.get()

        elif params.texture_mode == "Double texture aléatoire":
            params.texture_mode = "Double texture"
            params.texture_type = texture_type_var.get()
            params.texture_zoom = texture_zoom_var.get()
            params.texture_type_2 = texture_type_2_var.get()
            params.texture_zoom_2 = texture_zoom_2_var.get()

        else:
            params.texture_type = "Pas de texture"
            params.texture_zoom = "Moyen"
            params.texture_type_2 = "Pas de texture"
            params.texture_zoom_2 = "Moyen"

        return params


    def on_preview_click() -> None:
        try:
            params = build_current_params()
            draw_preview(params)
            status_var.set("Aperçu 2D/3D mis à jour.")
        except ValueError as exc:
            status_var.set("Paramètres invalides.")
            messagebox.showerror(APP_NAME, f"Paramètres invalides :\n{exc}")
        except Exception as exc:
            status_var.set("Erreur pendant l’aperçu.")
            messagebox.showerror(APP_NAME, f"Erreur pendant la mise à jour de l’aperçu :\n{exc}")



    def on_random_click() -> None:
        try:
            seed_var.set(str(random.randint(0, 999999999)))
            randomize_fields()
            params = build_current_params()
            draw_preview(params)
            status_var.set(
                f"Seed générée — {len(params.profiles)} profils — mode textures : {texture_mode_var.get()}."
            )
        except ValueError as exc:
            status_var.set("Seed ou paramètres invalides.")
            messagebox.showerror(APP_NAME, f"Valeur invalide :\n{exc}")
        except Exception as exc:
            status_var.set("Erreur pendant la génération aléatoire.")
            messagebox.showerror(APP_NAME, f"Erreur pendant la génération aléatoire :\n{exc}")

    def on_generate_click() -> None:
        try:
            export_dir = Path(export_path_var.get()).expanduser()

            if export_dir.suffix:
                export_dir = export_dir.parent

            export_dir.mkdir(parents=True, exist_ok=True)
            output_path = get_next_export_path(export_dir)

            params = build_current_params()
            vertices, faces = generate_vase_mesh(params)
            export_stl(vertices, faces, output_path)

            status_var.set(f"STL généré : {output_path}")

        except ValueError as exc:
            status_var.set("Paramètres invalides.")
            messagebox.showerror(APP_NAME, f"Paramètres invalides :\n{exc}")

        except Exception as exc:
            status_var.set("Erreur pendant la génération.")
            messagebox.showerror(APP_NAME, f"Erreur pendant la génération du STL :\n{exc}")


    def on_theme_change(event=None) -> None:
        try:
            save_selected_theme(base_dir, theme_var.get())
            apply_theme(
                root=root,
                style=style,
                theme_name=theme_var.get(),
                figure_side=figure_side,
                figure_top=figure_top,
                ax_side=ax_side,
                ax_top=ax_top,
                canvas_side=canvas_side,
                canvas_top=canvas_top,
                help_text_widget=help_text,
            )

            params = build_current_params()
            draw_preview(params)
        except Exception as exc:
            status_var.set("Erreur pendant l’application du thème.")
            messagebox.showerror(APP_NAME, f"Erreur pendant l’application du thème :\n{exc}")

    theme_combo.bind("<<ComboboxSelected>>", on_theme_change)
    printer_profile_combo.bind("<<ComboboxSelected>>", on_printer_profile_selected)
    texture_mode_combo.bind("<<ComboboxSelected>>", on_texture_controls_change)
    texture_type_combo.bind("<<ComboboxSelected>>", on_texture_controls_change)
    texture_zoom_combo.bind("<<ComboboxSelected>>", on_texture_controls_change)
    texture_type_2_combo.bind("<<ComboboxSelected>>", on_texture_controls_change)
    texture_zoom_2_combo.bind("<<ComboboxSelected>>", on_texture_controls_change)
    preview_3d_mode_combo.bind("<<ComboboxSelected>>", on_preview_3d_mode_change)
    profile_count_var.trace_add("write", lambda *args: update_profile_fields_state())

    ttk.Button(
        buttons_inner_frame,
        text="Aperçu",
        command=on_preview_click,
        style="Vaso.TButton",
    ).pack(side="left", padx=(0, 8))

    ttk.Button(
        buttons_inner_frame,
        text="Aléatoire",
        command=on_random_click,
        style="Vaso.TButton",
    ).pack(side="left", padx=(0, 8))

    ttk.Button(
        buttons_inner_frame,
        text="Générer le STL",
        command=on_generate_click,
        style="Vaso.TButton",
    ).pack(side="left")



    status_label = ttk.Label(
        main_frame,
        textvariable=status_var,
        style="Vaso.TLabel",
    )
    status_label.grid(row=1, column=0, sticky="w", pady=(8, 0))

    apply_theme(
        root=root,
        style=style,
        theme_name=theme_var.get(),
        figure_side=figure_side,
        figure_top=figure_top,
        ax_side=ax_side,
        ax_top=ax_top,
        canvas_side=canvas_side,
        canvas_top=canvas_top,
        help_text_widget=help_text,
    )

    refresh_printer_profile_combo_values()
    printer_profile_var.set(active_printer_profile["name"])
    update_profile_fields_state()
    update_random_complexity_state()
    update_texture_mode_state()

    shading_label_var.set(f"{int(round(shading_var.get()))} %")
    status_var.set("Interface prête. Cliquez sur « Aperçu » ou « Aléatoire » pour générer un vase.")


    root.mainloop()


if __name__ == "__main__":
    main()