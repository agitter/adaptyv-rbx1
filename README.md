# GEM x Adaptyv: RBX1 Binder Design Competition
Dockerfile based on the moPPIt [Colab notebook](https://colab.research.google.com/drive/16n8PIwKwAiG-oDLm171BWvv-lQH0dHMg?usp=sharing).
Pushed the image to [DockerHub](https://hub.docker.com/repository/docker/agitter/moppit).

Use `pytorch/pytorch:2.10.0-cuda12.8-cudnn9-runtime` as a base to match `torch 2.10.0+cu128`
Colab used Python 3.12.12, and the Docker image uses 3.12 as well.

Build and push with 
```
docker build -t agitter/moppit:2.10.0-cuda12.8-py3.12 -f Dockerfile .
docker push agitter/moppit:2.10.0-cuda12.8-py3.12
```

`moppit-demo.sub` and `moppit-demo.sh` are small-scale tests of the process that support hard-coded parameters.

Claude Sonnet 4.6 was used to draft most files.
