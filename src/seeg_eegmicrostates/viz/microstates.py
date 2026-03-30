from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


def plot_microstate_templates(model: dict[str, object], output_path: str | Path) -> Path:
    path = Path(output_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    centers = np.asarray(model["cluster_centers"], dtype=float)
    channels = [str(name) for name in np.asarray(model["channel_names"])]
    figure, axis = plt.subplots(figsize=(8, 4))
    image = axis.imshow(centers, aspect="auto", cmap="RdBu_r")
    axis.set_xlabel("Channel")
    axis.set_ylabel("Microstate")
    axis.set_xticks(np.arange(len(channels)))
    axis.set_xticklabels(channels, rotation=90)
    axis.set_title(f"Microstate templates ({model.get('branch', 'main')})")
    figure.colorbar(image, ax=axis, shrink=0.8)
    figure.tight_layout()
    figure.savefig(path, dpi=150)
    plt.close(figure)
    return path
