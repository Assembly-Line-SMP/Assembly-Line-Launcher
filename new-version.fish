#!/usr/bin/env fish
# release.fish -- tag and push a new release.
#
# Usage: ./release.fish v0.2.0
#
# Bumps the version in pyproject.toml + launcher/__init__.py, commits that,
# creates an annotated tag, and pushes both. Pushing the tag is what
# triggers .github/workflows/build.yml to build all platforms and publish
# a GitHub Release.

set -l release_version $argv[1]

if test -z "$release_version"
    echo "Usage: ./release.fish vX.Y.Z"
    exit 1
end

if not string match -rq '^v[0-9]+\.[0-9]+\.[0-9]+$' -- $release_version
    echo "Version must look like vX.Y.Z (e.g. v0.2.0), got: $release_version"
    exit 1
end

set -l bare_version (string sub -s 2 $release_version)  # strip leading 'v'

# Don't tag on top of uncommitted changes -- easy way to accidentally
# ship something half-finished.
set -l dirty_files (git status --porcelain)
if test -n "$dirty_files"
    echo "Working tree isn't clean. Commit or stash first."
    git status --short
    exit 1
end

set -l current_branch (git rev-parse --abbrev-ref HEAD)
if test "$current_branch" != "main"
    echo "You're on '$current_branch', not 'main'."
    read -l -P "Continue anyway? [y/N] " confirm
    if test "$confirm" != "y"
        exit 1
    end
end

if git rev-parse $release_version >/dev/null 2>&1
    echo "Tag $release_version already exists."
    exit 1
end

echo "Bumping version to $bare_version..."
sed -i "s/^version = \".*\"/version = \"$bare_version\"/" pyproject.toml
sed -i "s/__version__ = \".*\"/__version__ = \"$bare_version\"/" src/launcher/__init__.py

git add pyproject.toml src/launcher/__init__.py
git commit -m "Release $release_version"

git tag -a $release_version -m "Release $release_version"

echo "Pushing commit and tag..."
git push origin $current_branch
git push origin $release_version

echo "Done. CI will build and publish the release for $release_version:"
echo "  https://github.com/Pavle012/assembly-line-launcher/actions"