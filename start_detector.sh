#!/bin/bash
export AZURE_KEY="8SB6MDrRYgBJWAfbybO26TJQydLNJAfkWkzX0DLMZGupoo6HR6bJJQQJ99CCACYeBjFXJ3w3AAAFACOGp3iM"
export AZURE_ENDPOINT="https://dnsvisionprodemo.cognitiveservices.azure.com/"
export EVENTS_DIR="/home/manny/dns-vision-ai/events"
export BANK_DIR="/home/manny/dns-vision-ai/image_bank"

python3 /home/manny/dns-vision-ai/services/motion_detector/motion_detector_azure.py
