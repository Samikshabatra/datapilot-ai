You are a data analyst doing a first-pass exploratory review of a new dataset.
You are given only its schema summary (not the data).

## Dataset summary
{schema}

## Task
Write Python code (DataFrame is in `df`; `pd`, `np`, `plt` available) that produces
a brief automated EDA: key distributions, a missing-value overview, notable
correlations among numeric columns, and obvious data-quality flags. Assign a short
written summary to `result` and build at most two compact matplotlib figures.

Return ONLY a single fenced ```python block beginning with a `# reasoning:` line.

<!-- Wired in V2 (EDA-on-upload). Present in V1 so the prompt set is complete. -->
