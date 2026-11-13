# lendwatch-th

Research code for **detection-driven supervision of illegal digital lending in Thailand**.
It is the companion to the paper *The Reporting-Propensity Trap* and implements Paper 1
of that design: find lending apps and sites from public data, check them against the
allow-list of licensed lenders, link them to the operators behind them, rank them for
human review, and estimate how many operators no data source sees.

> **What this is not.** A score is a queue position for a human reviewer, never a
> finding that an app is illegal. Legal figures in `lendwatch/config.py` (interest
> ceilings, platform rules) were written from memory and must be verified against
> current Bank of Thailand, Ministry of Finance, Google and Apple texts before use.

## Quick start (offline, synthetic data)

```bash
pip install -r requirements.txt
python -m lendwatch demo --out outputs_demo      # full pipeline on a synthetic ecosystem
python -m pytest -q                              # 28 tests
```

The demo builds an invented market with known ground truth (300 illegal operators, 60
licensed lenders, plus cooperatives, pay-later firms and calculator apps that look like
unlicensed lenders but are not) and prints how the pipeline did against the truth.
With the default seed:

| Quantity | Value |
| --- | --- |
| True illegal operators | 300 |
| Observed on at least one list | 236 |
| Estimated total (log-linear, model-averaged) | 281, 95% CI 263-308 |
| High-tier precision / recall (rule score) | 0.998 / 0.889 |
| Medium tier | 88 artefacts: illegal and legitimate mixed, which is why humans review it |

These numbers show that the plumbing works. They say **nothing** about accuracy on
real data, where operators adapt and text is messier.

## Real data

```bash
# 1. Build the allow-list from the official BOT and Fiscal Policy Office lists
cp data/licensed_registry_template.csv data/licensed_registry.csv   # then fill it in

# 2. Collect public listings (needs network; Google Play needs google-play-scraper)
python -m lendwatch collect --sources google_play app_store web --max 100 --out artefacts.jsonl

# 3. Analyse
export LENDWATCH_SALT="keep-this-secret-and-stable"
python -m lendwatch analyse --artefacts artefacts.jsonl \
       --registry data/licensed_registry.csv --out outputs
#    optional: --labels reviewer_labels.csv   (columns: artefact_id,label ; 1 = illegal)
```

Complaints, ads or bank typology hits can be added as extra artefacts with
`"source": "complaint"` or `"ad"`; give them `mentions_artefacts`, `line_ids`, `phones`
or `bank_accounts` so they link to operators. They then count as extra lists in the
population estimate.

## Outputs

| File | Content |
| --- | --- |
| `watchlist.csv` | One row per artefact, highest risk first, with every reason and its points |
| `operators.csv` | One row per linked operator: members, sources, link types, status |
| `mse.json` | Hidden-population estimates: Chapman, Chao lower bound, log-linear models |
| `cases/*.md` | One-page evidence pack per high-risk artefact, with legal hooks to consider |
| `evidence/` | Raw snapshots and a hash-chained manifest (`EvidenceStore.verify()`) |
| `summary.md` | Counts, estimates and, if labels exist, evaluation |

## How it works

| Step | Module | Notes |
| --- | --- | --- |
| Collect | `collectors.py` | Google Play, iTunes Search API, Certificate Transparency logs, landing pages. Public data, rate-limited, robots.txt respected, reviewer names dropped |
| Allow-list match | `registry.py` | Registered app ids and own domains are authoritative. A matching name or self-declared website is only a claim (`licensed_name`) and is flagged for rent-a-licence or impersonation checks |
| Red flags | `features.py`, `rates.py` | Thai/English rate parsing with annualisation (Thai digits, "ร้อยละ", per-day/month cues, flat fee over a short tenor), tenor, marketing phrases, sensitive permissions, harm terms in reviews, developer metadata |
| Operator linkage | `linkage.py` | Shared developer account or e-mail, signing certificate, privacy-policy URL, own domain, LINE id, salted hashes of phone and account numbers, explicit references. Optional near-duplicate text links |
| Triage score | `scoring.py` | Additive 0-100 index with reasons; logistic regression on reviewer labels to re-estimate weights; cost-sensitive threshold |
| Hidden population | `mse.py` | Multiple systems estimation over the lists that saw each operator |
| Evidence | `evidence.py` | SHA-256 of every snapshot, UTC time, append-only hash chain |

## Reading the population estimate

Two errors push in opposite directions, and the demo reports both:

* **Linkage splits** (one operator recorded as two clusters) inflate the estimate.
* **Uneven catchability** (some operators are harder to see on every list) deflates it.

`oracle_linkage_mse_estimate` in the demo summary re-runs the estimator with perfect
linkage, which isolates the second error. On real data, audit a random sample of links,
run the estimate on reviewer-confirmed operators only, use short time windows, and
report the Chao bound and the log-linear estimate side by side.

## Safeguards built in

* Watches operators' public conduct, not borrowers. No log-ins, no private content, no
  contact with operators, no test borrowing.
* Analysis tables never contain phone or account numbers: linkage uses salted hashes,
  and the salt stays with the authority. Raw snapshots hold pages as published and
  belong in an access-controlled evidence store.
* Registered channels of licensees are never placed in the unlicensed queue.
* Known false-positive classes are in the demo on purpose: cooperatives, pay-later
  providers missing from the registry, loan calculators. Widen the registry to other
  regulators' lists before trusting "no licence match".
* Check platform terms of service; prefer official data feeds and data-sharing
  agreements to crawling. Publish methods and aggregates; keep live watchlists and
  exact thresholds restricted.

## Limits

* The collectors could not be run in the environment where this code was written (no
  access to the stores), so they are untested against live responses. Expect to adjust
  field names when store layouts change.
* Keyword dictionaries are a starting point; refresh them from reviewer feedback.
* Messaging channels (LINE, Telegram) are closed; only their entry points are seen.
* APK analysis (permissions from manifests, signing certificates) is not included;
  `signing_cert_sha256` is already a linkage key if you supply it.

## Layout

```
lendwatch/   config, textutils, rates, registry, features, linkage, scoring, mse,
             evidence, collectors, demo, pipeline, cli
tests/       rate parsing, Thai normalisation, registry matching, estimators, end-to-end
data/        licensed_registry_template.csv
sample_output/  outputs of the default demo run
```
