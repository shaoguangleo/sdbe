#include <stdio.h>
#include <syslog.h>
#include <unistd.h>
#include <pthread.h>
#include <sys/time.h>

#include "aphids.h"
#include "hashpipe.h"
#include "hashpipe_databuf.h"

#include "vdif_in_databuf.h"


static void *run_method(hashpipe_thread_args_t * args) {

  int rv = 0;
  int index = 0;
  vdif_packet_block_t null_vdif_packet_block = {};
  vdif_in_databuf_t *db_out = (vdif_in_databuf_t *)args->obuf;
  aphids_context_t aphids_ctx;

  // initialize the aphids context
  rv = aphids_init(&aphids_ctx, args);
  if (rv != APHIDS_OK) {
    hashpipe_error(__FUNCTION__, "error waiting for free databuf");
    pthread_exit(NULL);
  }

  while (run_threads()) { // hashpipe wants us to keep running

    while ((rv = hashpipe_databuf_wait_free((hashpipe_databuf_t *)db_out, index)) != HASHPIPE_OK) {

      if (rv == HASHPIPE_TIMEOUT) { // index is not ready
	continue;

      } else { // any other return value is an error

	// raise an error and exit thread
	hashpipe_error(__FUNCTION__, "error waiting for free databuf");
	pthread_exit(NULL);
	break;

      }

    }

    // update the data at this index
    db_out->blocks[index] = null_vdif_packet_block;

    // let hashpipe know we're done with the buffer (for now)
    hashpipe_databuf_set_filled((hashpipe_databuf_t *)db_out, index);

    // update the index modulo the maximum buffer depth
    index = (index + 1) % db_out->header.n_block;

    // update aphids statistics
    aphids_update(&aphids_ctx);

  } // end while(run_threads())

  // destroy aphids context and exit
  aphids_destroy(&aphids_ctx);

  return NULL;
}

static hashpipe_thread_desc_t vdif_in_null_thread = {
 name: "vdif_in_null_thread",
 skey: "VDIFIN",
 init: NULL,
 run:  run_method,
 ibuf_desc: {NULL},
 obuf_desc: {vdif_in_databuf_create}
};

static __attribute__((constructor)) void ctor()
{
  register_hashpipe_thread(&vdif_in_null_thread);
}