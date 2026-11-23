import json, sys
from src.core.loader import load_board
from src.core.netlist import extract_netlist
from src.core.evaluate import ground_truth, score

board = load_board(sys.argv[1])
result = extract_netlist(board)
print(json.dumps(result['nets'], indent=2, ensure_ascii=False))
truth = ground_truth({'top': board['top'], 'bottom': board['bottom']})
print(score(result, truth))