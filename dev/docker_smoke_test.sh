#!/usr/bin/env bash
# Smoke test a built ecsjobs Docker image before publishing it.
#
# Usage: dev/docker_smoke_test.sh IMAGE
#
# 1. CLI: --version matches the installed package metadata; --help works.
# 2. Tools the job scripts rely on: bash, rsnapshot, aws, the Python deps,
#    and a clean `pip check`.
# 3. End to end against moto (mocked S3 + SES) on a private docker network:
#    config loaded from S3, one passing and one failing LocalCommand job run
#    for a schedule, and the HTML report emailed through SES.
#
# Needs only docker and bash on the host.
set -euo pipefail

IMAGE="${1:?usage: $0 IMAGE}"
MOTO_IMAGE="${MOTO_IMAGE:-motoserver/moto:5.2.5}"
SCHEDULE="smoke-sched"
BUCKET="ecsjobs-smoke"
KEY="ecsjobs.yml"
FROM_EMAIL="ecsjobs@example.com"
NET="ecsjobs-smoke-$$"
MOTO="ecsjobs-smoke-moto-$$"

fail() { echo "FAIL: $*" >&2; exit 1; }
pass() { echo "ok: $*"; }

cleanup() {
  docker rm -f "$MOTO" >/dev/null 2>&1 || true
  docker network rm "$NET" >/dev/null 2>&1 || true
}
trap cleanup EXIT
trap 'exit 130' INT TERM

# run a command in the image with the entrypoint overridden
in_image() { docker run --rm --entrypoint "$1" "$IMAGE" "${@:2}"; }

# run in the image on the moto network, with AWS pointed at moto
# (no -i by default: an attached stdin that never closes hangs docker run)
on_net() {
  docker run --rm --network "$NET" \
    -e AWS_ENDPOINT_URL="http://${MOTO}:5000" \
    -e AWS_ACCESS_KEY_ID=testing -e AWS_SECRET_ACCESS_KEY=testing \
    -e AWS_DEFAULT_REGION=us-east-1 \
    "$@"
}

echo "== CLI"
pkg_version="$(in_image python -c 'from importlib.metadata import version; print(version("ecsjobs"))')"
cli_version="$(docker run --rm "$IMAGE" --version)"
[[ "$cli_version" == "ecsjobs v${pkg_version} <https://github.com/jantman/ecsjobs>" ]] \
  || fail "--version printed '$cli_version'; package metadata says $pkg_version"
pass "--version: $cli_version"
docker run --rm "$IMAGE" --help >/dev/null || fail "--help exited non-zero"
pass "--help"

echo "== tools"
in_image bash -c 'echo "$BASH_VERSION"' >/dev/null || fail "bash"
pass "bash"
rsnapshot_version="$(in_image rsnapshot --version)" || fail "rsnapshot"
pass "rsnapshot: $rsnapshot_version"
aws_version="$(in_image aws --version)" || fail "aws --version"
pass "aws: $aws_version"
in_image python -c 'import ecsjobs, boto3, docker, yaml, jsonschema, requests, cronex' \
  || fail "python imports"
pass "python imports"
in_image pip check >/dev/null || fail "pip check"
pass "pip check"

echo "== end to end against moto ($MOTO_IMAGE)"
docker pull -q "$MOTO_IMAGE" >/dev/null
docker network create "$NET" >/dev/null
docker run -d --name "$MOTO" --network "$NET" "$MOTO_IMAGE" >/dev/null
moto_up=false
for _ in $(seq 1 30); do
  if on_net --entrypoint python "$IMAGE" -c \
      "import urllib.request; urllib.request.urlopen('http://${MOTO}:5000/moto-api/', timeout=2)" \
      >/dev/null 2>&1; then
    moto_up=true
    break
  fi
  sleep 1
done
$moto_up || fail "moto did not answer at http://${MOTO}:5000"

# Config: one passing and one failing job on $SCHEDULE, plus one job on
# another schedule that must not run.
config="$(cat <<EOF
global:
  from_email: ${FROM_EMAIL}
  to_email: ops@example.com
  email_subject: ecsjobs smoke test
  inter_poll_sleep_sec: 1
jobs:
  - name: smoke-good
    class_name: LocalCommand
    schedule: ${SCHEDULE}
    command: "echo SMOKE_GOOD_OUTPUT"
    shell: true
  - name: smoke-bad
    class_name: LocalCommand
    schedule: ${SCHEDULE}
    command: "echo SMOKE_BAD_OUTPUT; exit 3"
    shell: true
  - name: smoke-other-schedule
    class_name: LocalCommand
    schedule: some-other-schedule
    command: "echo SHOULD_NOT_RUN"
    shell: true
EOF
)"

# seed S3 and the SES sender identity with the image's own aws CLI
echo "$config" | on_net -i --entrypoint bash "$IMAGE" -c "
  set -e
  aws s3api create-bucket --bucket $BUCKET >/dev/null
  aws s3 cp - s3://$BUCKET/$KEY
  aws ses verify-email-identity --email-address $FROM_EMAIL
" || fail "seeding moto with the aws CLI"
pass "seeded s3://$BUCKET/$KEY and SES identity via aws CLI"

# ecsjobs exits 0 when the run completes and the report is sent, even if
# jobs failed (failures are reported in the email); it exits non-zero only
# if config loading or sending the report raises.
rc=0
on_net -e ECSJOBS_BUCKET="$BUCKET" -e ECSJOBS_KEY="$KEY" "$IMAGE" -v run "$SCHEDULE" \
  || rc=$?
[[ $rc -eq 0 ]] || fail "ecsjobs run exited $rc"
pass "ecsjobs run exited 0"

# Pull the sent messages out of moto's state dump and check them in Python
# (inside the image, so the host needs no python or jq).
on_net -i --entrypoint python "$IMAGE" - "http://${MOTO}:5000/moto-api/data.json" <<'EOF' \
  || fail "SES report email check"
import json, sys, urllib.request

data = json.load(urllib.request.urlopen(sys.argv[1]))
sent = data.get("ses", {}).get("Message", [])
assert len(sent) == 1, f"expected 1 sent email, got {len(sent)}: {sent}"
msg = sent[0]
assert msg["subject"] == "ecsjobs smoke test", msg["subject"]
assert msg["source"] == "ecsjobs@example.com", msg["source"]
assert msg["destinations"]["ToAddresses"] == ["ops@example.com"], msg
body = msg["body"]
expected = [
    "smoke-good", "SMOKE_GOOD_OUTPUT",
    "smoke-bad", "SMOKE_BAD_OUTPUT",
    # success row background, failure row background, failure exit code cell
    '<tr style="background-color: #66ff66;">',
    '<tr style="background-color: #ff9999;">',
    'padding: 1em;">3</td>',
]
missing = [s for s in expected if s not in body]
assert not missing, f"report missing {missing}:\n{body}"
for s in ("smoke-other-schedule", "SHOULD_NOT_RUN"):
    assert s not in body, f"job from another schedule ran: {s}"
print("ok: one SES email with both jobs, their output and pass/fail markers")
EOF

echo "PASS: $IMAGE"
