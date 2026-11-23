"""Bước 5: Đo độ chính xác. Đáp án lấy từ thuộc tính netlist X2 (TO.N) KiCad ghi trong Gerber.
Thuật toán ở netlist.py KHÔNG đọc các thuộc tính này; chỉ file này đọc để chấm điểm."""
from itertools import combinations


def ground_truth(gerber_files):
    """{(x, y, side): tên_net_thật} lấy từ %TO.N%."""
    truth = {}
    for side, g in gerber_files.items():
        for obj in g.objects:
            if type(obj).__name__ == 'Flash' and '.N' in obj.attrs and '.P' in obj.attrs:
                truth[(round(obj.x, 4), round(obj.y, 4), side)] = obj.attrs['.N'][0]
    return truth


def score(result, truth):
    pred = {(p['x'], p['y'], p['side']): p['net'] for p in result['pads']}
    keys = sorted(set(pred) & set(truth))
    tp = fp = fn = 0
    for a, b in combinations(keys, 2):          # xét từng cặp pad: cùng net hay khác net?
        same_pred = pred[a] is not None and pred[a] == pred[b]
        same_true = truth[a] == truth[b]
        tp += same_pred and same_true
        fp += same_pred and not same_true
        fn += (not same_pred) and same_true
    precision = tp / (tp + fp) if tp + fp else 1.0
    recall = tp / (tp + fn) if tp + fn else 1.0
    f1 = 2 * precision * recall / (precision + recall) if precision + recall else 0.0

    def groups(m):
        g = {}
        for k in keys:
            g.setdefault(m[k], set()).add(k)
        return {frozenset(v) for v in g.values()}
    true_g, pred_g = groups(truth), groups(pred)
    exact = len(true_g & pred_g) / len(true_g) if true_g else 1.0
    return {'pads_matched': len(keys), 'pads_truth': len(truth),
            'precision': precision, 'recall': recall, 'f1': f1, 'net_exact_match': exact}