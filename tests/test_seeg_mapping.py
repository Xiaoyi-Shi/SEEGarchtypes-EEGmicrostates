from __future__ import annotations

import pandas as pd

from seeg_eegmicrostates.seeg.bipolar_map import build_same_region_bipolar_map


def test_build_same_region_bipolar_map_keeps_only_same_region_pairs() -> None:
    atlas_df = pd.DataFrame(
        {
            "Channel": ["A1", "A2", "A3", "B1", "B2"],
            "AAL3": ["Right Hippocampus", "Right Hippocampus", "Right Amygdala", "N/A", None],
        }
    )
    mapping = build_same_region_bipolar_map(
        atlas_df,
        ["A1-A2", "A2-A3", "B1-B2"],
        patient_id="sub-01",
    )
    valid = mapping[mapping["valid_same_region"]]
    assert valid["bipolar_channel"].tolist() == ["A1-A2"]
    assert valid["region"].tolist() == ["Right Hippocampus"]
