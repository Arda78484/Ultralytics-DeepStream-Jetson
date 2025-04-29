#!/usr/bin/env python3

################################################################################
# Copyright (c) 2020-2023, NVIDIA CORPORATION. All rights reserved.
# Copyright (c) 2024, Refactored by AI Assistant based on user request.
#
# Permission is hereby granted, free of charge, to any person obtaining a
# copy of this software and associated documentation files (the "Software"),
# to deal in the Software without restriction, including without limitation
# the rights to use, copy, modify, merge, publish, distribute, sublicense,
# and/or sell copies of the Software, and to permit persons to whom the
# Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.  IN NO EVENT SHALL
# THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING
# FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER
# DEALINGS IN THE SOFTWARE.
################################################################################

import sys
import gi
import platform
import signal # For graceful shutdown

gi.require_version('Gst', '1.0')
from gi.repository import GLib, Gst

# --- User Configuration ---
# Edit these constants to change camera settings
V4L2_DEVICE = "/dev/video0"  # Camera device node
VIDEO_FORMAT = "YUY2"       # Options: "YUY2", "MJPG"
CAPTURE_WIDTH = 640        # Capture width
CAPTURE_HEIGHT = 480       # Capture height
CAPTURE_FPS = 30           # Capture framerate
# --- End User Configuration ---


# Global variable for the main loop
main_loop = None

def signal_handler(sig, frame):
    """ Handles Ctrl+C signal to gracefully stop the loop. """
    print("\nCtrl+C pressed, stopping pipeline...")
    if main_loop:
        main_loop.quit()

def bus_call(bus, message, loop):
    """Callback function for handling messages from the GStreamer bus."""
    msg_type = message.type
    if msg_type == Gst.MessageType.EOS:
        print("End-of-stream received.")
        loop.quit()
    elif msg_type == Gst.MessageType.WARNING:
        err, debug = message.parse_warning()
        print(f"Warning from {message.src.get_name()}: {err}\n  Debug info: {debug}", file=sys.stderr)
    elif msg_type == Gst.MessageType.ERROR:
        err, debug = message.parse_error()
        print(f"Error from {message.src.get_name()}: {err}\n  Debug info: {debug}", file=sys.stderr)
        if isinstance(message.src, Gst.Element) and "v4l2" in message.src.get_factory().get_name():
             if "Cannot identify device" in debug or "Failed to open device" in debug:
                 print(f"Hint: Failed to open V4L2 device '{V4L2_DEVICE}'. Check permissions or Docker access.", file=sys.stderr)
             elif "Device or resource busy" in debug:
                 print(f"Hint: V4L2 device '{V4L2_DEVICE}' is busy. Is another application using it?", file=sys.stderr)
        loop.quit()
    return True

def on_fps_measurement(fpsdisplaysink, fps, droprate, avgfps):
    """Callback function for FPS measurements."""
    # '\r' carriage return moves cursor to the beginning of the line
    # ' ' padding ensures previous longer lines are overwritten
    print(f"\rFPS: {fps:.2f}, Dropped: {droprate:.2f}, Average FPS: {avgfps:.2f}        ", end='')

def create_element(factory_name, element_name, exit_on_error=True):
    """Creates a GStreamer element, handling potential errors."""
    print(f"  Creating element: {factory_name} (name={element_name})")
    element = Gst.ElementFactory.make(factory_name, element_name)
    if not element:
        print(f"Error: Unable to create element '{factory_name}'. Check GStreamer installation/plugins.", file=sys.stderr)
        if exit_on_error:
            sys.exit(1)
    return element

def link_elements(elements):
    """Links a list of GStreamer elements sequentially."""
    print("Linking pipeline elements:")
    for i in range(len(elements) - 1):
        src_elem = elements[i]
        dst_elem = elements[i+1]
        if src_elem is None or dst_elem is None:
            print(f"Error: Cannot link None element between element {i} and {i+1}", file=sys.stderr)
            return False

        print(f"  Linking '{src_elem.get_name()}' -> '{dst_elem.get_name()}'")
        if not src_elem.link(dst_elem):
            print(f"Error: Failed to link {src_elem.get_name()} to {dst_elem.get_name()}", file=sys.stderr)
            return False
    return True

def main():
    """Main function to create and run the GStreamer pipeline."""
    global main_loop

    # --- Display Configuration ---
    print("Running with configuration (set as constants in script):")
    print(f"  Device: {V4L2_DEVICE}")
    print(f"  Format: {VIDEO_FORMAT}")
    print(f"  Resolution: {CAPTURE_WIDTH}x{CAPTURE_HEIGHT}")
    print(f"  Framerate: {CAPTURE_FPS}")
    if VIDEO_FORMAT not in ["YUY2", "MJPG"]:
        print(f"Error: Invalid VIDEO_FORMAT constant '{VIDEO_FORMAT}'. Choose 'YUY2' or 'MJPG'.", file=sys.stderr)
        return 1

    # --- GStreamer Initialization ---
    Gst.init(None)
    main_loop = GLib.MainLoop()
    signal.signal(signal.SIGINT, signal_handler) # Setup Ctrl+C handler

    print("\nCreating Pipeline...")
    pipeline = Gst.Pipeline.new("camera-display-pipeline")
    if not pipeline:
        print("Error: Unable to create Gst Pipeline.", file=sys.stderr)
        return 1

    # --- Element Creation ---
    elements = [] # List to hold pipeline elements in order

    print("\nCreating Elements...")
    # 1. Source Element (v4l2src)
    source = create_element("v4l2src", "camera-source")
    source.set_property('device', V4L2_DEVICE)
    # Try setting io-mode=4 (DMABUF) for potentially better performance on Jetson/compatible systems
    try:
        source.set_property('io-mode', 4)
        print("    Set v4l2src io-mode=DMABUF (4)")
    except Exception as e:
        print(f"    Warning: Could not set v4l2src io-mode to DMABUF (may not be supported): {e}")
        try:
            source.set_property('io-mode', 2) # Try MMAP as fallback
            print("    Set v4l2src io-mode=MMAP (2)")
        except Exception as e_mmap:
            print(f"    Warning: Could not set v4l2src io-mode to MMAP: {e_mmap}")
    elements.append(source)

    # 2. Caps Filter
    caps_filter_src = create_element("capsfilter", "source-caps-filter")
    if VIDEO_FORMAT == "YUY2":
        caps_str = f"video/x-raw, format=YUY2, width={CAPTURE_WIDTH}, height={CAPTURE_HEIGHT}, framerate={CAPTURE_FPS}/1"
    elif VIDEO_FORMAT == "MJPG":
        caps_str = f"image/jpeg, width={CAPTURE_WIDTH}, height={CAPTURE_HEIGHT}, framerate={CAPTURE_FPS}/1"
    # No else needed here because we checked VIDEO_FORMAT earlier

    print(f"    Setting source caps: {caps_str}")
    caps = Gst.Caps.from_string(caps_str)
    caps_filter_src.set_property("caps", caps)
    elements.append(caps_filter_src)

    # 3. Decoder (Conditional)
    decoder = None
    if VIDEO_FORMAT == "MJPG":
        # Prefer hardware decoder if available
        decoder = create_element("nvjpegdec", "jpeg-decoder-gpu", exit_on_error=False)
        if not decoder:
            print("    nvjpegdec failed, trying software jpegdec...")
            decoder = create_element("jpegdec", "jpeg-decoder-cpu")
        elements.append(decoder)

    # 4. Video Converter (nvvidconv - GPU accelerated)
    nvvidconv = create_element("nvvidconv", "video-converter-gpu")
    elements.append(nvvidconv)

    # 5. Underlying Sink Element (Display)
    # Prefer nveglglessink for hardware acceleration on NVIDIA platforms
    video_sink_element = create_element("nveglglessink", "display-sink-actual", exit_on_error=False)
    if not video_sink_element:
        print("    nveglglessink failed, trying autovideosink...")
        video_sink_element = create_element("autovideosink", "display-sink-actual")
    # Setting sync=False can improve latency/throughput but may cause tearing/stuttering
    video_sink_element.set_property('sync', False)
    # video_sink_element.set_property('qos', False) # Optional

    # 6. FPS Display Sink Wrapper
    fps_sink = create_element("fpsdisplaysink", "fps-display")
    fps_sink.set_property("video-sink", video_sink_element) # Set the actual sink
    fps_sink.set_property("signal-fps-measurements", True) # Enable the signal
    fps_sink.set_property("text-overlay", False) # We'll print to console instead
    fps_sink.connect("fps-measurements", on_fps_measurement)
    elements.append(fps_sink)

# --- Build the Pipeline ---
    print("\nAdding elements to Pipeline...")
    # Filter out None elements (e.g., if decoder failed creation and exit_on_error was False)
    active_elements = [elem for elem in elements if elem is not None]

    # Add elements one by one
    for element in active_elements:
        print(f"  Adding '{element.get_name()}' to pipeline.")
        if not pipeline.add(element):
            print(f"Error: Failed to add element '{element.get_name()}' to the pipeline.", file=sys.stderr)
            return 1 # Exit if adding any element fails

    # --- Link the Elements ---
    if not link_elements(active_elements):
        print("Error: Pipeline linking failed.", file=sys.stderr)
        return 1

    # --- Setup Bus Watch ---
    bus = pipeline.get_bus()
    bus.add_signal_watch()
    bus.connect("message", bus_call, main_loop)

    # --- Run ---
    print("\nStarting pipeline...")
    pipeline.set_state(Gst.State.PLAYING)
    print("Pipeline running. Press Ctrl+C to stop.")

    try:
        main_loop.run()
    except Exception as e:
        print(f"\nAn unexpected error occurred during main loop execution: {e}", file=sys.stderr)
    finally:
        # --- Cleanup ---
        print("\nExiting application...")
        # Ensure newline after FPS counter ends
        print()
        print("Setting pipeline to NULL state...")
        pipeline.set_state(Gst.State.NULL)
        print("Pipeline stopped.")
        # Gst.deinit() # Optional, usually not needed at script exit

    return 0

if __name__ == '__main__':
    sys.exit(main())