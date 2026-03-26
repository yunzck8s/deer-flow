# Frontend Dockerfile
# Supports two targets:
#   --target dev   — install deps only, run `pnpm dev` at container start
#   --target prod  — full build baked in, run `pnpm start` at container start (default if no --target is specified)

ARG PNPM_STORE_PATH=/root/.local/share/pnpm/store
# Set to https://registry.npmjs.org if direct access is available
ARG NPM_REGISTRY=https://registry.npmmirror.com

# ── Base: shared setup ────────────────────────────────────────────────────────
FROM node:22-alpine AS base
ARG PNPM_STORE_PATH
ARG NPM_REGISTRY
RUN npm install -g pnpm@10.26.2 --registry=${NPM_REGISTRY}
RUN pnpm config set store-dir ${PNPM_STORE_PATH} && \
    pnpm config set registry ${NPM_REGISTRY}
WORKDIR /app
COPY frontend ./frontend

# ── Dev: install only, CMD is overridden by docker-compose ───────────────────
FROM base AS dev
RUN cd /app/frontend && pnpm install --frozen-lockfile

# ── Builder: install + compile Next.js ───────────────────────────────────────
FROM base AS builder
RUN cd /app/frontend && pnpm install --frozen-lockfile
# Skip env validation — runtime vars are injected by nginx/container
RUN cd /app/frontend && SKIP_ENV_VALIDATION=1 pnpm build

# ── Prod: minimal runtime with pre-built output ───────────────────────────────
FROM node:22-alpine AS prod
ARG PNPM_STORE_PATH
ARG NPM_REGISTRY=https://registry.npmmirror.com
RUN npm install -g pnpm@10.26.2 --registry=${NPM_REGISTRY}
RUN pnpm config set store-dir ${PNPM_STORE_PATH} && \
    pnpm config set registry ${NPM_REGISTRY}
WORKDIR /app
COPY --from=builder /app/frontend ./frontend
EXPOSE 3000
CMD ["sh", "-c", "cd /app/frontend && pnpm start"]
