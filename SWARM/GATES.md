# Lane Gates

Each lane has a **micro gate** - fast QA checks that don't slow you down.
Gates are acceptance criteria. Task isn't DONE until gate passes.

---

## KERNEL Gate

| Check | Description |
|-------|-------------|
| Correctness | Matches CPU reference within tolerance (e.g., `atol=1e-5`) |
| Benchmark | Runs one shape case without crash |

```python
# Example gate
assert torch.allclose(gpu_out, cpu_ref, atol=1e-5)
benchmark.run(shape=(1024, 1024))
```

---

## ML Gate

| Check | Description |
|-------|-------------|
| Unit tests | Critical functions have tests OR smoke-run passes |
| Import check | No import breaks, config loads |

```python
# Example gate
python -c "from model import Model; Model(cfg).forward(batch)"
pytest tests/test_model.py -x
```

---

## QUANT Gate

| Check | Description |
|-------|-------------|
| Deterministic | Same output for fixed seed + small dataset slice |
| Sanity | No lookahead, no NaNs, no future data leakage |

```python
# Example gate
assert not np.isnan(signal).any()
assert signal.index[0] >= data.index[0]  # no lookahead
```

---

## DEX Gate

| Check | Description |
|-------|-------------|
| Dry-run | TX builder creates valid transaction (or sim call works) |
| Safety | Destination allowlist, slippage bounds, amount limits |

```python
# Example gate
tx = builder.build(dry_run=True)
assert tx.destination in ALLOWLIST
assert slippage <= MAX_SLIPPAGE
```

---

## INTEGRATION Gate

| Check | Description |
|-------|-------------|
| Wire test | Modules connect without error |
| CLI check | `--help` works, config parses |

```bash
# Example gate
python main.py --help
python -c "from config import load; load('config.yaml')"
```

---

## Gate Rules

1. **Every task includes gate checkboxes** - in Acceptance Criteria
2. **Gate must be runnable in <30 seconds** - fast feedback
3. **Zergling checks gate before reporting DONE**
4. **PARTIAL if gate fails** - note which check failed
