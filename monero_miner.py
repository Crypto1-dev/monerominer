# monero_miner.py
import json
import socket
import threading
import time
import binascii
import subprocess
import os
import logging
import sys

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# RandomX hashing function
def randomx_hash(blob):
    try:
        process = subprocess.run(
            ['./randomx_hasher', blob.hex()],
            capture_output=True,
            text=True,
            check=True
        )
        hash_hex = process.stdout.strip()
        return binascii.unhexlify(hash_hex)
    except subprocess.CalledProcessError as e:
        logger.error(f"RandomX hash failed: {e}")
        return None
    except FileNotFoundError:
        logger.error("randomx_hasher not found. Compile it (see README).")
        sys.exit(1)

# Stratum client
class StratumClient:
    def __init__(self, pool_url, pool_port, wallet_address, worker_name, password, keepalive):
        self.pool_url = pool_url
        self.pool_port = pool_port
        self.wallet_address = wallet_address
        self.worker_name = worker_name
        self.password = password
        self.keepalive = keepalive
        self.sock = None
        self.job = None
        self.running = False
        self.nonce = 0
        self.keepalive_id = 3

    def connect(self):
        try:
            self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.sock.connect((self.pool_url, self.pool_port))
            logger.info(f"Connected to {self.pool_url}:{self.pool_port}")
            self.running = True
            return True
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False

    def send(self, data):
        try:
            self.sock.sendall((json.dumps(data) + "\n").encode())
        except Exception as e:
            logger.error(f"Send failed: {e}")

    def receive(self):
        try:
            data = self.sock.recv(4096).decode().strip()
            return json.loads(data)
        except Exception as e:
            logger.error(f"Receive failed: {e}")
            return None

    def login(self):
        login_msg = {
            "id": 1,
            "method": "login",
            "params": {
                "login": f"{self.wallet_address}.{self.worker_name}",
                "pass": self.password,
                "agent": "monero-miner/0.1"
            }
        }
        self.send(login_msg)
        response = self.receive()
        if response and "result" in response and "id" in response["result"]:
            logger.info("Login successful")
            self.job = response["result"]["job"]
            return True
        logger.error("Login failed")
        return False

    def submit_share(self, job_id, nonce, result):
        submit_msg = {
            "id": 2,
            "method": "submit",
            "params": {
                "id": job_id,
                "job_id": self.job["job_id"],
                "nonce": nonce,
                "result": result
            }
        }
        self.send(submit_msg)
        response = self.receive()
        if response and "result" in response and response["result"]["status"] == "OK":
            logger.info("Share accepted")
        else:
            logger.error("Share rejected")

    def send_keepalive(self):
        while self.running and self.keepalive:
            keepalive_msg = {
                "id": self.keepalive_id,
                "method": "keepalived"
            }
            self.send(keepalive_msg)
            response = self.receive()
            if response and "result" in response and response["result"]["status"] == "KEEPALIVED":
                logger.debug("Keepalive OK")
            else:
                logger.warning("Keepalive failed")
            time.sleep(60)

    def mine(self):
        while self.running:
            if not self.job:
                time.sleep(1)
                continue

            blob = binascii.unhexlify(self.job["blob"])
            target = int(self.job["target"], 16)
            job_id = self.job["job_id"]

            nonce_bytes = self.nonce.to_bytes(4, byteorder='little')
            blob = blob[:39] + nonce_bytes + blob[43:]

            hash_result = randomx_hash(blob)
            if not hash_result:
                continue
            hash_int = int.from_bytes(hash_result, byteorder='little')

            if hash_int < target:
                nonce_hex = nonce_bytes.hex()
                result_hex = hash_result.hex()
                logger.info(f"Found share: nonce={nonce_hex}, hash={result_hex}")
                self.submit_share(job_id, nonce_hex, result_hex)

            self.nonce += 1
            if self.nonce >= 0xFFFFFFFF:
                self.nonce = 0
                logger.info("Nonce overflow, waiting for new job")
                self.job = None

    def receive_jobs(self):
        while self.running:
            data = self.receive()
            if data and "method" in data and data["method"] == "job":
                self.job = data["params"]
                logger.info(f"New job: {self.job['job_id']}")

    def start(self):
        if not self.connect():
            return
        if not self.login():
            self.sock.close()
            return

        mining_thread = threading.Thread(target=self.mine)
        job_thread = threading.Thread(target=self.receive_jobs)
        keepalive_thread = threading.Thread(target=self.send_keepalive)
        mining_thread.daemon = True
        job_thread.daemon = True
        keepalive_thread.daemon = True
        mining_thread.start()
        job_thread.start()
        if self.keepalive:
            keepalive_thread.start()

        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            logger.info("Stopping miner")
            self.running = False
            self.sock.close()

def main():
    print("Monero CPU Miner")
    pool_url = input("Pool URL (e.g., xmr-eu1.nanopool.org): ").strip()
    while True:
        try:
            pool_port = int(input("Pool port (e.g., 10300): ").strip())
            break
        except ValueError:
            print("Port must be a number")
    wallet_address = input("Monero wallet address: ").strip()
    worker_name = input("Worker name (e.g., worker1): ").strip()
    password = input("Pool password (press Enter for 'x'): ").strip() or "x"
    keepalive = input("Enable keepalive? (yes/no): ").strip().lower() == "yes"

    client = StratumClient(
        pool_url,
        pool_port,
        wallet_address,
        worker_name,
        password,
        keepalive
    )
    client.start()

if __name__ == "__main__":
    main()
