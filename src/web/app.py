"""API cho front end: POST /api/analyze nhận file .zip -> trả JSON netlist + schematic SVG."""
import tempfile, zipfile
from pathlib import Path
from flask import Flask, request, jsonify
from src.core.loader import load_board
from src.core.netlist import extract_netlist
from src.core.evaluate import ground_truth, score
from src.schematic.render import render_svg

app = Flask(__name__)


@app.post('/api/analyze')
def analyze():
    f = request.files.get('file')
    if not f or not f.filename.lower().endswith('.zip'):
        return jsonify(error='Hãy tải lên 1 file .zip chứa Gerber + drill (+ .pos)'), 400
    with tempfile.TemporaryDirectory() as tmp:
        zipfile.ZipFile(f.stream).extractall(tmp)
        try:
            board = load_board(Path(tmp))
            result = extract_netlist(board)
        except Exception as e:
            return jsonify(error=str(e)), 422
        truth = ground_truth({'top': board['top'], 'bottom': board['bottom']})
        result['score'] = score(result, truth) if truth else None
        result['schematic_svg'] = render_svg(result)
        result['layers_svg'] = {'top': str(board['top'].to_svg()), 'bottom': str(board['bottom'].to_svg())}
    return jsonify(result)


if __name__ == '__main__':
    app.run(debug=True)