# ── CSRD Comply — Frontend Dockerfile ────────────────────────
# Multi-stage build per Next.js standalone

# ── Stage 1: Build ─────────────────────────────────────────────
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files
COPY package.json package-lock.json ./
RUN npm ci

# Copy source
COPY . .

# Build
# ⚠️ NON impostare NEXT_PUBLIC_API_URL come argomento!
# In Docker con Nginx, frontend e backend sono sulla stessa origine.
# L'API client usa il percorso relativo /api/v1 come fallback,
# e Nginx proxy /api/ → backend.
# HttpOnly cookie JWT funzionano solo se sono same-origin.
ENV NODE_ENV=production

RUN npm run build

# ── Stage 2: Runtime ──────────────────────────────────────────
FROM node:20-alpine

WORKDIR /app

# non-root user for security
RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

# Copy standalone output from builder
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

# Set correct permissions
RUN chown -R nextjs:nodejs /app

USER nextjs

EXPOSE 3000

ENV NODE_ENV=production
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD wget --no-verbose --tries=1 --spider http://localhost:3000 || exit 1

CMD ["node", "server.js"]
