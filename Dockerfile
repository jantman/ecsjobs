# Builder: build the wheel and export the exact locked runtime requirements.
FROM python:3.14-alpine3.24 AS builder
COPY --from=ghcr.io/astral-sh/uv:0.13.5 /uv /usr/local/bin/uv
WORKDIR /src
COPY . .
RUN uv build --wheel --out-dir /dist \
  && uv export --locked --no-dev --no-emit-project --format requirements.txt \
       --output-file /dist/requirements.txt

# Final image
FROM python:3.14-alpine3.24

LABEL org.opencontainers.image.title="ecsjobs" \
      org.opencontainers.image.description="A scheduled job wrapper for ECS, focused on email reporting and adding docker exec and local command abilities." \
      org.opencontainers.image.licenses="AGPL-3.0-or-later" \
      org.opencontainers.image.source="https://github.com/jantman/ecsjobs"

ENV PYTHONUNBUFFERED=1

# aws-cli is Alpine's AWS CLI v2 package; it runs on Alpine's own
# /usr/bin/python3 with its own site-packages, separate from the
# /usr/local Python that ecsjobs and its locked dependencies live in.
RUN apk add --no-cache bash rsnapshot aws-cli \
  && mkdir -p /root/.aws

RUN --mount=type=bind,from=builder,source=/dist,target=/dist \
  pip install --root-user-action=ignore --no-cache-dir --no-deps -r /dist/requirements.txt \
  && pip install --root-user-action=ignore --no-cache-dir --no-deps /dist/*.whl \
  && pip check

ENTRYPOINT ["/usr/local/bin/ecsjobs"]
