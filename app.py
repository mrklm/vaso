from pathlib import Path
from datetime import datetime
import json
import random
import tkinter as tk
import numpy as np
from tkinter import ttk, messagebox, filedialog, scrolledtext


from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from model import Profile, VaseParameters
from generator import (
    generate_vase_mesh,
    generate_outer_profile_points,
    generate_top_outer_contour,
)
from exporter import export_stl

APP_VERSION = "0.2.1"
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


def get_settings_path(base_dir: Path) -> Path:
    return base_dir / SETTINGS_FILE


def load_saved_theme(base_dir: Path) -> str | None:
    settings_path = get_settings_path(base_dir)
    if not settings_path.exists():
        return None

    try:
        data = json.loads(settings_path.read_text(encoding="utf-8"))
    except Exception:
        return None

    theme_name = data.get("theme")
    if isinstance(theme_name, str) and theme_name in THEMES:
        return theme_name
    return None


def save_selected_theme(base_dir: Path, theme_name: str) -> None:
    settings_path = get_settings_path(base_dir)
    payload = {"theme": theme_name}
    settings_path.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )


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


def _interp_float(a: float, b: float, t: float) -> float:
    return (1.0 - t) * a + t * b


def _interp_int(a: int, b: int, t: float) -> int:
    return int(round((1.0 - t) * a + t * b))


def _build_dynamic_profiles_from_anchors(
    profile_count: int,
    d_bottom: float,
    d_middle: float,
    d_top: float,
    s_bottom: int,
    s_middle: int,
    s_top: int,
    rot_middle: float,
    rot_top: float,
    middle_z_ratio: float,
) -> list[Profile]:
    if profile_count < 3 or profile_count > 10:
        raise ValueError("Le nombre de profils doit être compris entre 3 et 10.")

    if not (0.1 < middle_z_ratio < 0.9):
        raise ValueError("La hauteur du profil central doit être comprise entre 10 et 90 %.")

    profiles: list[Profile] = []

    for i in range(profile_count):
        z_ratio = i / (profile_count - 1)

        if z_ratio <= middle_z_ratio:
            local_t = z_ratio / middle_z_ratio if middle_z_ratio > 0 else 0.0

            diameter = _interp_float(d_bottom, d_middle, local_t)
            sides = _interp_int(s_bottom, s_middle, local_t)
            rotation_deg = _interp_float(0.0, rot_middle, local_t)
        else:
            upper_span = 1.0 - middle_z_ratio
            local_t = (z_ratio - middle_z_ratio) / upper_span if upper_span > 0 else 0.0

            diameter = _interp_float(d_middle, d_top, local_t)
            sides = _interp_int(s_middle, s_top, local_t)
            rotation_deg = _interp_float(rot_middle, rot_top, local_t)

        profiles.append(
            Profile(
                z_ratio=z_ratio,
                diameter=diameter,
                sides=max(3, sides),
                rotation_deg=rotation_deg,
                offset_x=0.0,
                offset_y=0.0,
            )
        )

    return profiles


def build_params_from_ui(
    height_var: tk.StringVar,
    wall_var: tk.StringVar,
    bottom_var: tk.StringVar,
    radial_var: tk.StringVar,
    vertical_var: tk.StringVar,
    profile_count_var: tk.StringVar,
    d_bottom_var: tk.StringVar,
    d_middle_var: tk.StringVar,
    d_top_var: tk.StringVar,
    s_bottom_var: tk.StringVar,
    s_middle_var: tk.StringVar,
    s_top_var: tk.StringVar,
    rot_middle_var: tk.StringVar,
    rot_top_var: tk.StringVar,
    middle_height_ratio_var: tk.StringVar,
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
    if profile_count < 3 or profile_count > 10:
        raise ValueError("Le nombre de profils doit être compris entre 3 et 10.")

    params.profiles = _build_dynamic_profiles_from_anchors(
        profile_count=profile_count,
        d_bottom=float(d_bottom_var.get()),
        d_middle=float(d_middle_var.get()),
        d_top=float(d_top_var.get()),
        s_bottom=int(s_bottom_var.get()),
        s_middle=int(s_middle_var.get()),
        s_top=int(s_top_var.get()),
        rot_middle=float(rot_middle_var.get()),
        rot_top=float(rot_top_var.get()),
        middle_z_ratio=float(middle_height_ratio_var.get()) / 100.0,
    )


    return params


def apply_theme(
    root: tk.Tk,
    style: ttk.Style,
    theme_name: str,
    figure: Figure,
    ax_side,
    ax_top,
    canvas: FigureCanvasTkAgg,
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

    figure.patch.set_facecolor(panel)

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

    canvas.draw_idle()

def apply_theme_to_3d_axes(ax_3d, theme_name: str) -> None:
    colors = THEMES[theme_name]

    panel = colors["PANEL"]
    field = colors["FIELD"]
    fg = colors["FG"]
    accent = colors["ACCENT"]

    ax_3d.set_facecolor(field)
    ax_3d.set_title("Aperçu 3D", color=accent)

    ax_3d.set_xlabel("X (mm)", color=fg)
    ax_3d.set_ylabel("Y (mm)", color=fg)
    ax_3d.set_zlabel("Z (mm)", color=fg)

    ax_3d.tick_params(colors=fg)

    # Fond des panneaux 3D
    try:
        ax_3d.xaxis.pane.set_facecolor(field)
        ax_3d.yaxis.pane.set_facecolor(field)
        ax_3d.zaxis.pane.set_facecolor(field)

        ax_3d.xaxis.pane.set_edgecolor(accent)
        ax_3d.yaxis.pane.set_edgecolor(accent)
        ax_3d.zaxis.pane.set_edgecolor(accent)
    except Exception:
        pass

    # Couleur des axes
    try:
        ax_3d.xaxis.line.set_color(accent)
        ax_3d.yaxis.line.set_color(accent)
        ax_3d.zaxis.line.set_color(accent)
    except Exception:
        pass

    ax_3d.grid(True, color=accent, alpha=0.25)


def main() -> None:
    root = tk.Tk()
    root.title(f"{APP_NAME} — v{APP_VERSION}")
    root.geometry("1280x760")
    root.minsize(1160, 700)

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

    status_var = tk.StringVar(value="Prêt.")
    export_path_var = tk.StringVar(value=str(get_default_export_dir()))
    seed_var = tk.StringVar(value="")

    height_var = tk.StringVar(value="180")
    wall_var = tk.StringVar(value="2.4")
    bottom_var = tk.StringVar(value="3.0")
    radial_var = tk.StringVar(value="96")
    vertical_var = tk.StringVar(value="120")
    profile_count_var = tk.StringVar(value="3")

    d_bottom_var = tk.StringVar(value="40")
    d_middle_var = tk.StringVar(value="90")
    d_top_var = tk.StringVar(value="50")

    s_bottom_var = tk.StringVar(value="6")
    s_middle_var = tk.StringVar(value="8")
    s_top_var = tk.StringVar(value="6")

    rot_middle_var = tk.StringVar(value="15")
    rot_top_var = tk.StringVar(value="30")
    middle_height_ratio_var = tk.StringVar(value="50")


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

    general_tab.rowconfigure(0, weight=4)
    general_tab.rowconfigure(1, weight=2)
    general_tab.rowconfigure(2, weight=0)

    general_frame = ttk.LabelFrame(
        general_tab,
        text="Paramètres généraux",
        padding=12,
        style="Vaso.TLabelframe",
    )
    general_frame.grid(row=0, column=0, rowspan=2, sticky="nsew", padx=(0, 12), pady=(0, 12))

    preview_3d_frame = ttk.LabelFrame(
        general_tab,
        text="Aperçu 3D",
        padding=12,
        style="Vaso.TLabelframe",
    )
    preview_3d_frame.grid(row=0, column=1, sticky="nsew", padx=(0, 12), pady=(0, 12))

    preview_2d_frame = ttk.LabelFrame(
        general_tab,
        text="Aperçu 2D",
        padding=12,
        style="Vaso.TLabelframe",
    )
    preview_2d_frame.grid(row=1, column=1, sticky="nsew", padx=(0, 12), pady=(0, 12))

    shape_frame = ttk.LabelFrame(
        general_tab,
        text="Forme du vase",
        padding=12,
        style="Vaso.TLabelframe",
    )
    shape_frame.grid(row=0, column=2, rowspan=2, sticky="nsew", pady=(0, 12))


    ttk.Label(general_frame, text="Hauteur (mm)", style="Vaso.TLabel").grid(row=0, column=0, sticky="w", pady=4)
    ttk.Entry(general_frame, textvariable=height_var, width=12, style="Vaso.TEntry").grid(row=0, column=1, sticky="ew", pady=4)

    ttk.Label(general_frame, text="Épaisseur coque (mm)", style="Vaso.TLabel").grid(row=1, column=0, sticky="w", pady=4)
    ttk.Entry(general_frame, textvariable=wall_var, width=12, style="Vaso.TEntry").grid(row=1, column=1, sticky="ew", pady=4)

    ttk.Label(general_frame, text="Épaisseur fond (mm)", style="Vaso.TLabel").grid(row=2, column=0, sticky="w", pady=4)
    ttk.Entry(general_frame, textvariable=bottom_var, width=12, style="Vaso.TEntry").grid(row=2, column=1, sticky="ew", pady=4)

    ttk.Label(general_frame, text="Résolution circulaire", style="Vaso.TLabel").grid(row=3, column=0, sticky="w", pady=4)
    ttk.Entry(general_frame, textvariable=radial_var, width=12, style="Vaso.TEntry").grid(row=3, column=1, sticky="ew", pady=4)

    ttk.Label(general_frame, text="Résolution verticale", style="Vaso.TLabel").grid(row=4, column=0, sticky="w", pady=4)
    ttk.Entry(general_frame, textvariable=vertical_var, width=12, style="Vaso.TEntry").grid(row=4, column=1, sticky="ew", pady=4)

    ttk.Label(general_frame, text="Nombre de profils (3-10)", style="Vaso.TLabel").grid(row=5, column=0, sticky="w", pady=4)
    ttk.Entry(general_frame, textvariable=profile_count_var, width=12, style="Vaso.TEntry").grid(row=5, column=1, sticky="ew", pady=4)

    ttk.Label(general_frame, text="Seed", style="Vaso.TLabel").grid(row=6, column=0, sticky="w", pady=4)
    ttk.Entry(general_frame, textvariable=seed_var, width=12, style="Vaso.TEntry").grid(row=6, column=1, sticky="ew", pady=4)

    general_frame.columnconfigure(1, weight=1)

    ttk.Label(shape_frame, text="Diamètre bas (mm)", style="Vaso.TLabel").grid(row=0, column=0, sticky="w", pady=4)
    ttk.Entry(shape_frame, textvariable=d_bottom_var, width=12, style="Vaso.TEntry").grid(row=0, column=1, sticky="ew", pady=4)

    ttk.Label(shape_frame, text="Diamètre milieu (mm)", style="Vaso.TLabel").grid(row=1, column=0, sticky="w", pady=4)
    ttk.Entry(shape_frame, textvariable=d_middle_var, width=12, style="Vaso.TEntry").grid(row=1, column=1, sticky="ew", pady=4)

    ttk.Label(shape_frame, text="Diamètre haut (mm)", style="Vaso.TLabel").grid(row=2, column=0, sticky="w", pady=4)
    ttk.Entry(shape_frame, textvariable=d_top_var, width=12, style="Vaso.TEntry").grid(row=2, column=1, sticky="ew", pady=4)

    ttk.Label(shape_frame, text="Côtés bas", style="Vaso.TLabel").grid(row=3, column=0, sticky="w", pady=4)
    ttk.Entry(shape_frame, textvariable=s_bottom_var, width=12, style="Vaso.TEntry").grid(row=3, column=1, sticky="ew", pady=4)

    ttk.Label(shape_frame, text="Côtés milieu", style="Vaso.TLabel").grid(row=4, column=0, sticky="w", pady=4)
    ttk.Entry(shape_frame, textvariable=s_middle_var, width=12, style="Vaso.TEntry").grid(row=4, column=1, sticky="ew", pady=4)

    ttk.Label(shape_frame, text="Côtés haut", style="Vaso.TLabel").grid(row=5, column=0, sticky="w", pady=4)
    ttk.Entry(shape_frame, textvariable=s_top_var, width=12, style="Vaso.TEntry").grid(row=5, column=1, sticky="ew", pady=4)

    ttk.Label(shape_frame, text="Rotation milieu (°)", style="Vaso.TLabel").grid(row=6, column=0, sticky="w", pady=4)
    ttk.Entry(shape_frame, textvariable=rot_middle_var, width=12, style="Vaso.TEntry").grid(row=6, column=1, sticky="ew", pady=4)

    ttk.Label(shape_frame, text="Rotation haut (°)", style="Vaso.TLabel").grid(row=7, column=0, sticky="w", pady=4)
    ttk.Entry(shape_frame, textvariable=rot_top_var, width=12, style="Vaso.TEntry").grid(row=7, column=1, sticky="ew", pady=4)

    ttk.Label(shape_frame, text="Hauteur profil central (%)", style="Vaso.TLabel").grid(row=8, column=0, sticky="w", pady=4)
    ttk.Entry(shape_frame, textvariable=middle_height_ratio_var, width=12, style="Vaso.TEntry").grid(row=8, column=1, sticky="ew", pady=4)

    ttk.Label(
        shape_frame,
        text="50 = milieu exact, 40 = plus bas, 60 = plus haut",
        style="Vaso.TLabel",
    ).grid(row=9, column=0, columnspan=2, sticky="w", pady=4)


    shape_frame.columnconfigure(1, weight=1)

    figure_3d = Figure(figsize=(7.2, 5.8), dpi=100)
    ax_3d = figure_3d.add_subplot(111, projection="3d")
    canvas_3d = FigureCanvasTkAgg(figure_3d, master=preview_3d_frame)
    canvas_3d_widget = canvas_3d.get_tk_widget()
    canvas_3d_widget.pack(fill="both", expand=True)

    figure = Figure(figsize=(7.2, 2.8), dpi=100)
    ax_side = figure.add_subplot(121)
    ax_top = figure.add_subplot(122)
    figure.tight_layout(pad=2.0)

    canvas = FigureCanvasTkAgg(figure, master=preview_2d_frame)
    canvas_widget = canvas.get_tk_widget()
    canvas_widget.pack(fill="both", expand=True)

    buttons_frame = ttk.Frame(general_tab, style="Vaso.TFrame")
    buttons_frame.grid(row=2, column=0, columnspan=3, sticky="w", pady=(0, 8))


    # Options
    options_tab.columnconfigure(0, weight=1)
    options_tab.rowconfigure(0, weight=0)
    options_tab.rowconfigure(1, weight=1)

    theme_frame = ttk.LabelFrame(
        options_tab,
        text="Thème",
        padding=12,
        style="Vaso.TLabelframe",
    )
    theme_frame.grid(row=0, column=0, sticky="nw", padx=(0, 0), pady=(0, 12))

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
    ).grid(row=2, column=0, sticky="w", pady=(4, 0))

    theme_frame.columnconfigure(0, weight=1)

    export_frame = ttk.LabelFrame(
        options_tab,
        text="Export STL",
        padding=12,
        style="Vaso.TLabelframe",
    )
    export_frame.grid(row=1, column=0, sticky="nw", padx=(0, 0), pady=(0, 0))

    ttk.Label(export_frame, text="Dossier d’export STL", style="Vaso.TLabel").grid(row=0, column=0, sticky="w", pady=4)
    ttk.Entry(export_frame, textvariable=export_path_var, width=48, style="Vaso.TEntry").grid(row=1, column=0, sticky="ew", pady=(0, 8))

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
            "Exemple : Vaso-26-03-14 puis vaso_export_0.stl, vaso_export_1.stl, etc."
        ),
        justify="left",
        style="Vaso.TLabel",
    ).grid(row=3, column=0, sticky="w", pady=(8, 0))

    export_frame.columnconfigure(0, weight=1)

    # Aide
    help_tab.columnconfigure(0, weight=1)
    help_tab.rowconfigure(0, weight=1)

    help_text = scrolledtext.ScrolledText(
        help_tab,
        wrap="word",
        font=("Consolas", 10),
        relief="flat",
        borderwidth=0,
    )
    help_text.grid(row=0, column=0, sticky="nsew")
    help_text.insert("1.0", load_help_text(base_dir))
    help_text.configure(state="disabled")

    def draw_preview(params: VaseParameters) -> None:
        z_values, radius_values = generate_outer_profile_points(params, samples_z=240)
        top_contour = generate_top_outer_contour(params)
        vertices, faces = generate_vase_mesh(params)

        if len(top_contour) >= 2:
            top_contour_closed = np.vstack([top_contour, top_contour[0]])
        else:
            top_contour_closed = top_contour

        colors = THEMES[theme_var.get()]

        ax_side.clear()
        ax_top.clear()
        ax_3d.clear()

        # --- Aperçu 2D
        ax_side.plot(-radius_values, z_values)
        ax_side.plot(radius_values, z_values)
        ax_side.fill_betweenx(z_values, -radius_values, radius_values, alpha=0.15)
        ax_side.set_title("Silhouette")
        ax_side.set_xlabel("Largeur (mm)")
        ax_side.set_ylabel("Hauteur (mm)")
        ax_side.set_aspect("equal", adjustable="box")

        ax_top.plot(top_contour_closed[:, 0], top_contour_closed[:, 1])
        ax_top.fill(top_contour_closed[:, 0], top_contour_closed[:, 1], alpha=0.15)
        ax_top.set_title("Vue du haut")
        ax_top.set_xlabel("X (mm)")
        ax_top.set_ylabel("Y (mm)")
        ax_top.set_aspect("equal", adjustable="box")

        # --- Aperçu 3D
        triangles = vertices[faces]
        mesh = Poly3DCollection(
            triangles,
            linewidths=0.20,
            edgecolors=colors["ACCENT"],
            alpha=0.85,
        )
        mesh.set_facecolor(colors["FIELD"])
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

        ax_3d.set_xlim(x_center - half_range, x_center + half_range)
        ax_3d.set_ylim(y_center - half_range, y_center + half_range)
        ax_3d.set_zlim(z_center - half_range, z_center + half_range)

        try:
            ax_3d.set_box_aspect((
                max(x_size, 1.0),
                max(y_size, 1.0),
                max(z_size, 1.0),
            ))
        except Exception:
            pass

        ax_3d.view_init(elev=22, azim=35)

        apply_theme(
            root=root,
            style=style,
            theme_name=theme_var.get(),
            figure=figure,
            ax_side=ax_side,
            ax_top=ax_top,
            canvas=canvas,
            help_text_widget=help_text,
        )

        figure_3d.patch.set_facecolor(colors["PANEL"])
        apply_theme_to_3d_axes(ax_3d, theme_var.get())

        figure.tight_layout(pad=2.0)
        figure_3d.tight_layout(pad=1.2)

        canvas.draw()
        canvas_3d.draw()


    def read_seed() -> int | None:
        raw = seed_var.get().strip()
        if raw == "":
            return None
        return int(raw)

    def randomize_fields() -> None:
        seed_value = read_seed()
        if seed_value is None:
            seed_value = random.randint(0, 999999999)
            seed_var.set(str(seed_value))

        rng = random.Random(seed_value)

        height = rng.randint(120, 260)
        wall = round(rng.uniform(2.0, 3.6), 1)
        bottom = round(rng.uniform(max(wall, 2.5), 6.0), 1)

        radial = rng.choice([72, 96, 120, 144])
        vertical = rng.choice([90, 120, 150, 180])
        profile_count = rng.randint(3, 10)

        d_bottom = rng.randint(25, 70)
        d_middle = rng.randint(max(d_bottom + 10, 45), 130)
        d_top = rng.randint(20, 80)

        s_bottom = rng.randint(3, 10)
        s_middle = rng.randint(3, 12)
        s_top = rng.randint(3, 10)

        rot_middle = rng.randint(0, 45)
        rot_top = rng.randint(0, 90)

        middle_height_ratio = rng.randint(38, 62)


        height_var.set(str(height))
        wall_var.set(f"{wall:.1f}")
        bottom_var.set(f"{bottom:.1f}")
        radial_var.set(str(radial))
        vertical_var.set(str(vertical))
        profile_count_var.set(str(profile_count))

        d_bottom_var.set(str(d_bottom))
        d_middle_var.set(str(d_middle))
        d_top_var.set(str(d_top))

        s_bottom_var.set(str(s_bottom))
        s_middle_var.set(str(s_middle))
        s_top_var.set(str(s_top))

        rot_middle_var.set(str(rot_middle))
        rot_top_var.set(str(rot_top))
        middle_height_ratio_var.set(str(middle_height_ratio))



    def build_current_params() -> VaseParameters:
        return build_params_from_ui(
            height_var=height_var,
            wall_var=wall_var,
            bottom_var=bottom_var,
            radial_var=radial_var,
            vertical_var=vertical_var,
            profile_count_var=profile_count_var,
            d_bottom_var=d_bottom_var,
            d_middle_var=d_middle_var,
            d_top_var=d_top_var,
            s_bottom_var=s_bottom_var,
            s_middle_var=s_middle_var,
            s_top_var=s_top_var,
            rot_middle_var=rot_middle_var,
            rot_top_var=rot_top_var,
            middle_height_ratio_var=middle_height_ratio_var,
        )


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
            status_var.set("Nouvelle seed aléatoire générée.")
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
                figure=figure,
                ax_side=ax_side,
                ax_top=ax_top,
                canvas=canvas,
                help_text_widget=help_text,
            )
            params = build_current_params()
            draw_preview(params)
        except Exception as exc:
            status_var.set("Erreur pendant l’application du thème.")
            messagebox.showerror(APP_NAME, f"Erreur pendant l’application du thème :\n{exc}")

    theme_combo.bind("<<ComboboxSelected>>", on_theme_change)

    ttk.Button(
        buttons_frame,
        text="Aperçu",
        command=on_preview_click,
        style="Vaso.TButton",
    ).pack(side="left", padx=(0, 8))

    ttk.Button(
        buttons_frame,
        text="Aléatoire",
        command=on_random_click,
        style="Vaso.TButton",
    ).pack(side="left", padx=(0, 8))

    ttk.Button(
        buttons_frame,
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
        figure=figure,
        ax_side=ax_side,
        ax_top=ax_top,
        canvas=canvas,
        help_text_widget=help_text,
    )

    try:
        draw_preview(build_current_params())
    except Exception as exc:
        status_var.set(f"Aperçu initial impossible : {exc}")

    root.mainloop()


if __name__ == "__main__":
    main()