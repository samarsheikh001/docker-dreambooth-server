FROM pytorch/pytorch:latest

WORKDIR /

RUN mkdir -p ~/.huggingface
# Use the environment variable to write the token to the file
RUN echo -n $HUGGINGFACE_TOKEN > ~/.huggingface/token

# Update system and install necessary system packages for git and wget
RUN apt-get update && apt-get install -y git wget && rm -rf /var/lib/apt/lists/*

# Upgrade pip and install necessary python packages.
RUN pip install --upgrade pip && \
    pip install -qq git+https://github.com/ShivamShrirao/diffusers && \
    pip install -q -U --pre triton && \
    pip install -q accelerate transformers ftfy bitsandbytes==0.35.0 gradio natsort safetensors xformers && \
    pip install -q boto3 firebase-admin python-dotenv

# Download necessary python files using ADD instead of wget.
ADD https://github.com/ShivamShrirao/diffusers/raw/main/examples/dreambooth/train_dreambooth.py train_dreambooth.py
ADD https://raw.githubusercontent.com/CompVis/stable-diffusion/main/configs/stable-diffusion/v1-inference.yaml v1-inference.yaml
ADD https://raw.githubusercontent.com/samarsheikh001/docker-dreambooth-server/main/server.py server.py
ADD https://raw.githubusercontent.com/samarsheikh001/docker-dreambooth-server/main/to_ckpt.py to_ckpt.py
ADD https://raw.githubusercontent.com/samarsheikh001/docker-dreambooth-server/main/upload.py upload.py
ADD https://raw.githubusercontent.com/samarsheikh001/docker-dreambooth-server/main/runpod.py runpod.py

# Set the command to run when the container starts
CMD ["python", "server.py"]
