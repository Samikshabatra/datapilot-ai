Your previous code failed when executed. Fix it.

## Dataset summary
{schema}

## Question
{question}

## Your previous code
```python
{previous_code}
```

## The error it produced
```
{error}
```

## Instructions
- Diagnose the actual cause from the traceback, do not guess blindly.
- If the error means the question cannot be answered from this data (e.g. it refers
  to a column that does not exist and has no clear equivalent), do NOT keep retrying.
  Instead return a single fenced ```python block whose only content is:
  `result = "CLARIFY: <one sentence saying what is missing or ambiguous>"`
- Otherwise return ONLY the corrected ```python code block, starting with a
  one-line `# reasoning:` comment describing what you changed and why.
