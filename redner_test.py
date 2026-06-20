import numpy as np
import matplotlib.pyplot as plt

w, h = 1000, 1000

grid = np.zeros((h, w), dtype=np.uint8)

plt.ion()
fig, ax = plt.subplots()
img = ax.imshow(grid, cmap="gray", vmin=0, vmax=255, animated=True)
ax.axis("off")

while True:
    grid[:] = np.random.randint(0, 256, size=(h, w), dtype=np.uint8)

    img.set_data(grid)
    fig.canvas.draw_idle()
    fig.canvas.flush_events()