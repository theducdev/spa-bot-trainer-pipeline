import os
import json
from utils import load_config, process_data, train_model, deploy_model

def main():
    # Load configurations
    config = load_config("../configs/chatbot_config.json")
    
    # Process training data
    process_data("../data/training.jsonl")
    
    # Start fine-tuning
    train_model("../configs/fine_tune_spa.yaml")
    
    # Deploy to Ollama
    deploy_model(
        model_name=config["model_name"],
        adapter_path="../ollama/adapter_model.bin",
        modelfile_path="../ollama/Modelfile"
    )

if __name__ == "__main__":
    main() 