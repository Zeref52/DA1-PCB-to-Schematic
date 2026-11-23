import json, sys
from src.core.loader import load_board
from src.core.netlist import extract_netlist
from src.core.evaluate import ground_truth, score, component_truth, component_accuracy
from src.schematic.render import render_svg

board = load_board(sys.argv[1])
result = extract_netlist(board)
print(json.dumps(result['nets'], indent=2, ensure_ascii=False))

layers = {'top': board['top'], 'bottom': board['bottom']}
s = score(result, ground_truth(layers))
s['component_accuracy'] = component_accuracy(result, component_truth(layers))
print(s)

with open('schematic.svg', 'w', encoding='utf-8') as f:
    f.write(render_svg(result))
print('Đã lưu schematic.svg')