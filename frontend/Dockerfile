# Use nginx alpine image for serving static files
FROM nginx:alpine

# Copy custom nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Copy frontend files
COPY . /usr/share/nginx/html

# Expose port 80
EXPOSE 80

# Start nginx
CMD ["nginx", "-g", "daemon off;"]
