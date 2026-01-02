# Deployment Verification Checklist

Use this checklist to verify your production deployment.

## 1. Pre-Deployment Check
- [ ] `docker-compose.yml` uses `expose: "5000"` for backend (NOT `ports`).
- [ ] `nginx-https.conf` is correct (no `user nginx;`, strict HTTPS).
- [ ] Backend `app.py` binds to `0.0.0.0` (Verified).

## 2. Deployment Steps
1. Stop existing containers:
   ```bash
   docker compose down
   ```

2. Generate Certificates (if not already present):
   ```bash
   # Run certbot to get certificates
   docker compose run --rm certbot certonly --webroot --webroot-path /var/www/certbot -d civicfix-server.asolvitra.tech
   
   # NOTE: If this fails because nginx isn't running to serve the challenge, 
   # temporarily start nginx with a simple HTTP config or use standalone mode.
   # Ideally, start nginx first (it might fail on SSL if certs missing), then run certbot, then restart nginx.
   ```

3. Start Services:
   ```bash
   docker compose up -d
   ```

4. Verify Running Containers:
   ```bash
   docker ps
   # Should see: civicfix-backend, civicfix-nginx (civicfix-certbot should be exited)
   ```

## 3. Verification

### Nginx Configuration
- [ ] Test configuration syntax:
  ```bash
  docker compose exec nginx nginx -t
  ```
- [ ] Check listening ports:
  ```bash
  docker compose exec nginx ss -lntp | grep -E '80|443'
  # Output must show *:80 and *:443 (or :::80 / :::443)
  ```

### HTTPS Access
- [ ] Visit `https://civicfix-server.asolvitra.tech/health`
  - Should return `{"status": "healthy", ...}` (from backend)
- [ ] Visit `https://civicfix-server.asolvitra.tech/nginx-health`
  - Should return `healthy` (direct from Nginx)
- [ ] Browser check: Lock icon should be present and valid.

### HTTP to HTTPS Redirect
- [ ] Visit `http://civicfix-server.asolvitra.tech`
  - Should automatically redirect to `https://...`

## 4. Maintenance
- **Renew Certificates**:
  ```bash
  docker compose run --rm certbot renew
  docker compose exec nginx nginx -s reload
  ```

## 5. Troubleshooting

### "Container is restarting" Error
If you see `Error response from daemon: Container ... is restarting`, it means Nginx is failing to start, usually because **HTTPS certificates are missing**.

**Solution:**
Nginx cannot start in HTTPS mode without certificates, but you need running Nginx to get certificates.

1. **Run the Setup Script in Git Bash/Terminal**:
   ```bash
   chmod +x setup-letsencrypt.sh
   ./setup-letsencrypt.sh
   ```

2. **Manual Fix (if script fails)**:
   - Create `nginx-http.conf` (HTTP only).
   - Edit `docker-compose.yml` to mount `nginx-http.conf` instead of `nginx-https.conf`.
   - `docker compose up -d nginx`
   - Run the Certbot command from step 2 above.
   - Revert `docker-compose.yml` to use `nginx-https.conf`.
   - `docker compose restart nginx`

