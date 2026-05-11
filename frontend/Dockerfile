# PULSE — frontend image. Multi-stage: node:20-alpine builds the Vite SPA,
# nginx:1.30-alpine serves the static dist on :80.
# Plan 04 (frontend skeleton) creates frontend/src/, frontend/package.json, etc.

# -----------------------------------------------------------------------------
# Stage 1 — builder (Vite/pnpm)
# -----------------------------------------------------------------------------
FROM node:20-alpine AS builder

ENV CI=1 \
    PNPM_HOME=/pnpm \
    PATH=/pnpm:$PATH

# Activate pnpm via the bundled corepack shim, matching the host pinned version.
RUN corepack enable && corepack prepare pnpm@10.15.0 --activate

WORKDIR /app

# Copy lockfile + manifest first so dependency install is cached separately from
# the rest of the source. pnpm-lock.yaml may not exist on the very first build
# (Plan 04 creates it) — the wildcard makes the COPY non-fatal in that case.
COPY package.json ./
COPY pnpm-lock.yaml* ./
COPY .npmrc* ./

RUN pnpm install --frozen-lockfile

# Now copy the rest of the source and build.
COPY . .

RUN pnpm run build


# -----------------------------------------------------------------------------
# Stage 2 — runtime (nginx serving the SPA)
# -----------------------------------------------------------------------------
FROM nginx:1.30-alpine AS runtime

# Drop the default vhost shipped by the base image.
RUN rm -f /etc/nginx/conf.d/default.conf

# SPA config — try_files fallback, gzip, no security headers (pulse-nginx owns those).
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Built assets.
COPY --from=builder /app/dist /usr/share/nginx/html

EXPOSE 80

# wget is available in nginx:alpine for the compose healthcheck (`wget --spider`).
CMD ["nginx", "-g", "daemon off;"]
