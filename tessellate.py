import math
import hashlib

import numpy as np
import scipy.spatial as ss


def transform_matrix_3pt(pt0, pt1, pt2):
    matB = np.identity(4)
    e1 = pt1 - pt0
    e1 /= np.linalg.norm(e1)
    v02 = pt2 - pt0
    e2 = v02 - np.dot(v02, e1) * v02
    e2 /= np.linalg.norm(e2)
    e3 = np.cross(e1, e2)
    matB[0:3, 0] = e1
    matB[0:3, 1] = e2
    matB[0:3, 2] = e3

    matT = np.identity(4)
    matT[3, 0] = -pt0[0]
    matT[3, 1] = -pt0[1]
    matT[3, 2] = -pt0[2]

    return matT @ matB


def distance_2pt(pt1, pt2):
    return math.sqrt(sum((pt1 - pt2)**2))


def divideby_distance(pt1, pt2, reflength):
    vec12 = pt2 - pt1
    div_num = int(distance_2pt(pt1, pt2)/reflength) + 1
    vec12 = vec12 / div_num
    points = []
    for i in range(1, div_num):
        points.append(pt1 + i * vec12)
    return points


def randompts_inside_polygon(num: int, poly):
    """Create random points inside input polygon

    Args:
        num (int): number of create points
        poly ((dim,n)ndarray): polygon corner points coordinate.

    Returns:
        points [(...,num) array-like]: random points inside polygon.
    """
    pts_num = len(poly)
    points = []

    for i in range(num):
        facs = np.random.rand(pts_num)
        sum_fac = np.sum(facs)

        sum_pt = facs[0] * poly[0]
        for fac, pt in zip(facs[1:], poly[1:]):
            sum_pt += fac * pt

        points.append(sum_pt / sum_fac)

    return points


class Vertex:
    """Mesh Vertex

    Attributes:
        x, y, z (float): 頂点座標成分
    """
    def __init__(self, x: float, y: float, z: float):
        self.x = x
        self.y = y
        self.z = z

    def to_array(self):
        return np.array([self.x, self.y, self.z])

    def to_localcoord(self, trans_matrix):
        """この頂点を2次元局所座標系へ変換

        Args:
            trans_matrix ((4,4)ndarray): 変換行列

        Returns:
            2次元局所座標[(2)ndarray]: trans_matrixに基づいて計算された2次元局所座標系
        """
        vec1 = np.array([self.x, self.y, self.z, 1.0])
        return (vec1 @ trans_matrix)[:2]


class TopologicalEdge:
    """Topological Edge
    順列を区別しないエッジの格納
    """
    def __init__(self, n1: int, n2: int):
        self.n1 = n1
        self.n2 = n2

    def __hash__(self):
        h1 = hashlib.sha224(hex(self.n1).encode()).digest()
        h2 = hashlib.sha224(hex(self.n2).encode()).digest()
        return hash(h1) + hash(h2)

    def __eq__(self, other):
        return hash(self) == hash(other)

    def __str__(self):
        return f"n1: {self.n1}, n2: {self.n2}"


def tessellate_mesh(vertices, faces, reflength):
    """Delaunay based refinement to input mesh

    Args:1
        vertices ((n,dim)ndarray): [[x1, y1, z1], [x2, y2, z2]...], float
        faces ((m,...)ndarray): [[n1_1, n2_1, n3_1], [n1_2, n2_2, n3_2]...]

    Notes:
        n: Vertices number
        m: Faces number

    Returns:
        tess_vertices [(n) array-like: Vertex]: 生成メッシュの頂点
        tess_triangles [(3,n) array-like: int]: 生成メッシュの頂点-頂点関係
    """
    # Initialize tessellated verticies collection
    refarea = reflength**2 * 0.5
    tess_vertices = []  # Result vertices collection
    tess_triangles = []  # Result triangle-vertices relation collection
    for pti in vertices:
        tess_vertices.append(Vertex(pti[0], pti[1], pti[2]))

    # Final vertex ID indicator
    vertex_count = len(tess_vertices)

    # Extract topological edges
    edge_set = set()
    for fi in faces:
        # collect edges
        edge_set.add(TopologicalEdge(fi[0], fi[1]))
        edge_set.add(TopologicalEdge(fi[1], fi[2]))
        edge_set.add(TopologicalEdge(fi[2], fi[0]))

    # Divide collected edges
    edge_vertexids = {}
    for ei in edge_set:
        # 分割された節点を細分化節点コレクションに追加
        mid_points = divideby_distance(vertices[ei.n1], vertices[ei.n2], reflength)
        vertexids = []
        for i, pti in enumerate(mid_points):
            tess_vertices.append(Vertex(pti[0], pti[1], pti[2]))
            vertexids.append(vertex_count)
            vertex_count += 1

        # 節点IDをそれぞれのエッジごとに保存
        edge_vertexids[ei] = vertexids

    # Facetごとの処理
    for fi in faces:
        face_vertex_ids = []  # 2次元座標の頂点に対応する3次元頂点のIDを格納
        face_vertices = []  # 2次元座標の頂点を格納

        # コーナー頂点を取得
        v1 = tess_vertices[fi[0]]
        v2 = tess_vertices[fi[1]]
        v3 = tess_vertices[fi[2]]
        # 頂点IDをコレクション
        face_vertex_ids.append(fi[0])
        face_vertex_ids.append(fi[1])
        face_vertex_ids.append(fi[2])
        # 局所平面座標系の変換マトリクスを取得
        matE = transform_matrix_3pt(v1.to_array(), v2.to_array(), v3.to_array())
        # コーナー頂点の二次元座標を計算して登録
        p1 = v1.to_localcoord(matE)
        p2 = v2.to_localcoord(matE)
        p3 = v3.to_localcoord(matE)
        face_vertices.append(p1)
        face_vertices.append(p2)
        face_vertices.append(p3)
        # 面積から内部節点の生成数を決定
        inside_pts_num = abs(int(np.cross(p2-p1, p3-p1) * 0.5 / refarea))

        # エッジ頂点を取得
        polygon_vertices = []
        for j in range(3):
            # 三角形の頂点座標をコレクション
            polygon_vertices.append(vertices[fi[j]])
            # エッジ上の頂点を取得してIDをコレクション
            vertexids_onedge = edge_vertexids[TopologicalEdge(fi[j], fi[(j+1) % 3])]
            # エッジ上の頂点の二次元座標を計算して登録
            for k in vertexids_onedge:
                face_vertex_ids.append(k)
                face_vertices.append(tess_vertices[k].to_localcoord(matE))

        # 内部節点の生成
        for pti in randompts_inside_polygon(inside_pts_num, np.array(polygon_vertices)):
            # 内部節点を生成して細分化節点コレクションに追加
            vi = Vertex(pti[0], pti[1], pti[2])
            tess_vertices.append(vi)
            # 節点IDをコレクション
            face_vertex_ids.append(vertex_count)
            vertex_count += 1
            # 生成節点を二次元座標に変換して登録
            face_vertices.append(vi.to_localcoord(matE))

        # Delaunay分割
        delaun_result = ss.Delaunay(face_vertices)

        # 単体(3角形)の節点IDを全体節点IDに変換してコレクション
        for facet in delaun_result.simplices:
            tess_triangles.append([face_vertex_ids[facet[0]],
                                   face_vertex_ids[facet[1]],
                                   face_vertex_ids[facet[2]]])

    return tess_vertices, tess_triangles
