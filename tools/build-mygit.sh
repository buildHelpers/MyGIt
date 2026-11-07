#!/usr/bin/env bash
# MyGIt macOS release-preview builder. No UI patching, no GitHub-hosted CI.
# Usage: bash tools/build-mygit.sh [new-output-directory]
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ "$(uname -s)" != "Darwin" ]]; then
  echo "ERROR: MyGIt .app builds require macOS." >&2
  exit 2
fi

for command in git python3 dotnet clang codesign ditto; do
  if ! command -v "$command" >/dev/null 2>&1; then
    echo "ERROR: Missing $command; install the macOS build dependency first." >&2
    exit 2
  fi
done

case "$(uname -m)" in
  arm64) runtime="osx-arm64"; clang_arch="arm64" ;;
  x86_64) runtime="osx-x64"; clang_arch="x86_64" ;;
  *) echo "ERROR: Unsupported Mac architecture." >&2; exit 2 ;;
esac

if [[ -n "$(git status --porcelain --untracked-files=no)" ]]; then
  echo "ERROR: Commit/stash tracked source edits before building this version." >&2
  exit 2
fi

destination="${1:-"$ROOT/../MyGIt-Build"}"
mkdir -p "$destination"
destination="$(cd "$destination" && pwd)"
app="$destination/MyGIt.app"
archive="$destination/MyGIt-${runtime}.zip"
if [[ -e "$app" || -e "$archive" ]]; then
  echo "ERROR: MyGIt.app or archive already exists in $destination; choose a fresh directory." >&2
  exit 2
fi

scratch="$(mktemp -d "${TMPDIR:-/tmp}/mygit-direct-build.XXXXXXXX")"
source_dir="$scratch/source"
worktree_added=false
clean() {
  if [[ "$worktree_added" == "true" ]]; then
    git -C "$ROOT" worktree remove --force "$source_dir" || true
  fi
  rm -rf "$scratch"
}
trap clean EXIT

# The product's UI is already committed in src/. A detached worktree is used
# for packaging isolation only, never to apply theme/layout patches.
git worktree add --detach "$source_dir" HEAD
worktree_added=true
git -C "$source_dir" submodule update --init --recursive

# Rasterize the MyGIt vector icon in the disposable packaging checkout.
python3 "$source_dir/mygit-themes/tools/icons.py" --root "$source_dir"

dotnet publish "$source_dir/src/SourceGit.csproj" \
  -c Release -r "$runtime" -p:DisableAOT=true \
  --self-contained true -o "$scratch/publish"

mkdir -p "$app/Contents/MacOS" "$app/Contents/Resources"
cp -R "$scratch/publish/." "$app/Contents/MacOS/"
cp "$source_dir/build/resources/app/App.icns" "$app/Contents/Resources/App.icns"

version="$(tr -d '\r\n' < "$source_dir/VERSION")"
sed "s/SOURCE_GIT_VERSION/$version/g" \
  "$source_dir/build/resources/app/App.plist" > "$app/Contents/Info.plist"

clang -arch "$clang_arch" \
  "$source_dir/tools/setsid-macos/setsid.c" \
  -o "$app/Contents/MacOS/setsid" -mmacosx-version-min=13.0

bundle_id="$(/usr/libexec/PlistBuddy -c 'Print :CFBundleIdentifier' "$app/Contents/Info.plist")"
bundle_name="$(/usr/libexec/PlistBuddy -c 'Print :CFBundleName' "$app/Contents/Info.plist")"
if [[ "$bundle_id" != "com.buildhelpers.mygit" || "$bundle_name" != "MyGIt" ]]; then
  echo "ERROR: Refusing to package a SourceGit-branded build ($bundle_id / $bundle_name)." >&2
  exit 1
fi

codesign --force --deep --sign - "$app"
codesign --verify --deep --strict "$app"
ditto -c -k --sequesterRsrc --keepParent "$app" "$archive"
echo "PASS: direct-source MyGIt build; bundle ID $bundle_id"
echo "App: $app"
echo "ZIP: $archive"
echo "NOTE: ad-hoc signed local acceptance build, not notarized for distribution."
