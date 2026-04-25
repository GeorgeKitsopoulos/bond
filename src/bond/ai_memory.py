#!/usr/bin/env python3
import argparse
from ai_core import (
    FACT_BUCKETS,
    FILES,
    append_jsonl,
    build_active_context,
    ensure_memory_dirs,
    load_fact_bucket,
    save_json,
    utc_now,
)


def set_fact(bucket: str, key: str, value, source: str = "explicit") -> dict:
    if bucket not in FACT_BUCKETS:
        raise ValueError(f"Unsupported fact bucket: {bucket}")

    ensure_memory_dirs()
    data = load_fact_bucket(bucket)
    data[key] = {
        "value": value,
        "updated_at": utc_now(),
        "source": source,
    }
    save_json(FILES[bucket], data)
    build_active_context()
    return data[key]


def append_log(kind: str, message: str, meta=None) -> None:
    ensure_memory_dirs()
    append_jsonl(
        FILES[kind],
        {
            "ts": utc_now(),
            "message": message,
            "meta": meta or {},
        },
    )
    build_active_context()


def main():
    parser = argparse.ArgumentParser(description="AI memory manager")
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_set = sub.add_parser("set", help="Store/update a durable fact")
    p_set.add_argument("bucket", choices=FACT_BUCKETS)
    p_set.add_argument("key")
    p_set.add_argument("value")
    p_set.add_argument("--source", default="explicit")

    p_log = sub.add_parser("log", help="Append a log entry")
    p_log.add_argument("kind", choices=("actions", "failures", "chats", "reflections"))
    p_log.add_argument("message")
    p_log.add_argument("--meta", default="{}")

    args = parser.parse_args()

    if args.cmd == "set":
        fact = set_fact(args.bucket, args.key, args.value, args.source)
        print(f"stored {args.bucket}.{args.key} = {fact['value']}")
        return

    if args.cmd == "log":
        import json

        try:
            meta = json.loads(args.meta)
            if not isinstance(meta, dict):
                raise ValueError
        except Exception:
            raise SystemExit("--meta must be a valid JSON object string")

        append_log(args.kind, args.message, meta)
        print(f"logged to {args.kind}")
        return


if __name__ == "__main__":
    main()
