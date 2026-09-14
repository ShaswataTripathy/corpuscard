"""
CLI entry point.

    corpuscard generate manifest.yaml -o summary.md
    corpuscard check manifest.yaml
    corpuscard render-html manifest.yaml -o summary.html
    corpuscard render-model-card manifest.yaml -o MODEL_CARD.md
    corpuscard render-copyright-policy manifest.yaml -o copyright-policy.md
    corpuscard render-ab2013 manifest.yaml -o ab2013-disclosure.md
    corpuscard diff old.yaml new.yaml
    corpuscard status ./manifests/
    corpuscard estimate --text ./corpus/ --image ./images/
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .diff import diff_summaries
from .estimate import estimate_image_count, estimate_text_tokens, suggest_manifest_snippet
from .loader import load_manifest
from .render import render_markdown
from .render_ab2013 import render_ab2013
from .render_copyright import render_copyright_policy
from .render_html import render_html
from .render_modelcard import render_model_card
from .status import scan_directory
from .validate import validate


def _load_or_die(path: str) -> object | None:
    try:
        return load_manifest(path)
    except Exception as e:  # noqa: BLE001 - CLI boundary: report any load failure (bad YAML,
        # missing file, schema validation) as a clean message, not a raw traceback.
        print(f"Failed to load manifest '{path}': {e}", file=sys.stderr)
        return None


def _write_or_print(content: str, output: str | None, label: str) -> None:
    if output:
        Path(output).write_text(content, encoding="utf-8")
        print(f"Wrote {label} to {output}")
    else:
        print(content)


def _run_validation_gate(summary, force: bool) -> bool:
    """Prints findings; returns True if generation should proceed."""
    findings = validate(summary)
    errors = [f for f in findings if f.level == "error"]
    for f in findings:
        print(str(f), file=sys.stderr)
    if errors and not force:
        print(f"\n{len(errors)} error(s) found. Fix them or re-run with --force to generate anyway.", file=sys.stderr)
        return False
    return True


def _cmd_generate(args: argparse.Namespace) -> int:
    summary = _load_or_die(args.manifest)
    if summary is None:
        return 1
    if not _run_validation_gate(summary, args.force):
        return 1
    _write_or_print(render_markdown(summary), args.output, "Summary (Markdown)")
    return 0


def _cmd_check(args: argparse.Namespace) -> int:
    summary = _load_or_die(args.manifest)
    if summary is None:
        return 1
    findings = validate(summary)
    if not findings:
        print("No issues found.")
        return 0
    for f in findings:
        print(str(f))
    return 1 if any(f.level == "error" for f in findings) else 0


def _cmd_render_html(args: argparse.Namespace) -> int:
    summary = _load_or_die(args.manifest)
    if summary is None:
        return 1
    if not _run_validation_gate(summary, args.force):
        return 1
    _write_or_print(render_html(summary), args.output, "Summary (HTML)")
    return 0


def _cmd_render_model_card(args: argparse.Namespace) -> int:
    summary = _load_or_die(args.manifest)
    if summary is None:
        return 1
    card = render_model_card(summary, license=args.license, summary_url=args.summary_url)
    _write_or_print(card, args.output, "Model Card")
    return 0


def _cmd_render_copyright_policy(args: argparse.Namespace) -> int:
    summary = _load_or_die(args.manifest)
    if summary is None:
        return 1
    _write_or_print(render_copyright_policy(summary), args.output, "Copyright policy")
    return 0


def _cmd_render_ab2013(args: argparse.Namespace) -> int:
    summary = _load_or_die(args.manifest)
    if summary is None:
        return 1
    try:
        content = render_ab2013(summary)
    except ValueError as e:
        print(str(e), file=sys.stderr)
        return 1
    _write_or_print(content, args.output, "AB 2013 disclosure")
    return 0


def _cmd_diff(args: argparse.Namespace) -> int:
    old = _load_or_die(args.old_manifest)
    new = _load_or_die(args.new_manifest)
    if old is None or new is None:
        return 1
    changes = diff_summaries(old, new)
    if not changes:
        print("No differences.")
        return 0
    for c in changes:
        print(str(c))
    return 0


def _cmd_status(args: argparse.Namespace) -> int:
    results = scan_directory(args.directory)
    if not results:
        print(f"No manifest files (.yaml/.yml/.json) found under {args.directory}")
        return 0

    any_overdue = False
    any_error = False
    for r in results:
        if r.load_error:
            any_error = True
            print(f"[ERROR] {r.path}: failed to load ({r.load_error})")
            continue
        flag = "OVERDUE" if r.overdue else "ok"
        if r.overdue:
            any_overdue = True
        names = ", ".join(r.model_names) or "(unnamed)"
        age = f"{r.days_since_update}d ago" if r.days_since_update is not None else "unknown age"
        print(f"[{flag:7}] {r.path}: {names} - last update {r.last_update} ({age})")

    if any_error:
        return 1
    return 1 if any_overdue and args.fail_on_overdue else 0


def _cmd_estimate(args: argparse.Namespace) -> int:
    if not args.text and not args.image:
        print("Provide at least one of --text or --image.", file=sys.stderr)
        return 1

    text_estimate = None
    if args.text:
        text_estimate = estimate_text_tokens(args.text)
        print(
            f"text: {text_estimate.file_count} file(s), {text_estimate.word_count:,} words, "
            f"~{text_estimate.estimated_tokens:,} tokens ({text_estimate.method}) "
            f"-> size_range: \"{text_estimate.size_range}\""
        )

    image_estimate = None
    if args.image:
        image_estimate = estimate_image_count(args.image)
        print(f"image: {image_estimate.file_count} file(s) -> size_range: \"{image_estimate.size_range}\"")

    print("\nSuggested manifest snippet:\n")
    print(suggest_manifest_snippet(text_estimate, image_estimate))
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="corpuscard", description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="command", required=True)

    p_gen = sub.add_parser("generate", help="Render a manifest into the official narrative Summary format (Markdown).")
    p_gen.add_argument("manifest", help="Path to a YAML or JSON manifest file.")
    p_gen.add_argument("-o", "--output", help="Output file path. Prints to stdout if omitted.")
    p_gen.add_argument("--force", action="store_true", help="Generate even if validation errors are found.")
    p_gen.set_defaults(func=_cmd_generate)

    p_chk = sub.add_parser("check", help="Run completeness checks against a manifest without rendering.")
    p_chk.add_argument("manifest", help="Path to a YAML or JSON manifest file.")
    p_chk.set_defaults(func=_cmd_check)

    p_html = sub.add_parser("render-html", help="Render the Summary as a single self-contained HTML page.")
    p_html.add_argument("manifest", help="Path to a YAML or JSON manifest file.")
    p_html.add_argument("-o", "--output", help="Output file path. Prints to stdout if omitted.")
    p_html.add_argument("--force", action="store_true", help="Generate even if validation errors are found.")
    p_html.set_defaults(func=_cmd_render_html)

    p_card = sub.add_parser("render-model-card", help="Render a Hugging Face-style Model Card from the same manifest.")
    p_card.add_argument("manifest", help="Path to a YAML or JSON manifest file.")
    p_card.add_argument("-o", "--output", help="Output file path. Prints to stdout if omitted.")
    p_card.add_argument("--license", help="SPDX license identifier to include in the card's frontmatter.")
    p_card.add_argument("--summary-url", help="Link to the published Article 53 Summary, if hosted.")
    p_card.set_defaults(func=_cmd_render_model_card)

    p_copy = sub.add_parser("render-copyright-policy", help="Render an Article 53(1)(c) copyright-policy starting point.")
    p_copy.add_argument("manifest", help="Path to a YAML or JSON manifest file.")
    p_copy.add_argument("-o", "--output", help="Output file path. Prints to stdout if omitted.")
    p_copy.set_defaults(func=_cmd_render_copyright_policy)

    p_ab = sub.add_parser("render-ab2013", help="Render a California AB 2013 training-data transparency disclosure.")
    p_ab.add_argument("manifest", help="Path to a YAML or JSON manifest file (must include an 'ab2013' block).")
    p_ab.add_argument("-o", "--output", help="Output file path. Prints to stdout if omitted.")
    p_ab.set_defaults(func=_cmd_render_ab2013)

    p_diff = sub.add_parser("diff", help="Show what changed between two manifest versions.")
    p_diff.add_argument("old_manifest")
    p_diff.add_argument("new_manifest")
    p_diff.set_defaults(func=_cmd_diff)

    p_status = sub.add_parser("status", help="Scan a directory of manifests and flag which are overdue for update.")
    p_status.add_argument("directory")
    p_status.add_argument(
        "--fail-on-overdue", action="store_true",
        help="Exit with status 1 if any manifest is overdue (useful in CI).",
    )
    p_status.set_defaults(func=_cmd_status)

    p_est = sub.add_parser("estimate", help="Estimate modality sizes from files on disk and suggest a manifest snippet.")
    p_est.add_argument("--text", nargs="+", default=[], help="File(s)/directory(ies) of text content to count.")
    p_est.add_argument("--image", nargs="+", default=[], help="File(s)/directory(ies) of image content to count.")
    p_est.set_defaults(func=_cmd_estimate)

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
