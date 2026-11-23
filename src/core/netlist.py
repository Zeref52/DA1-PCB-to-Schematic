"""Bước 3-4: Tìm net bằng đồ thị liên thông, gán pad vào linh kiện, xuất netlist."""
import math
import networkx as nx
from shapely.geometry import Point
from shapely.strtree import STRtree
from .geometry import layer_to_islands, extract_pads, courtyard_polygons


def build_nets(board):
    islands = {'top': layer_to_islands(board['top']), 'bottom': layer_to_islands(board['bottom'])}
    trees = {side: STRtree(polys) for side, polys in islands.items()}   # cây không gian: tìm đảo chứa điểm cho nhanh

    G = nx.Graph()
    for side, polys in islands.items():           # mỗi đảo đồng = 1 nút của đồ thị
        G.add_nodes_from((side, i) for i in range(len(polys)))

    for x, y, dia, plated in board['drills']:     # lỗ khoan có mạ nối đảo mặt trên với đảo mặt dưới
        if plated is False:
            continue
        hole = Point(x, y).buffer(dia / 2)
        hits = [(side, int(i)) for side, tree in trees.items()
                for i in tree.query(hole, predicate='intersects')]
        for a, b in zip(hits, hits[1:]):
            G.add_edge(a, b)

    node_to_net = {}
    for k, comp in enumerate(nx.connected_components(G)):
        for node in comp:
            node_to_net[node] = k
    return islands, trees, node_to_net


def nearest_component(p, components, max_dist, same_side_only):
    best, best_d = None, max_dist
    for c in components:
        if same_side_only and c['side'] != p['side']:
            continue
        d = math.dist((p['x'], p['y']), (c['x'], c['y']))
        if d < best_d:
            best, best_d = c, d
    return best


def assign_pads(pads, components, courtyards=None, max_dist=5.0):
    """Gán pad vào linh kiện.
    Cách chính: dùng viền courtyard. Footprint nào có điểm gốc (.pos) nằm trong viền
    thì viền đó thuộc footprint; pad nằm trong viền nào thì thuộc footprint đó.
    Viền không chứa điểm gốc nào (ví dụ lỗ bắt vít không có trong .pos) -> pad để trống.
    Dự phòng (không có courtyard hoặc pad nằm ngoài mọi viền): linh kiện gần nhất trong max_dist mm."""
    courtyards = courtyards or {}
    zones = []                                     # (đa giác, mặt, linh kiện hoặc None)
    for side in ('top', 'bottom'):
        for poly in courtyard_polygons(courtyards.get(side)):
            inside = [c for c in components if c['side'] == side and poly.covers(Point(c['x'], c['y']))]
            comp = min(inside, key=lambda c: poly.centroid.distance(Point(c['x'], c['y']))) if inside else None
            zones.append((poly, side, comp))

    for p in pads:
        pt = Point(p['x'], p['y'])
        covering = [z for z in zones if z[0].covers(pt)]
        # ưu tiên viền cùng mặt với pad; không có thì lấy viền mặt kia
        # (pad xuyên lỗ, hoặc connector cạnh bo có pad SMD ở cả 2 mặt)
        hits = [z for z in covering if z[1] == p['side']] or covering
        if hits:
            poly, side, comp = min(hits, key=lambda h: h[0].area)   # viền nhỏ nhất = sát nhất
            p['ref'] = comp['ref'] if comp else None
        else:
            same_only = p['function'] != 'ComponentPad'
            best = (nearest_component(p, components, max_dist, same_only)
                    or nearest_component(p, components, max_dist, False))
            p['ref'] = best['ref'] if best else None
    # đánh số pad trong từng linh kiện theo thứ tự trái->phải (CHƯA trùng số chân thật)
    by_ref = {}
    for p in pads:
        by_ref.setdefault(p['ref'], []).append(p)
    for ref, ps in by_ref.items():
        for i, p in enumerate(sorted(ps, key=lambda q: (q['x'], q['y'])), 1):
            p['name'] = f"{ref}.{i}" if ref else f"?{i}"
    return pads


def extract_netlist(board):
    islands, trees, node_to_net = build_nets(board)
    pads = extract_pads(board['top'], 'top')
    seen = {(p['x'], p['y']) for p in pads}
    # pad xuyên lỗ (THT) xuất hiện ở cả 2 lớp -> chỉ giữ 1 bản (mặt trên)
    pads += [p for p in extract_pads(board['bottom'], 'bottom') if (p['x'], p['y']) not in seen]
    assign_pads(pads, board['components'], board.get('courtyards'))

    groups = {}
    for p in pads:
        side = p['side']
        idx = trees[side].query(Point(p['x'], p['y']), predicate='intersects')
        p['net'] = node_to_net[(side, int(idx[0]))] if len(idx) else None
        groups.setdefault(p['net'], []).append(p)

    # đặt tên net gọn: N1 là net có nhiều pad nhất (thường là GND), N2 tiếp theo...
    ordered = sorted(groups.items(), key=lambda kv: -len(kv[1]))
    nets = []
    for k, (net_id, ps) in enumerate(ordered, 1):
        name = f"N{k}" if net_id is not None else "NC"
        for p in ps:
            p['net'] = name
        nets.append({'name': name, 'pads': sorted(p['name'] for p in ps)})
    return {'components': board['components'], 'pads': pads, 'nets': nets}