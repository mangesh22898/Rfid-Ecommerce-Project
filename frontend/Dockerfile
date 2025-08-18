FROM nginx:alpine
# Copy frontend files into Nginx default html directory
COPY . /usr/share/nginx/html
EXPOSE 80
CMD ["nginx", "-g", "daemon off;"]