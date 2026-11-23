"""Bước 6: Vẽ schematic dạng 'nhãn net': mỗi linh kiện là 1 hộp, mỗi chân có nhãn tên net."""
import math
from html import escape


def _natural(ref):
    """Sắp xếp tự nhiên: R2 trước R10."""
    head = ref.rstrip('0123456789')
    tail = ref[len(head):]
    return (head, int(tail) if tail else 0)


def _pin_no(name):
    tail = name.split('.')[-1]
    return int(tail) if tail.isdigit() else 0


def render_svg(result, cols=4, box_w=120, pitch=22, gap=80):
    pads_by_ref = {}
    for p in result['pads']:
        if p['ref'] is not None:                       # pad không thuộc linh kiện nào (lỗ bắt vít...) thì bỏ qua
            pads_by_ref.setdefault(p['ref'], []).append(p)
    net_name = {pad: n['name'] for n in result['nets'] for pad in n['pads']}

    items = sorted(pads_by_ref.items(), key=lambda kv: _natural(kv[0]))
    parts, x0, y = [], gap + 20, 40
    for r0 in range(0, len(items), cols):             # vẽ theo từng hàng, mỗi hàng cao bằng hộp cao nhất
        row_items, row_h = items[r0:r0 + cols], 0
        for col, (ref, pads) in enumerate(row_items):
            x = x0 + col * (box_w + 2 * gap)
            pads = sorted(pads, key=lambda q: _pin_no(q['name']))
            n_rows = max(1, math.ceil(len(pads) / 2))
            h = n_rows * pitch * 2                       # chân lẻ bên trái, chân chẵn bên phải
            parts.append(f'<rect x="{x}" y="{y}" width="{box_w}" height="{h}" fill="none" stroke="black"/>')
            parts.append(f'<text x="{x + box_w/2}" y="{y - 6}" text-anchor="middle" font-weight="bold">{escape(ref)}</text>')
            for i, p in enumerate(pads):
                left = i % 2 == 0
                py = y + (i // 2) * pitch * 2 + pitch
                sx, ex = (x, x - 30) if left else (x + box_w, x + box_w + 30)
                tx, anchor = (ex - 4, 'end') if left else (ex + 4, 'start')
                parts.append(f'<line x1="{sx}" y1="{py}" x2="{ex}" y2="{py}" stroke="black"/>')
                parts.append(f'<text x="{tx}" y="{py + 4}" text-anchor="{anchor}" fill="blue" font-size="12">'
                             f'{escape(net_name.get(p["name"], "?"))}</text>')
                parts.append(f'<text x="{sx + (6 if left else -6)}" y="{py + 4}" '
                             f'text-anchor="{"start" if left else "end"}" font-size="10">{_pin_no(p["name"])}</text>')
            row_h = max(row_h, h)
        y += row_h + 60
    width = x0 * 2 + cols * (box_w + 2 * gap)
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{y}" '
            f'font-family="sans-serif" style="background:white">' + ''.join(parts) + '</svg>')