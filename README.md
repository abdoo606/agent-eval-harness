# agent-eval-harness

Rubric-based scoring for coding-agent transcripts — the core artifact of the
"evaluate whether the model thinks like a great engineer" work.

Zero dependencies (stdlib only), Python 3.9+.

## What problem it solves

Evaluating an agent transcript is a judgment call, and judgment calls drift:
two reviewers of the same transcript disagree, weights get eyeballed, and
"looks fine" replaces a defended score. This tool makes the rubric explicit
(weighted criteria with score anchors), computes a reproducible weighted score,
and refuses to hide a criterion that nobody scored.

## Usage

```bash
python -m agenteval check-rubric --rubric sample_data/rubric.json
python -m agenteval score --rubric sample_data/rubric.json \
                          --scores sample_data/scores.json --json
python -m agenteval score ... --strict   # exit 1 on incomplete rubric
```

## Design notes

- **Weights are relative.** `3/1` and `30/10` produce identical scores, so a
  rubric can be rescaled without invalidating historical evaluations.
- **Missing ≠ zero.** An unscored criterion is excluded from the mean and
  reported in `missing`; `--strict` turns that into a non-zero exit code so it
  cannot leak into a batch run unnoticed.
- **Scores are validated at the boundary.** Unknown criteria, duplicate
  evaluations and out-of-range scores raise instead of being coerced.

## Tests

```bash
python -m unittest discover -s tests -v
```
