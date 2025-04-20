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
