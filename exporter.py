import trimesh


def export_stl(vertices, faces, filename: str) -> None:
    mesh = trimesh.Trimesh(vertices=vertices, faces=faces, process=False)
    mesh.export(filename)
