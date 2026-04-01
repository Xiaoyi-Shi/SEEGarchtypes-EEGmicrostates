from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
from pycrostates.cluster import ModKMeans


def plot_microstate_templates(model: ModKMeans, output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    figure = model.plot(show=False, block=False)
    figure.savefig(path, dpi=150)
    plt.close(figure)
    return path
