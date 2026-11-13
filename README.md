# Regulating Non-Bank Lenders in the Digital Age

**Thanatchon Chongmankhong** · Working paper, November 2026

A comparative study of how twelve regimes regulate non-bank consumer lenders, a theory of
complaint-driven enforcement against unlicensed lenders, and a three-phase reform roadmap for
Thailand. The repository holds the paper, the code that produces every figure and number in
it, and `lendwatch-th`, an open-source pipeline for detecting unlicensed digital lenders.

📄 **Paper:** [`paper/paper.pdf`](paper/paper.pdf)

![Two enforcement pipelines](paper/figs/fig1_pipeline.png)

## Contents

| Folder | What it holds |
| --- | --- |
| `paper/` | LaTeX source, compiled PDF and all figures (vector PDF and PNG) |
| `analysis/` | `sim.py` (Monte Carlo and model results), `validate_lendwatch.py` (pipeline validation on 30 synthetic markets), `figures.py` (all figures), and the numerical results in `data/` |
| `lendwatch-th/` | Detection pipeline: collectors, allow-list matching, Thai/English rate parsing, operator linkage, risk scoring, multiple systems estimation, evidence integrity; 28 tests |

## Reproduce

Python 3.10+ and a TeX Live installation with `pdflatex`.

```bash
pip install -r analysis/requirements.txt

python analysis/sim.py                 # Monte Carlo and model results -> analysis/data/
python analysis/validate_lendwatch.py  # 30 synthetic markets, about 1 minute -> analysis/data/
python analysis/figures.py             # all figures -> paper/figs/

cd paper && pdflatex paper.tex && pdflatex paper.tex   # twice, for cross-references

cd ../lendwatch-th && python -m pytest -q              # pipeline tests
```

The simulation uses a fixed random seed, so results match the paper exactly.

## Important caveats

- **Institutional facts need verification.** Laws, dates, rate ceilings and references were
  compiled from secondary knowledge without access to primary databases. Check each one
  against the original source before citing it. The coding of the twelve regimes is
  provisional and has not yet been validated by local experts.
- **All quantitative results are simulated.** Model results, the Monte Carlo and the pipeline
  validation use synthetic data and hypothetical parameters. They illustrate mechanisms and
  are not estimates for the Thai market.
- **The live collectors in `lendwatch-th` have not been run against real app stores.** Check
  platform terms of service before collecting, and treat every risk score as a queue position
  for human review, never a finding of illegality.
- **Preparation.** Drafting, simulations and figures were prepared with the assistance of an
  AI system (Claude, Anthropic); the author takes responsibility for the content.

## Citation

```bibtex
@misc{chongmankhong2026nonbank,
  author = {Chongmankhong, Thanatchon},
  title  = {Regulating Non-Bank Lenders in the Digital Age: A Comparative Study of Twelve
            Regimes, a Theory of Complaint-Driven Enforcement, and a Roadmap for Thailand},
  year   = {2026},
  note   = {Working paper}
}
```

## License

No license has been chosen yet. Until one is added, others may view the repository but have
no right to reuse the code or text.
