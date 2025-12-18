#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
build_dir="${repo_root}/build"
install_dir="${repo_root}/install"
dist_dir="${repo_root}/dist"

library_present() {
  local lib_dir
  for lib_dir in \
    "${install_dir}/lib" \
    "${install_dir}/lib64" \
    "${install_dir}/lib/x86_64-linux-gnu" \
    "${install_dir}/lib/aarch64-linux-gnu"; do
    if ls "${lib_dir}"/libwebrtc-audio-processing-2.* >/dev/null 2>&1; then
      return 0
    fi
  done
  return 1
}

if ! library_present; then
  if ! command -v meson >/dev/null 2>&1; then
    echo "meson not found; please install meson and ninja, then re-run."
    exit 1
  fi
  if [ ! -d "${build_dir}" ]; then
    meson setup "${build_dir}" -Dprefix="${install_dir}" "${repo_root}"
  else
    meson setup --reconfigure "${build_dir}" -Dprefix="${install_dir}" "${repo_root}"
  fi
  meson compile -C "${build_dir}"
  meson install -C "${build_dir}"
fi

mkdir -p "${dist_dir}"

cd "${repo_root}/python"

if python -c "import build" >/dev/null 2>&1; then
  python -m build --wheel --no-isolation --outdir "${dist_dir}"
elif python -c "import wheel" >/dev/null 2>&1; then
  python setup.py bdist_wheel --dist-dir "${dist_dir}"
else
  echo "Missing build tooling. Install either 'build' or 'wheel' and retry."
  exit 1
fi

echo "Wheel created in ${dist_dir}"
