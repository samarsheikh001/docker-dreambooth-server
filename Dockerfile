FROM pytorch/pytorch:latest

WORKDIR /

# Set environment variables
ENV HUGGINGFACE_TOKEN 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

RUN mkdir -p ~/.huggingface
# Write the Hugging Face token to the file
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
ADD https://sgp1.vultrobjects.com/dreambooth-files/main.py main.py
ADD https://raw.githubusercontent.com/samarsheikh001/dreambooth-server/main/to_ckpt.py to_ckpt.py
ADD "https://firebasestorage.googleapis.com/v0/b/copykitties-avatar.appspot.com/o/upload.py?alt=media&token=465f5809-c013-43c7-a089-718f75087b2b&_gl=1*vjv9hp*_ga*NjIyODc5MTgxLjE2ODY0MjM0OTY.*_ga_CW55HF8NVT*MTY4NjYwMjA0OC4xMi4xLjE2ODY2MDMxNzguMC4wLjA." upload.py

# Set the command to run when the container starts
CMD ["python", "main.py"]
