from pathlib import Path
import trimesh


def export_stl(vertices, faces, filename: str | Path) -> None:
    mesh = trimesh.Trimesh(vertices=vertices, faces=faces, process=False)
    mesh.export(str(filename))