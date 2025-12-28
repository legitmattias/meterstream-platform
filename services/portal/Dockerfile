# Build stage
FROM node:20-alpine AS build

# ==== ANALYTICS INTEGRATION: Accept build args for environment-specific URLs ====
ARG VITE_API_BASE_URL=http://localhost:8000
ARG VITE_GRAFANA_URL=http://localhost:3000

# Set as env vars so Vite can embed them during build
ENV VITE_API_BASE_URL=$VITE_API_BASE_URL
ENV VITE_GRAFANA_URL=$VITE_GRAFANA_URL
# ==== END ANALYTICS INTEGRATION ====

WORKDIR /app
COPY package*.json ./
RUN npm ci
COPY . .
RUN npm run build

# Production stage
FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/nginx.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
