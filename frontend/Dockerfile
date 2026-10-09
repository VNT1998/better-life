# Multi-stage production build

# Stage 1: Build React SPA
FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json package-lock.json ./
RUN npm ci

COPY . .
RUN npm run build

# Stage 2: Production Nginx Server
FROM nginx:alpine

COPY --from=builder /app/dist /usr/share/nginx/html

# Hardened Nginx configuration with client routing and unbuffered SSE reverse proxy
RUN echo 'server { \
    listen 80; \
    server_name localhost; \
    location / { \
        root /usr/share/nginx/html; \
        index index.html index.htm; \
        try_files $uri $uri/ /index.html; \
    } \
    location /api/ { \
        proxy_pass http://backend:8000/api/; \
        proxy_http_version 1.1; \
        proxy_set_header Host $host; \
        proxy_set_header X-Real-IP $remote_addr; \
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for; \
        proxy_set_header Connection ""; \
        proxy_buffering off; \
        proxy_cache off; \
        proxy_read_timeout 600s; \
    } \
    location /health { \
        proxy_pass http://backend:8000/health; \
    } \
    location /ready { \
        proxy_pass http://backend:8000/ready; \
    } \
}' > /etc/nginx/conf.d/default.conf

EXPOSE 80

CMD ["nginx", "-g", "daemon off;"]
