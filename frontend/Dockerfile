# frontend/Dockerfile

# --- Stage 1: Build the React App ---
FROM node:18-alpine as builder
WORKDIR /app
COPY package*.json ./
RUN npm install
COPY . .

# We set the API URL to localhost because React runs in the user's browser
ARG VITE_API_URL=http://localhost:8000
ENV VITE_API_URL=$VITE_API_URL

RUN npm run build

# --- Stage 2: Serve with Nginx ---
FROM nginx:alpine
# Copy the built files from Stage 1
COPY --from=builder /app/dist /usr/share/nginx/html
# Copy our custom Nginx config (we will create this next)
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]