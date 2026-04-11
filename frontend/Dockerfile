FROM node:22-alpine AS build

# Set working directory
WORKDIR /app

# Install dependencies based on standard Node package files
COPY package*.json ./
RUN npm install

# Build static assets using Vite
COPY . .
RUN npm run build

# Use NGINX to serve the static assets
FROM nginx:alpine
# Copy our custom NGINX configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf
# Copy the compiled React/Vite assets to NGINX's serving directory
COPY --from=build /app/dist /usr/share/nginx/html

EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]
