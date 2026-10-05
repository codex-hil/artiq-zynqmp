#!/usr/bin/env python3
"""Archive full histories separately from development; inventory exact refs.

Existing mirrors are never automatically updated. Extra canonical refs are
fetched under a separate namespace, preserving GitHub's archived revisions.
"""
import argparse
import concurrent.futures
import json
from pathlib import Path
import subprocess


def git(path, *args):
    return subprocess.check_output(["git", "--git-dir=" + str(path), *args], text=True).strip()


def acquire(destination, name, specification):
    mirror = destination / (name + ".git")
    try:
        if not mirror.exists():
            subprocess.run(["git", "clone", "--mirror", specification["url"], str(mirror)], check=True)
        for index, url in enumerate(specification.get("extra_urls", [])):
            prefix = "canonical" if index == 0 else "canonical" + str(index)
            if not git(mirror, "for-each-ref", "refs/heads/" + prefix):
                subprocess.run(["git", "--git-dir=" + str(mirror), "fetch", url,
                    "+refs/heads/*:refs/heads/" + prefix + "/*",
                    "+refs/tags/*:refs/tags/*"], check=True)
        for revision in specification.get("pins", []):
            git(mirror, "cat-file", "-e", revision + "^{commit}")
        return {"name": name, "url": specification["url"],
                "extra_urls": specification.get("extra_urls", []),
                "head": git(mirror, "rev-parse", "HEAD"),
                "refs": git(mirror, "show-ref").splitlines(),
                "pins": specification.get("pins", []), "status": "ARCHIVED"}
    except (subprocess.CalledProcessError, OSError) as error:
        return {"name": name, "url": specification["url"], "status": "FAILED", "error": str(error)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", required=True, type=Path)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--include-yocto", action="store_true")
    options = parser.parse_args()
    options.destination.mkdir(parents=True, exist_ok=True)
    registry = json.loads(Path(__file__).with_name("source-registry.json").read_text())
    jobs = [(name, spec) for name, spec in registry.items()
            if options.include_yocto or spec.get("group") != "yocto"]
    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as workers:
        futures = [workers.submit(acquire, options.destination, name, spec) for name, spec in jobs]
        results = []
        for future in concurrent.futures.as_completed(futures):
            result = future.result()
            print(result["name"], result["status"], flush=True)
            results.append(result)
    options.manifest.parent.mkdir(parents=True, exist_ok=True)
    options.manifest.write_text(json.dumps(sorted(results, key=lambda x: x["name"]), indent=2) + "\n")
    return 1 if any(r["status"] == "FAILED" for r in results) else 0


if __name__ == "__main__":
    raise SystemExit(main())
