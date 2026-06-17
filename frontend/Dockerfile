FROM node:24-bookworm-slim AS deps

WORKDIR /app
COPY package.json package-lock.json ./
RUN npm ci

FROM node:24-bookworm-slim AS builder

WORKDIR /app
ARG NEXT_PUBLIC_API_BASE_URL=http://localhost:38081/api
ARG NEXT_PUBLIC_SELLERHARBOR_TENANT_ID=local
ARG NEXT_PUBLIC_SELLERHARBOR_API_KEY=
ENV NEXT_PUBLIC_API_BASE_URL=$NEXT_PUBLIC_API_BASE_URL \
    NEXT_PUBLIC_SELLERHARBOR_TENANT_ID=$NEXT_PUBLIC_SELLERHARBOR_TENANT_ID \
    NEXT_PUBLIC_SELLERHARBOR_API_KEY=$NEXT_PUBLIC_SELLERHARBOR_API_KEY \
    NEXT_TELEMETRY_DISABLED=1

COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN mkdir -p public && npm run build

FROM node:24-bookworm-slim AS runner

WORKDIR /app
ENV NODE_ENV=production \
    NEXT_TELEMETRY_DISABLED=1 \
    HOSTNAME=0.0.0.0 \
    PORT=33001

COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
COPY --from=builder /app/public ./public

EXPOSE 33001

HEALTHCHECK --interval=30s --timeout=5s --start-period=20s --retries=3 \
  CMD node -e "fetch('http://127.0.0.1:33001/products').then((r)=>process.exit(r.ok?0:1)).catch(()=>process.exit(1))"

CMD ["node", "server.js"]
