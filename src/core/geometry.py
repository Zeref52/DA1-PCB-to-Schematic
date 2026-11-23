"""Bước 2: Biến các đối tượng Gerber (đường mạch, pad, vùng đồng) thành đa giác shapely."""
import gerbonara.graphic_primitives as gp
from shapely.geometry import Polygon, LineString
from shapely.ops import unary_union, polygonize

def primitive_to_polygon(prim):
    """Một 'primitive' (hình cơ bản) của gerbonara -> 1 đa giác shapely, đơn vị mm."""
    if isinstance(prim, gp.Line):
        # Đường mạch = đoạn thẳng có bề rộng -> phình đoạn thẳng ra mỗi bên width/2
        return LineString([(prim.x1, prim.y1), (prim.x2, prim.y2)]).buffer(prim.width / 2)
    # Các hình khác (chữ nhật, tròn, cung, vùng) đổi sang ArcPoly rồi xấp xỉ cung bằng đoạn thẳng
    pts = prim.to_arc_poly().approximate_arcs().outline
    return Polygon(pts).buffer(0) if len(pts) >= 3 else None   # buffer(0) sửa đa giác tự cắt


def layer_to_islands(gerber):
    """Gộp toàn bộ đồng của một lớp, trả về danh sách 'đảo đồng' (các mảng đồng rời nhau)."""
    copper = Polygon()
    for obj in gerber.objects:                     # giữ đúng thứ tự: vẽ đồng (dark) rồi khoét (clear)
        polys = [p for p in (primitive_to_polygon(pr) for pr in obj.to_primitives(unit='mm')) if p]
        if not polys:
            continue
        shape = unary_union(polys)
        copper = copper.union(shape) if obj.polarity_dark else copper.difference(shape)
    return list(copper.geoms) if hasattr(copper, 'geoms') else ([copper] if not copper.is_empty else [])


def pad_function(obj):
    """Đọc thuộc tính X2 '.AperFunction' của aperture: SMDPad, ComponentPad, ViaPad, Conductor..."""
    for key, val in getattr(obj.aperture, 'attrs', ()) or ():
        if key == '.AperFunction':
            return val[0]
    return None


def extract_pads(gerber, side):
    """Lấy các pad linh kiện (Flash không phải via) trên một lớp đồng."""
    pads = []
    for obj in gerber.objects:
        if type(obj).__name__ != 'Flash':
            continue
        func = pad_function(obj)
        if func in ('ViaPad', 'Conductor'):
            continue
        pads.append({'x': round(obj.x, 4), 'y': round(obj.y, 4), 'side': side, 'function': func})
    return pads


def courtyard_polygons(gerber):
    """Ghép các nét vẽ (đường thẳng, cung) của lớp Courtyard thành các đa giác khép kín.
    Mỗi đa giác là vùng chiếm chỗ của 1 footprint."""
    if gerber is None:
        return []
    segments = []
    for obj in gerber.objects:
        kind = type(obj).__name__
        lines = obj.approximate() if kind == 'Arc' else [obj] if kind == 'Line' else []
        for ln in lines:                               # cung được xấp xỉ bằng nhiều đoạn thẳng nhỏ
            segments.append(LineString([(round(ln.x1, 4), round(ln.y1, 4)), (round(ln.x2, 4), round(ln.y2, 4))]))
    if not segments:
        return []
    return [poly for poly in polygonize(unary_union(segments)) if poly.area > 0.01]