#!/bin/bash
#
# Author: Dodotree
# https://github.community/t5/How-to-use-Git-and-GitHub/How-to-create-full-release-from-command-line-not-just-a-tag/m-p/6911/highlight/true#M2303
# Modified by rix1337
#
#
# This script accepts the following parameters:
#
# * owner
# * repo
# * tag
# * github_api_token
#
# Script to create a release using the GitHub API v3.
#
# Example:
#
# setup_create_release.sh github_api_token=TOKEN owner=rix1337 repo=feedcrawler version=v0.1.0

# Check dependencies.
set -e
xargs=$(which gxargs || which xargs)

# Validate settings.
[ "$TRACE" ] && set -x

CONFIG=$@

for line in $CONFIG; do
  eval "$line"
done

generate_post_data()
{
  cat <<EOF
{
  "tag_name": "$version",
  "target_commitish": "master",
  "name": "$version",
  "body": "Platzhalter",
  "draft": false,
  "prerelease": false
}
EOF
}

echo "Create release $version for repo: $owner/$repo branch: master"
curl -H "Authorization: token $github_api_token" --data "$(generate_post_data)" "https://api.github.com/repos/$owner/$repo/releases"
