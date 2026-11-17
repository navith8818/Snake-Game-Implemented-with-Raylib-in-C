import re
import sys

def patch_file(path, old, new):
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
    if old not in content:
        print(f"Warning: target string not found in {path}")
        return False
    content = content.replace(old, new, 1)
    with open(path, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"Successfully patched {path}")
    return True

# 1. Patch rcore.c
rcore_path = 'raylib/src/rcore.c'
with open(rcore_path, 'r', encoding='utf-8') as f:
    rcore = f.read()
rcore = '#if defined(__EMSCRIPTEN__)\n#include <emscripten/emscripten.h>\n#endif\n' + rcore
rcore = re.sub(
    r'void WaitTime\(double seconds\)\r?\n\{',
    'void WaitTime(double seconds)\n{\n#if defined(__EMSCRIPTEN__)\n    if (seconds > 0.0) emscripten_sleep((unsigned int)(seconds * 1000.0));\n    return;\n#endif',
    rcore
)
with open(rcore_path, 'w', encoding='utf-8') as f:
    f.write(rcore)
print('Successfully patched raylib/src/rcore.c')

# 2. Patch raudio.c
raudio_path = 'raylib/src/raudio.c'
t_raudio = """void UnloadAudioBuffer(AudioBuffer *buffer)
{
    if (buffer != NULL)
    {
        ma_data_converter_uninit(&buffer->converter, NULL);
        UntrackAudioBuffer(buffer);
        RL_FREE(buffer->data);
        RL_FREE(buffer);
    }
}"""
r_raudio = """void UnloadAudioBuffer(AudioBuffer *buffer)
{
    if (buffer != NULL)
    {
        buffer->playing = false;
        UntrackAudioBuffer(buffer);
        ma_data_converter_uninit(&buffer->converter, NULL);
        RL_FREE(buffer->data);
        RL_FREE(buffer);
    }
}"""
patch_file(raudio_path, t_raudio, r_raudio)

# 3. Patch miniaudio.h
miniaudio_path = 'raylib/src/external/miniaudio.h'
with open(miniaudio_path, 'r', encoding='utf-8') as f:
    ma = f.read()

t_active = "device.scriptNode.onaudioprocess = function(e) {\n                if (device.intermediaryBufferView == null || device.intermediaryBufferView.length == 0) {"
r_active = """device.scriptNode.onaudioprocess = function(e) {
                if (typeof Asyncify !== 'undefined' && (Asyncify.currData !== null || Asyncify.state !== 0)) {
                    for (var i = 0; i < e.outputBuffer.numberOfChannels; ++i) e.outputBuffer.getChannelData(i).fill(0.0);
                    return;
                }
                try {
                if (device.intermediaryBufferView == null || device.intermediaryBufferView.buffer !== Module.HEAPF32.buffer || device.intermediaryBufferView.length == 0) {"""

ma = ma.replace(t_active, r_active, 1)

t_catch = """for (var iChannel = 0; iChannel < e.outputBuffer.numberOfChannels; ++iChannel) {
                        e.outputBuffer.getChannelData(iChannel).fill(0.0);
                    }
                }
            };"""
r_catch = """for (var iChannel = 0; iChannel < e.outputBuffer.numberOfChannels; ++iChannel) {
                        e.outputBuffer.getChannelData(iChannel).fill(0.0);
                    }
                }
                } catch(err) {
                    for (var i = 0; i < e.outputBuffer.numberOfChannels; ++i) e.outputBuffer.getChannelData(i).fill(0.0);
                }
            };"""
ma = ma.replace(t_catch, r_catch, 1)

with open(miniaudio_path, 'w', encoding='utf-8') as f:
    f.write(ma)
print('Successfully patched raylib/src/external/miniaudio.h')
