#!/bin/bash

docker run -p 5000:5000 -e WANDB_API_KEY=${WANDB_API_KEY} ift6758/serving:latest