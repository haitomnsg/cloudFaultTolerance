# Fault Tolerance & Load Balancing Demo

This project demonstrates basic **fault tolerance** and **load balancing** using:

- 4 Python HTTP servers (web1–web4)
- An Nginx load balancer
- A small Tailwind CSS UI to visualize traffic and simulate failures

Everything runs in Docker using docker-compose.

---

## Architecture

**Services (from docker-compose.yml):**

- `web1`, `web2`, `web3`, `web4`
  - All use the same Python app from `server.py`
  - Expose HTTP on port `5000`
  - Each has its own `SERVER_NAME` (web1–web4) so responses are identifiable
- `loadbalancer`
  - Based on the official `nginx:latest` image
  - Listens on host port **8080** → container port **80**
  - Uses `ngix.conf` as its Nginx configuration
  - Serves the static UI from `static/index.html`
  - Load-balances `/api` requests across the 4 web servers
  - Proxies `/control` requests to the same backends

**Flow:**

1. UI in the browser calls `GET /api` on Nginx (port 8080).
2. Nginx distributes requests across `web1`–`web4`.
3. Each server responds with `Response from server: webX`.
4. UI parses responses and shows counts and percentages per server.
5. You can simulate failures on individual servers from the UI; Nginx will route around inactive servers.

---

## Prerequisites

- Docker
- Docker Compose

On Windows, make sure Docker Desktop is running.

---

## Running the Demo

From the project root (where docker-compose.yml lives):

```bash
docker-compose down        # optional cleanup
docker-compose up --build
```

Docker will build the Python image, start `web1`–`web4`, and start the Nginx load balancer.

When everything is running, open:

- http://localhost:8080

You should see the Tailwind UI.

---

## Using the UI

The UI shows:

- A **"Send Single Request"** button
- A **"Start Auto Requests" / "Stop Auto Requests"** toggle (1 request per second)
- A card for each server (web1–web4) with:
  - Status: **ACTIVE** or **INACTIVE (simulated failure)**
  - Response count and traffic percentage
  - A button to **Simulate Failure** or **Restore Server**
- A "Last Response" panel with the raw backend response and timestamp

### Normal operation

1. Click **Start Auto Requests** to send continuous traffic.
2. Watch the response counts and percentages for web1–web4.
   - With all servers active, traffic should be roughly evenly balanced.

### Simulating failures (disasters / hardware issues)

Each server can be toggled active/inactive from the UI:

1. Pick a server card (for example, `web2`).
2. Click **Simulate Failure**.
   - The card turns red and shows `INACTIVE (simulated failure)`.
   - Internally, `web2` switches an `ACTIVE` flag to `False`.
   - For `/api` requests, inactive servers respond with HTTP 503 to simulate failure.
3. Keep auto requests running and observe:
   - Nginx receives 503 from the inactive server and routes requests to the remaining active servers.
   - Response counts and percentages shift to web1, web3, and web4.
4. To bring a server back:
   - Click **Restore Server**.
   - The server becomes **ACTIVE**, and traffic starts flowing to it again.

This simulates a node going down and being restored, while the load balancer continues serving traffic using the remaining healthy nodes.

---

## How It Works (Backend Details)

**Python server (server.py):**

- Uses the built-in `http.server` module.
- Reads `SERVER_NAME` from the environment; falls back to `socket.gethostname()`.
- Maintains a process-level `ACTIVE` flag.
- Exposes:
  - `GET /api` – main endpoint used by the UI
    - If `ACTIVE` is `True`, returns `200` with `Response from server: webX`.
    - If `ACTIVE` is `False`, returns `503` with a message indicating the server is inactive.
  - `GET /control/toggle?target=NAME&active=true|false`
    - Only the server whose `SERVER_NAME` equals `NAME` updates its `ACTIVE` state.
    - Responds with a message confirming the new state (`STATUS UPDATED`).

**Nginx (ngix.conf):**

- Defines an `upstream backend` with `web1:5000`, `web2:5000`, `web3:5000`, `web4:5000`.
- In the main `server` block:
  - `location /` serves the static UI from `/usr/share/nginx/html`.
  - `location /api` proxies to the `backend` upstream.
  - `location /control` also proxies to `backend` for the toggle functionality.

**UI (static/index.html):**

- Built with plain HTML + Tailwind CSS via CDN.
- Uses JavaScript `fetch` to:
  - Call `/api` and update per-server metrics.
  - Call `/control/toggle` to toggle servers on/off.
- Retries `/control/toggle` a few times because control requests are also load-balanced; it waits until it sees a `STATUS UPDATED` message from the correct server.

---

## Stopping the Demo

From the project root:

```bash
docker-compose down
```

This stops and removes all containers created for the demo.

---

## Possible Extensions

Some ideas you could add on top of this demo:

- Health checks in Nginx (e.g., `max_fails`, `fail_timeout`, or active health check modules).
- Visual timeline of events (when servers went down/up).
- Metrics such as error rate, latency, or request logs.
- Multiple load balancers or regions to simulate larger architectures.
