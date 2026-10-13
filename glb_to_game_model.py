"""Turn a Pixal3D model (about a million triangles and a 4K texture) into a small model a game can draw.

    python glb_to_game_model.py pixal3d_textured.glb game.glb --triangles 14000 --views views.jpg

What it does:
1. Reads the .glb and copies the texture's colour onto every corner point (vertex colours), so the game needs no texture file.
2. Draws the model from four sides into one picture (--views), so you or your agent can check it before using it.
3. Merges nearby points on a grid until the model is at or under --triangles.
4. Turns every face to point outward, because the source can contain two-sided faces.
5. Writes a .glb with vertex colours.

Needs: pip install trimesh numpy scipy pillow
"""
import argparse
import numpy as np
import trimesh
from PIL import Image
from scipy import ndimage


def load(path):
    scene = trimesh.load(path)
    mesh = scene.to_geometry() if hasattr(scene, 'to_geometry') else scene.dump(concatenate=True)
    verts = np.asarray(mesh.vertices, dtype=np.float64)
    faces = np.asarray(mesh.faces)
    tex = np.asarray(mesh.visual.material.baseColorTexture.convert('RGB')).astype(np.float32)
    uv = np.asarray(mesh.visual.uv)
    h, w = tex.shape[:2]
    px = np.clip((uv[:, 0] % 1.0) * (w - 1), 0, w - 1).astype(int)
    py = np.clip((1 - (uv[:, 1] % 1.0)) * (h - 1), 0, h - 1).astype(int)
    return verts, faces, tex[py, px]


def four_views(verts, colours, path, size=700):
    """Front, side, back and other side as point pictures: the nearest point wins each pixel."""
    height = verts[:, 1]
    span = height.max() - height.min()
    tiles = []
    for axis, flip in [(0, False), (2, False), (0, True), (2, True)]:
        sign = -1 if flip else 1
        across = verts[:, axis] * sign
        depth = verts[:, 2 - axis] * sign * (1 if axis == 0 else -1)
        sx = ((across - (across.min() + across.max()) / 2) / span * size * 0.95 + size / 2).astype(int)
        sy = ((height.max() - height) / span * size * 0.95 + size * 0.02).astype(int)
        order = np.argsort(depth)
        keep = (sx >= 0) & (sx < size) & (sy >= 0) & (sy < size)
        order = order[keep[order]]
        img = np.full((size, size, 3), 20, np.uint8)
        img[sy[order], sx[order]] = colours[order].astype(np.uint8)
        tiles.append(Image.fromarray(img))
    sheet = Image.new('RGB', (size * 4, size))
    for i, tile in enumerate(tiles):
        sheet.paste(tile, (i * size, 0))
    sheet.save(path, quality=90)


def cluster(verts, faces, colours, cell):
    """Merge every point that falls in the same grid cell, and drop the faces that collapse."""
    key = np.floor(verts / cell).astype(np.int64)
    _, inverse, count = np.unique(key, axis=0, return_inverse=True, return_counts=True)
    inverse = inverse.ravel()
    points = np.zeros((len(count), 3)); np.add.at(points, inverse, verts); points /= count[:, None]
    cols = np.zeros((len(count), 3)); np.add.at(cols, inverse, colours); cols /= count[:, None]
    f = inverse[faces]
    f = f[(f[:, 0] != f[:, 1]) & (f[:, 1] != f[:, 2]) & (f[:, 0] != f[:, 2])]
    _, first = np.unique(np.sort(f, axis=1), axis=0, return_index=True)
    f = f[first]
    used = np.unique(f)
    remap = -np.ones(len(points), int); remap[used] = np.arange(len(used))
    return points[used], remap[f], cols[used]


def face_outward(source_verts, points, faces):
    """Flip the faces that point inward. Outside is whatever a corner of the box can reach without crossing the surface."""
    r = (source_verts.max(0) - source_verts.min(0)).max() / 170
    lo = source_verts.min(0) - 4 * r
    dims = np.ceil((source_verts.max(0) - lo) / r).astype(int) + 5
    grid = np.zeros(dims, bool)
    gi = np.floor((source_verts - lo) / r).astype(int)
    grid[gi[:, 0], gi[:, 1], gi[:, 2]] = True
    wall = ndimage.binary_dilation(grid, iterations=2)
    labels, _ = ndimage.label(~wall)
    outside = labels == labels[0, 0, 0]

    def is_outside(p):
        q = np.clip(np.floor((p - lo) / r).astype(int), 0, dims - 1)
        return outside[q[:, 0], q[:, 1], q[:, 2]]

    a, b, c = points[faces[:, 0]], points[faces[:, 1]], points[faces[:, 2]]
    normal = np.cross(b - a, c - a)
    normal /= np.maximum(np.linalg.norm(normal, axis=1, keepdims=True), 1e-12)
    centre = (a + b + c) / 3
    score = np.zeros(len(faces))
    for step in (4, 5, 7, 10, 14):
        score += is_outside(centre + normal * r * step).astype(float) - is_outside(centre - normal * r * step).astype(float)
    flip = score < 0
    faces = faces.copy(); faces[flip] = faces[flip][:, [0, 2, 1]]
    return faces, int(flip.sum())


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('source'); ap.add_argument('out')
    ap.add_argument('--triangles', type=int, default=14000, help='the most triangles the game model may have')
    ap.add_argument('--views', help='write a four-view check picture here')
    a = ap.parse_args()

    verts, faces, colours = load(a.source)
    print(f'source: {len(faces):,} triangles, {len(verts):,} points')
    if a.views:
        four_views(verts, colours, a.views); print('wrote', a.views)

    size = (verts.max(0) - verts.min(0)).max()
    lo, hi = size / 2000, size / 10          # the grid cell: too fine keeps too many triangles, too coarse loses the shape
    for _ in range(18):
        cell = (lo * hi) ** 0.5
        points, f, cols = cluster(verts, faces, colours, cell)
        if len(f) > a.triangles: lo = cell
        else: hi = cell
    points, f, cols = cluster(verts, faces, colours, hi)
    f, flipped = face_outward(verts, points, f)
    print(f'game model: {len(f):,} triangles, {len(points):,} points, {flipped:,} faces turned outward')

    rgba = np.concatenate([np.clip(cols, 0, 255), np.full((len(cols), 1), 255.0)], axis=1).astype(np.uint8)
    trimesh.Trimesh(vertices=points, faces=f, vertex_colors=rgba, process=False).export(a.out)
    print('wrote', a.out)


if __name__ == '__main__':
    main()
