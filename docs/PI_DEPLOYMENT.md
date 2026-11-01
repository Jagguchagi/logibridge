# Optional: Raspberry Pi 5 target

On the Pi, `localhost:5000` is the Pi itself and an x86 image fails with "exec format error".
1. Bind the registry to the laptop's LAN address in compose.yml (`"<LAPTOP_IP>:5000:5000"`).
2. On the Pi, add `{"insecure-registries": ["<LAPTOP_IP>:5000"]}` to /etc/docker/daemon.json and restart Docker (lab only).
3. On the laptop: `sh scripts/build_arm64.sh <LAPTOP_IP>`.
4. Inventory line: `pi ansible_host=<PI_IP> ansible_user=<user> ansible_python_interpreter=/usr/bin/python3`; install python3-requests on the Pi.
5. Run the playbook with `-e image_name=<LAPTOP_IP>:5000/logibridge:v1-arm64`, twice.
6. Sync clocks (chrony) before timing anything, and report Pi latency separately from laptop latency.
