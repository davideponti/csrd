# ── CSRD Comply — Frontend Dockerfile (per Render) ────────────
# Questo Dockerfile si trova alla root del repository.
# Il codice del frontend si trova nella sottodirectory CSRD-Comply/frontend/

# Stage 1: Build
FROM node:20-alpine AS builder

WORKDIR /app

# Copy package files from frontend directory (monorepo con CSRD-Comply/)
COPY CSRD-Comply/frontend/package.json CSRD-Comply/frontend/package-lock.json ./
RUN npm ci

# Copy frontend source
COPY CSRD-Comply/frontend/ .

# Build
ARG NEXT_PUBLIC_API_URL=https://csrdcomply.onrender.com/api/v1
ENV NEXT_PUBLIC_API_URL=$NEXT_PUBLIC_API_URL
ENV NODE_ENV=production

RUN npm run build

# Stage 2: Runtime
FROM node:20-alpine

WORKDIR /app

RUN addgroup --system --gid 1001 nodejs && \
    adduser --system --uid 1001 nextjs

COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

RUN chown -R nextjs:nodejs /app

USER nextjs

EXPOSE 3000

ENV NODE_ENV=production
ENV PORT=3000
ENV HOSTNAME="0.0.0.0"

CMD ["node", "server.js"]
# Ultima modifica: 28 maggio 2026
