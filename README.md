# README.md
# Monero CPU Miner
Mines Monero using RandomX on your CPU.

## Prerequisites
- macOS (MacBook Pro)
- Homebrew: `brew install git cmake`
- Monero wallet address (from getmonero.org or exchange)
- GCC/Clang: `xcode-select --install`

## Setup
1. Create folder: `mkdir ~/monero-miner && cd ~/monero-miner`
2. Save `monero_miner.py` and this README.
3. Compile RandomX hasher:
   ```bash
   git clone https://github.com/tevador/RandomX.git
   cd RandomX
   ```
   Save `randomx_hasher.c` (see below), then:
   ```bash
   mkdir build && cd build
   cmake ..
   make
   mv randomx-hasher ../../randomx_hasher
   cd ../..
   rm -rf RandomX
   chmod +x randomx_hasher
   ```
4. Run:
   ```bash
   python3 monero_miner.py
   ```

## randomx_hasher.c
```c
#include <stdio.h>
#include <string.h>
#include "randomx.h"

int main(int argc, char *argv[]) {
    if (argc != 2) {
        fprintf(stderr, "Usage: %s <blob_hex>\n", argv[0]);
        return 1;
    }
    size_t blob_len = strlen(argv[1]) / 2;
    unsigned char *blob = malloc(blob_len);
    for (size_t i = 0; i < blob_len; i++) {
        sscanf(argv[1] + 2 * i, "%2hhx", &blob[i]);
    }
    randomx_flags flags = RANDOMX_FLAG_DEFAULT;
    randomx_cache *cache = randomx_alloc_cache(flags);
    randomx_dataset *dataset = randomx_alloc_dataset(flags);
    randomx_init_cache(cache, "RandomXKey", 9);
    randomx_init_dataset(dataset, cache, 0, randomx_dataset_item_count());
    randomx_vm *vm = randomx_create_vm(flags, cache, dataset);
    unsigned char hash[RANDOMX_HASH_SIZE];
    randomx_calculate_hash(vm, blob, blob_len, hash);
    for (int i = 0; i < RANDOMX_HASH_SIZE; i++) {
        printf("%02x", hash[i]);
    }
    printf("\n");
    randomx_destroy_vm(vm);
    randomx_release_cache(cache);
    randomx_release_dataset(dataset);
    free(blob);
    return 0;
}
```

## Usage
- Pool URL: `xmr-eu1.nanopool.org`
- Port: `10300`
- Wallet address: ~95 chars, starts with 4/8
- Worker name: e.g., `worker1`
- Password: Press Enter for `x`
- Keepalive: `yes` or `no`
- Stop: Ctrl+C

## Notes
- Hashrate: ~100-1000 H/s (M1/M2 CPU).
- Check shares on pool dashboard (e.g., Nanopool).
- XMRig is faster for production.

## Troubleshooting
- **randomx_hasher missing**: Compile it.
- **Connection issues**: Try `pool.supportxmr.com:3333`.
- **Low hashrate**: Check CPU usage (`top`).
