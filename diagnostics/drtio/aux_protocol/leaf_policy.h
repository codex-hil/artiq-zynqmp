/* Fixed direct-link rank1 leaf readiness; LGPL-3.0-or-later. */
#pragma once
static inline int leaf_ready(unsigned destination,unsigned rank,unsigned route,
                             unsigned loaded,unsigned blocked,unsigned backend,
                             unsigned reset,unsigned errors) {
 return destination==1 && rank==1 && route && loaded && !blocked && backend && !reset && !errors;
}
