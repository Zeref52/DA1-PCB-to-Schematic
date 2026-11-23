"""Bước 3-4: Tìm net bằng đồ thị liên thông, gán pad vào linh kiện, xuất netlist."""
import math
import networkx as nx
from shapely.geometry import Point
from shapely.strtree import STRtree
from .geometry import layer_to_islands, extract_pads


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


def assign_pads(pads, components, max_dist=50.0):
    """MVP: pad thuộc linh kiện có tâm (.pos) gần nhất.
    Ưu tiên linh kiện cùng mặt; nếu không có thì xét cả mặt kia
    (pad xuyên lỗ, hoặc connector cạnh bo có pad ở cả 2 mặt)."""
    def nearest(p, same_side_only):
        best, best_d = None, max_dist
        for c in components:
            if same_side_only and c['side'] != p['side']:
                continue
            d = math.dist((p['x'], p['y']), (c['x'], c['y']))
            if d < best_d:
                best, best_d = c, d
        return best

    for p in pads:
        same_only = p['function'] != 'ComponentPad'
        best = nearest(p, same_only) or nearest(p, False)
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
    assign_pads(pads, board['components'])

    nets = {}
    for p in pads:
        side = p['side']
        idx = trees[side].query(Point(p['x'], p['y']), predicate='intersects')
        net = node_to_net[(side, int(idx[0]))] if len(idx) else None
        p['net'] = net
        nets.setdefault(net, []).append(p['name'])
    return {
        'components': board['components'],
        'pads': pads,
        'nets': [{'name': f"N{k}", 'pads': sorted(v)} for k, v in sorted(nets.items(), key=lambda kv: str(kv[0]))],
    }