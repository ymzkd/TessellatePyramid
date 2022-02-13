from flask import Flask
import ghhops_server as hs
import rhino3dm as rh
import numpy as np

from tessellate import tessellate_mesh

# register hops app as middleware
app = Flask(__name__)
hops: hs.HopsFlask = hs.Hops(app)


# flask app can be used for other stuff directly
@app.route("/help")
def help():
    return "Welcome to Grashopper Hops for CPython!"


def triangles_to_rhinomesh_transform(vertices, triangles) -> rh.Mesh:
    """節点と面-節点関係からRhinoMeshを作成

    Args:
        vertices ([N] array-like: Vertex): N vertices 3d coordinate
        triangles ([3,M] array-like: int): M facet corner vertices index

    Returns:
        rhino3dm.Mesh: Converted Mesh
    """
    mesh = rh.Mesh()
    # register vertex
    for pti in vertices:
        mesh.Vertices.Add(pti.x, pti.y, pti.z)
    # register face
    for simpl in triangles:
        mesh.Faces.AddFace(simpl[0], simpl[1], simpl[2])

    return mesh


@hops.component(
    "/tessellate",
    name="Tessellate",
    description="Create tessellation from base objects",
    inputs=[
        hs.HopsCurve("PL", "PL", "Base polyline"),
        hs.HopsPoint("P", "P", "Top points"),
    ],
    outputs=[ 
        hs.HopsMesh("Mesh", "M", "Roof mesh")
    ],
)
def tessellate(crv: rh.Curve, pt: rh.Point3d) -> rh.Mesh:
    pl = crv.TryGetPolyline()
    pts_num = len(pl)-1

    vertices = [[pt.X, pt.Y, pt.Z]]
    faces = []
    for i in range(pts_num):
        vi1 = i + 1
        vi2 = (i + 1) % pts_num + 1
        faces.append([0, vi1, vi2])

        pti = pl[i]
        vertices.append([pti.X, pti.Y, pti.Z])

    ref_vertices, ref_triangles = \
        tessellate_mesh(np.array(vertices), np.array(faces), 20.0)

    return triangles_to_rhinomesh_transform(ref_vertices, ref_triangles)


if __name__ == "__main__":
    app.run(debug=True)