import numpy as np
import scipy.spatial as ss
import numpy as np
import random
import math

def transform_from3pt(pt0, pt1, pt2):
    matB = np.identity(4)
    e1 = pt1 - pt0
    e1 /= np.linalg.norm(e1)
    v02 = pt2 - pt0
    e2 = v02 -  np.dot(v02, e1) * v02
    e2 /= np.linalg.norm(e2)
    e3 = np.cross(e1,e2)
    matB[0:3,0] = e1
    matB[0:3,1] = e2
    matB[0:3,2] = e3

    matT = np.identity(4)
    matT[3,0] = -pt0[0]
    matT[3,1] = -pt0[1]
    matT[3,2] = -pt0[2]

    return matT @ matB


def sqdistance(pt1, pt2):
  return math.sqrt((pt1[0] - pt2[0])**2 + (pt1[1] - pt2[1])**2)


def divideby_distance(pt1, pt2, reflength):
  dist = sqdistance(pt1, pt2)
  vec12 = pt2 - pt1
  div_num = int(dist/reflength) + 1
  vec12 = vec12 / div_num

  points = []
  for i in range(1, div_num):
    points.append(pt1 + i * vec12)
  return points


def randompts_inside_polygon(num: int, poly):
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


def tessellate_2d(poly, reflength: float):
    """
    Tessellate 2d comvex resion delaunay trianguration 

    Args:
        poly (2dim-ndarray): [[x0,y0],[x1,y1],...]
        reflength (float): reference length, decide average density.
    """
    tess_points = []
    pts_num = len(poly)
    refarea = reflength**2 * 0.5

    # Corner & Edge
    for i, pti in enumerate(poly):
        # register corner
        tess_points.append(pti) 

        # register edge (divided)
        pt_next = poly[(i+1)%pts_num]
        tess_points += divideby_distance(pti, pt_next, reflength)

    # Inside
    # NOTE : ConvexPolygonの面積を簡単に求める方法忘れた。とりあえず三角形前提でゴリ押す。
    # TODO : 思い出して密度に応じた点の生成を行う。
    p0 = poly[0]; p1 = poly[1]; p2 = poly[2]
    inside_pts_num = int(np.cross(p1-p0, p2-p0) * 0.5 / refarea)
    inside_pts_num = max(inside_pts_num, 10)
    
    tess_points += randompts_inside_polygon(inside_pts_num, poly)

    return ss.Delaunay(tess_points)