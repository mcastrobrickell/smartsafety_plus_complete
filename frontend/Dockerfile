FROM node:18-alpine AS build

WORKDIR /app

# Dependencies
COPY package.json ./
RUN npm install --legacy-peer-deps

# Build args for API URL
ARG REACT_APP_BACKEND_URL=http://localhost:8001
ENV REACT_APP_BACKEND_URL=$REACT_APP_BACKEND_URL
ENV CI=false

# Build
COPY . .
RUN npm run build

# Production: serve with nginx
FROM nginx:alpine

# Custom nginx config
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy built files
COPY --from=build /app/build /usr/share/nginx/html

EXPOSE 80

ENV PORT=80

HEALTHCHECK --interval=30s --timeout=3s \
    CMD wget -qO- http://localhost:$PORT/ || exit 1

CMD ["sh", "-c", "envsubst '$PORT' < /etc/nginx/conf.d/default.conf > /tmp/nginx.conf && mv /tmp/nginx.conf /etc/nginx/conf.d/default.conf && exec nginx -g 'daemon off;'"]
