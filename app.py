from flask import Flask
import ghhops_server as hs
import rhino3dm as rh
import numpy as np

from tessellate import transform_from3pt, tessellate_2d

# register hops app as middleware
app = Flask(__name__)
hops: hs.HopsFlask = hs.Hops(app)

# flask app can be used for other stuff directly
@app.route("/help")
def help():
    return "Welcome to Grashopper Hops for CPython!"

def scipytriangle_to_rhinomesh_transform(tri, tr:np.ndarray) -> rh.Mesh:
    """2d Delaunay Mesh with Scipy to 3d Rhino Mesh

    Args:
        tri (): scipy output delaunay mesh
        tr (4x4 ndarray): transform matrix(not inversed)

    Returns:
        rh.Mesh: 
    """
    mesh = rh.Mesh()
    invtr = np.linalg.inv(tr)

    # register vertex
    for pti in tri.points:
        pt_vec = np.array([pti[0], pti[1], 0, 1]) @ invtr
        mesh.Vertices.Add(pt_vec[0], pt_vec[1], pt_vec[2])
    # register face
    for simpl in tri.simplices:
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

    marged_mesh = rh.Mesh()

    for i in range(pts_num):
        pti = pl[i]
        pt_next = pl[(i+1)%pts_num]

        pt00 = np.array([pt.X, pt.Y, pt.Z, 1.0])
        pt11 = np.array([pti.X, pti.Y, pti.Z, 1.0])
        pt22 = np.array([pt_next.X, pt_next.Y, pt_next.Z, 1.0])
        
        matE = transform_from3pt(pt00[:3], pt11[:3], pt22[:3])
        p1 = pt00 @ matE
        p2 = pt11 @ matE
        p3 = pt22 @ matE

        poly = np.array([[p1[0], p1[1]], [p2[0], p2[1]], [p3[0], p3[1]]])
        tri = tessellate_2d(poly, 20.0)
        mesh_i = scipytriangle_to_rhinomesh_transform(tri, matE)

        marged_mesh.Append(mesh_i)

    return marged_mesh


if __name__ == "__main__":
    app.run(debug=True)