#!/usr/bin/env python3
import argparse
import json

from ai_core import get_state_root
from ai_probe_contract import results_to_dicts, validate_probe_result
from ai_probes import list_probe_names, run_all_probes, run_named_probe

OUT = get_state_root() / "system_profile.json"


def build_payload(results):
    validation_errors: list[str] = []
    failed_probe_errors: list[str] = []
    for result in results:
        for err in validate_probe_result(result):
            validation_errors.append(f"{result.probe_name}: {err}")
        if not result.ok:
            error_kind = "unknown"
            error_message = "probe failed"
            if isinstance(result.error, dict):
                error_kind = str(result.error.get("kind", error_kind))
                error_message = str(result.error.get("message", error_message))
            failed_probe_errors.append(f"{result.probe_name}: {error_kind}: {error_message}")

    payload = {
        "ok": not validation_errors and not failed_probe_errors,
        "generated_by": "ai_scan_system",
        "schema": "stage2f_d_a_probe_snapshot",
        "results": results_to_dicts(results),
        "errors": validation_errors + failed_probe_errors,
    }
    return payload


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--probe", default="all")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    if args.list:
        for name in list_probe_names():
            print(name)
        return

    if args.probe == "all":
        results = run_all_probes()
    else:
        results = [run_named_probe(args.probe)]

    payload = build_payload(results)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"Wrote {OUT}")


if __name__ == "__main__":
    main()
