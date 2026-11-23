"""Bước 1: Đọc bộ file Gerber + drill + .pos của một bo mạch.
Nhận diện lớp bằng thuộc tính X2 '.FileFunction' ghi trong file (không phụ thuộc tên file)."""
import csv
import warnings
warnings.filterwarnings('ignore', category=SyntaxWarning, module='gerbonara')
from pathlib import Path
from gerbonara import GerberFile, ExcellonFile


def load_board(folder):
    """Trả về dict gồm lớp đồng mặt trên/dưới, danh sách lỗ khoan và linh kiện từ .pos."""
    folder = Path(folder)
    top = bottom = None
    for path in sorted(folder.glob('*.gbr')):
        g = GerberFile.open(path)
        func = g.file_attrs.get('.FileFunction', ())     # ví dụ ('Copper', 'L1', 'Top')
        if func and func[0] == 'Copper':
            if 'Top' in func:
                top = g
            elif 'Bot' in func:
                bottom = g
    if top is None or bottom is None:
        raise ValueError("Không tìm thấy lớp đồng Top/Bot. Hãy xuất Gerber với 'Use extended X2 format'.")

    drills = []                                          # mỗi lỗ: (x, y, đường kính, có mạ không)
    for path in sorted(folder.glob('*.drl')):
        plated = 'NPTH' not in path.name.upper()         # KiCad tách file: ...-PTH.drl và ...-NPTH.drl
        for obj in ExcellonFile.open(path).objects:
            drills.append((obj.x, obj.y, obj.aperture.diameter, plated))

    pos_files = list(folder.glob('*pos*.csv')) + list(folder.glob('*.pos'))
    components = load_pos(pos_files[0]) if pos_files else []
    return {'top': top, 'bottom': bottom, 'drills': drills, 'components': components}


def load_pos(path):
    """Đọc file vị trí linh kiện KiCad dạng CSV (Ref,Val,Package,PosX,PosY,Rot,Side)."""
    comps = []
    with open(path, newline='', encoding='utf-8') as f:
        for row in csv.DictReader(f):
            comps.append({'ref': row['Ref'], 'value': row['Val'], 'footprint': row['Package'],
                          'x': float(row['PosX']), 'y': float(row['PosY']),
                          'rot': float(row['Rot']), 'side': row['Side']})
    return comps