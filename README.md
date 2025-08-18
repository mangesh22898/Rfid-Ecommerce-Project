# RFID-Enabled Business Card Ordering Platform

This repository contains a complete, containerised microservice
architecture for a university internal application that allows staff and
students to configure and order RFID‑enabled business cards. The system
consists of a static frontend served via Nginx and several FastAPI
backend services running on Kubernetes.

## Microservices

| Service           | Description                                                                 | Default Port |
|-------------------|-----------------------------------------------------------------------------|--------------|
| **frontend**      | Static HTML/JS/CSS application allowing users to select a card template,
                      enter their personal details, preview the card, add it to a cart and
                      complete the checkout process. In production the frontend is served via
                      Nginx.                                                                      | 80           |
| **catalog**       | Provides a catalogue of available card templates. Returns a static list of
                      five templates (id, name, description, colour).                             | 80           |
| **cart**          | Maintains a simple in‑memory cart. Supports listing cart contents,
                      adding items and removing items.                                             | 80           |
| **checkout**      | Accepts completed orders, persists them to a JSON file and calls the
                      email service to send confirmation emails.                                   | 80           |
| **email**         | Sends order confirmation emails to the user and an administrator. In the
                      prototype it prints messages to standard output but can be configured to
                      use a real SMTP server.                                                      | 80           |
| **orders**        | Provides an admin‑only endpoint to list all placed orders. Reads from
                      the same JSON file written by the checkout service.                          | 80           |
| **mongo**         | MongoDB instance (planned for future persistence layer).                    | 27017        |

## Running Locally Without Kubernetes

Each service is built on FastAPI and can be run directly with
`uvicorn`. Ensure you have Python 3.11 installed. The project uses
FastAPI, Uvicorn and Requests, all of which are specified in
`base-requirements.txt`. If you are offline you can still run the
services because they are bundled in this repository.

```bash
# Change into each service directory and start it on its own port
cd rfid-card-app/catalog-service && uvicorn main:app --reload --port 8001 &
cd rfid-card-app/cart-service    && uvicorn main:app --reload --port 8002 &
cd rfid-card-app/checkout-service && uvicorn main:app --reload --port 8003 &
cd rfid-card-app/email-service   && uvicorn main:app --reload --port 8004 &
cd rfid-card-app/orders-service  && uvicorn main:app --reload --port 8005 &

# Serve the frontend using a simple HTTP server
cd rfid-card-app/frontend && python3 -m http.server 8080

# Then open http://localhost:8080 in your browser. The frontend
# assumes the API endpoints are accessible at /api/ on the same domain.
# You can use a reverse proxy like Nginx or Caddy locally to route
# /api/catalog → localhost:8001, /api/cart → localhost:8002, etc.
```

## Docker Images

Each service has its own `Dockerfile` that installs the Python
dependencies, copies the application code and runs Uvicorn. The
frontend uses an Alpine Nginx image to serve static files. Before
building these images you should edit the Kubernetes manifests under
`k8s-manifests/` and replace `YOUR_DOCKERHUB_USERNAME` with your actual
Docker Hub user name.

To build and run an image locally:

```bash
docker build -t myuser/catalog-service:latest -f rfid-card-app/catalog-service/Dockerfile rfid-card-app/catalog-service
docker run -p 8001:80 myuser/catalog-service:latest
```

Follow the same pattern for the other services.

## Kubernetes Deployment

All Kubernetes manifests live in `k8s-manifests/`. They include:

* Deployments and Services for each microservice and the MongoDB database.
* A `PersistentVolumeClaim` (`orders-pvc`) used by both checkout and orders
  services to share the JSON orders file.
* An Ingress (`ingress.yaml`) that routes `/api/*` paths to the relevant
  backend service and everything else to the frontend. The host is
  configured as `rfid.local`; adjust this for your cluster/domain.

To deploy on a local Minikube cluster:

```bash
# Start minikube and enable ingress (nginx) addon
minikube start
minikube addons enable ingress

# Create a namespace (optional)
kubectl create namespace rfid-app
kubectl config set-context --current --namespace=rfid-app

# Apply PVC first, then all services
kubectl apply -f k8s-manifests/orders-pvc.yaml
kubectl apply -f k8s-manifests/mongo-deployment.yaml
kubectl apply -f k8s-manifests/catalog-deployment.yaml
kubectl apply -f k8s-manifests/cart-deployment.yaml
kubectl apply -f k8s-manifests/checkout-deployment.yaml
kubectl apply -f k8s-manifests/email-deployment.yaml
kubectl apply -f k8s-manifests/orders-deployment.yaml
kubectl apply -f k8s-manifests/frontend-deployment.yaml
kubectl apply -f k8s-manifests/ingress.yaml

# Determine the ingress IP and update your hosts file
minikube ip
# Add a line to /etc/hosts like:  <minikube-ip> rfid.local

# Then access the app at http://rfid.local
```

## Continuous Integration and Delivery

A GitHub Actions workflow under `.github/workflows/build-and-deploy.yml`
automates the build and push of Docker images on every commit to the
`main` branch. It expects the following secrets to be configured in
your GitHub repository settings:

* `DOCKERHUB_USERNAME` and `DOCKERHUB_TOKEN` – credentials for pushing
  images to your Docker Hub account.
* `ARGOCD_SERVER`, `ARGOCD_USERNAME`, `ARGOCD_PASSWORD` and
  `ARGOCD_APP_NAME` – used to authenticate with an ArgoCD server and
  trigger a deployment sync.

The deployment job is optional; remove it if you are not using ArgoCD.

## Future Enhancements

* Replace the in‑memory cart and file‑based order store with MongoDB. A
  deployment manifest for MongoDB is included and can be used as a
  foundation. Once `pymongo` or an equivalent driver is available,
  persistence can be implemented in the services.
* Implement user authentication and per‑user cart isolation.
* Add an admin UI that consumes the `/api/orders` endpoint for order
  management.
* Improve the visual design of the frontend and make it responsive.

---

This project provides a complete example of how to build and deploy a
simple microservice architecture on Kubernetes, from local development
through to CI/CD and GitOps. Feel free to extend and adapt it to suit
your university's needs.
