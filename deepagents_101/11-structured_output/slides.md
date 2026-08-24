---
marp: true
theme: default
paginate: true
size: 16:9
---

# Deep Agents 101

## Episode 11 — Structured Output

*Describe the shape you want and get a real Python object back — no regex required*

---

# Schema In

```python
class BookReview(BaseModel):
    """A structured verdict on a book."""
    title: str = Field(description="The title of the book being reviewed.")
    rating: int = Field(description="A rating from 1 to 5, where 5 is best.")
    one_liner: str = Field(description="A single sentence summarizing the verdict.")

agent = create_deep_agent(model=MODEL, response_format=BookReview)
```

- `Field(description=...)` is **sent to the model** — treat each one as a per-field instruction
- Keep schemas **flat and simple**; small models handle a few scalars far better than deep nesting

---

# Typed Object Out

```python
review = result["structured_response"]     # a BookReview, not a string
review.rating                              # 5
review.model_dump_json(indent=2)           # ready for an API or database
```

- Validation and serialization come free with Pydantic
- Structured output rides on the model following a schema — **smaller models drift**, so wrap the
  `invoke` in `try/except` and degrade gracefully instead of crashing

**Next (ep. 12):** memory within a conversation — checkpointers and `thread_id`.
