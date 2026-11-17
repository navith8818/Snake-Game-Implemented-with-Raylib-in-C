#if defined(PLATFORM_WEB)
#include <emscripten/emscripten.h>

// WebAssembly-safe non-blocking implementation of WaitTime.
// In desktop Raylib, WaitTime uses synchronous nanosleep() which halts the CPU thread.
// In single-threaded WebAssembly with Asyncify, nanosleep() halts the browser event loop and crashes.
// Replacing it with emscripten_sleep yields to the browser cleanly for the requested duration.
void WaitTime(double seconds) {
    if (seconds > 0.0) {
        emscripten_sleep((unsigned int)(seconds * 1000.0));
    }
}
#endif
