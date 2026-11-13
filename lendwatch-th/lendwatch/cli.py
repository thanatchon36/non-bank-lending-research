"""Command line.

    python -m lendwatch demo     --out outputs_demo
    python -m lendwatch collect  --sources google_play app_store web --max 100 --out artefacts.jsonl
    python -m lendwatch analyse  --artefacts artefacts.jsonl --registry data/licensed_registry.csv --out outputs

Set LENDWATCH_SALT (kept by the authority) so hashed phone and account numbers link
across runs. Without it a random salt is used and hashes are not comparable later.
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import secrets
import sys

from .pipeline import render_summary, run_analysis
from .registry import LicensedRegistry

REGISTRY_COLUMNS = ["entity_name_th", "entity_name_en", "brand_names", "licence_type",
                    "regulator", "app_ids", "domains", "source_url", "as_of"]


def _salt(arg: str | None) -> str:
    salt = arg or os.environ.get("LENDWATCH_SALT")
    if not salt:
        salt = secrets.token_hex(16)
        print("[warn] no salt given: using a random one; hashes will not link across runs",
              file=sys.stderr)
    return salt


def cmd_demo(args) -> int:
    from .demo import make_demo
    demo = make_demo(seed=args.seed, n_illegal=args.operators)
    os.makedirs(args.out, exist_ok=True)
    reg_path = os.path.join(args.out, "demo_registry.csv")
    with open(reg_path, "w", encoding="utf-8-sig", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=REGISTRY_COLUMNS)
        w.writeheader()
        w.writerows(demo["registry_rows"])
    arts = demo["artefacts"]
    with open(os.path.join(args.out, "demo_artefacts.jsonl"), "w", encoding="utf-8") as fh:
        for a in arts:
            fh.write(json.dumps({k: v for k, v in a.items() if not k.startswith("_")},
                                ensure_ascii=False) + "\n")
    res = run_analysis(
        arts, LicensedRegistry.from_csv(reg_path), _salt(args.salt or "demo-salt"), args.out,
        use_text_similarity=args.text_similarity,
        truth_labels={a["artefact_id"]: a["_true_label"] for a in arts},
        truth_operators={a["artefact_id"]: a["_true_operator"] for a in arts},
        truth_total_operators=demo["truth"]["n_illegal_operators"],
    )
    print(render_summary(res))
    print(f"Outputs written to {os.path.abspath(args.out)}")
    return 0


def cmd_collect(args) -> int:
    from .collectors import collect_live
    arts = collect_live(sources=args.sources, max_per_source=args.max)
    with open(args.out, "w", encoding="utf-8") as fh:
        for a in arts:
            fh.write(json.dumps(a, ensure_ascii=False, default=str) + "\n")
    print(f"{len(arts)} artefacts written to {args.out}")
    return 0


def cmd_analyse(args) -> int:
    with open(args.artefacts, encoding="utf-8") as fh:
        arts = [json.loads(line) for line in fh if line.strip()]
    labels = None
    if args.labels:                     # CSV with columns artefact_id,label (1 = illegal)
        with open(args.labels, encoding="utf-8-sig", newline="") as fh:
            labels = {r["artefact_id"]: int(r["label"]) for r in csv.DictReader(fh)}
    res = run_analysis(arts, LicensedRegistry.from_csv(args.registry), _salt(args.salt), args.out,
                       use_text_similarity=args.text_similarity, truth_labels=labels)
    print(render_summary(res))
    return 0


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="lendwatch", description=__doc__,
                                formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = p.add_subparsers(dest="cmd", required=True)

    d = sub.add_parser("demo", help="run the full pipeline on synthetic data")
    d.add_argument("--out", default="outputs_demo")
    d.add_argument("--seed", type=int, default=7)
    d.add_argument("--operators", type=int, default=300, help="true number of illegal operators")
    d.add_argument("--salt")
    d.add_argument("--text-similarity", action="store_true")
    d.set_defaults(func=cmd_demo)

    c = sub.add_parser("collect", help="collect public listings (needs network)")
    c.add_argument("--sources", nargs="+", default=["google_play", "app_store", "web"],
                   choices=["google_play", "app_store", "web"])
    c.add_argument("--max", type=int, default=100, help="maximum artefacts per source")
    c.add_argument("--out", default="artefacts.jsonl")
    c.set_defaults(func=cmd_collect)

    a = sub.add_parser("analyse", help="score, link and estimate from collected artefacts")
    a.add_argument("--artefacts", required=True)
    a.add_argument("--registry", required=True)
    a.add_argument("--labels", help="optional reviewer labels CSV: artefact_id,label")
    a.add_argument("--out", default="outputs")
    a.add_argument("--salt")
    a.add_argument("--text-similarity", action="store_true")
    a.set_defaults(func=cmd_analyse)

    args = p.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
