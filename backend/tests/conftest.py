from __future__ import annotations

import pandas as pd
import pytest


@pytest.fixture
def sample_csv(tmp_path):
    df = pd.DataFrame(
        {
            "region": ["North", "South", "North", "West", "South"],
            "revenue": [100, 250, 175, 300, 50],
            "units": [1, 5, 3, 6, 1],
        }
    )
    path = tmp_path / "sales.csv"
    df.to_csv(path, index=False)
    return str(path)
