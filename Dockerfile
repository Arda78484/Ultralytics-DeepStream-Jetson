FROM nvcr.io/nvidia/deepstream:7.1-triton-multiarch

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive

# Install necessary dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    apt-utils \
    git \
    wget \
    build-essential \
    libssl-dev \
    libopencv-dev \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN pip install -U pip

# Clone the Ultralytics repository
RUN git clone https://github.com/ultralytics/ultralytics /ultralytics

# Install Ultralytics with necessary dependencies
WORKDIR /ultralytics
RUN pip install -e ".[export]" onnxslim

# Clone the DeepStream-Yolo repository
RUN git clone https://github.com/marcoslucianops/DeepStream-Yolo /DeepStream-Yolo

# Copy the export_yoloV8.py file from DeepStream-Yolo/utils to the ultralytics folder
RUN cp /DeepStream-Yolo/utils/export_yoloV8.py /ultralytics

# Download the YOLOv11 model (yolo11s.pt)
WORKDIR /ultralytics
RUN wget https://github.com/ultralytics/assets/releases/download/v8.3.0/yolo11s.pt

# Convert the YOLOv11 model to ONNX
RUN python3 export_yoloV8.py -w yolo11s.pt --opset 16 -s 1280 --simplify --dynamic

# Copy the generated ONNX model and labels.txt to the DeepStream-Yolo folder
RUN cp yolo11s.pt.onnx labels.txt /DeepStream-Yolo  

# Set the CUDA version for JetPack 6.1
ENV CUDA_VER=12.6

# Compile the DeepStream-Yolo library
WORKDIR /DeepStream-Yolo
RUN make -C nvdsinfer_custom_impl_Yolo clean && make -C nvdsinfer_custom_impl_Yolo

WORKDIR /

# Default command to use bash shell instead of DeepStream
CMD ["/bin/bash"]