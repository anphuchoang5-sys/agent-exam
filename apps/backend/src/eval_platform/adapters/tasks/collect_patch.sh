#!/usr/bin/env bash
set -euo pipefail
export LC_ALL=C
base_commit="${1:?base commit is required}"
out_dir=/logs/artifacts
mkdir -p "$out_dir"
cd /testbed
git rev-parse --verify "${base_commit}^{commit}" >/dev/null
while IFS= read -r -d '' path; do
  git add -N -- "$path"
done < <(git ls-files --others --exclude-standard -z)
tmp="$(mktemp "$out_dir/model.patch.tmp.XXXXXX")"
trap 'rm -f "$tmp"' EXIT
git diff --no-ext-diff --no-textconv --full-index "$base_commit" -- . > "$tmp"
binary=0
while IFS=$'\t' read -r added deleted _path; do
  if [[ "$added" == "-" || "$deleted" == "-" ]]; then
    binary=1
    break
  fi
done < <(git diff --numstat "$base_commit" -- .)
sha256sum "$tmp" | cut -d ' ' -f 1 > "$out_dir/model.patch.sha256"
wc -c < "$tmp" | tr -d ' ' > "$out_dir/model.patch.bytes"
printf '%s\n' "$binary" > "$out_dir/model.patch.binary"
mv "$tmp" "$out_dir/model.patch"
trap - EXIT
