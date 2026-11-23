import sys, matplotlib.pyplot as plt
from src.core.loader import load_board
from src.core.geometry import layer_to_islands

board = load_board(sys.argv[1])
fig, axes = plt.subplots(1, 2, figsize=(12, 5))
for ax, side in zip(axes, ['top', 'bottom']):
    for i, poly in enumerate(layer_to_islands(board[side])):
        x, y = poly.exterior.xy
        ax.fill(x, y, alpha=0.6)
        c = poly.representative_point()
        ax.text(c.x, c.y, str(i), fontsize=9)
    for x, y, d, _ in board['drills']:
        ax.add_patch(plt.Circle((x, y), d / 2, color='black'))
    ax.set_title(side); ax.set_aspect('equal')
plt.savefig('islands.png', dpi=120); print('Đã lưu islands.png')