### Configuration Files (`config*.txt`)

These files define model-related operations:

*   `model-engine-file`: Path to the generated TensorRT engine file.
*   `onnx-file`: Path to the ONNX model file (converted from `.pt`).
*   `#int8-calib-file`: Path to the INT8 calibration file (if using INT8 precision). Refer to documentation for calibration details.
*   `labelfile-path`: Path to the file containing label names (order matters).
*   `batch-size`: Set to `1` for a single camera, `2` or more for multiple cameras.
*   `network-mode`: Precision mode (`0`=FP32, `1`=INT8, `2`=FP16).

### Inference Configuration (`deepstream_app_config.txt`)

This file defines the DeepStream pipeline, including sources.

**Example RTSP Camera Source:**

```ini
[source0]
enable=1
#Type - 1=CameraV4L2 2=URI 3=MultiURI 4=RTSP
type=4
uri=rtsp://admin:OpenZeka2016@192.168.1.252:554/cam/realmonitor?channel=1&subtype=0&unicast=true&proto=Onvif
num-sources=1
gpu-id=0
latency=100
drop-frame-interval=0
# 0=nvbuf-mem-default 1=nvbuf-mem-cuda-pinned 2=nvbuf-mem-cuda-device 3=nvbuf-mem-cuda-unified
nvbuf-memory-type=0
```

**Example USB Camera Source:**

```ini
[source1]
enable=1
#Type - 1=CameraV4L2 2=URI 3=MultiURI 4=RTSP
type=1
camera-width=640
camera-height=480
camera-fps-n=30
camera-v4l2-dev-node=0 # Typically /dev/video0
```

**Note:** Replace `[sourceX]` with the appropriate source number (e.g., `[source0]`, `[source1]`).

model_b1_gpu0_fp32.engine = tek kamera 4 bit (29FPS)
model_b2_gpu0_fp32.engine = çok kamera 4 bit (15FPS)
model_b2_gpu0_fp16.engine = çok kamera 2 bit (24FPS)
