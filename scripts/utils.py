import json
import subprocess
import requests

def load_config(config_path):
    """Load configuration from JSON file"""
    with open(config_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def process_data(data_path):
    """Process and validate training data"""
    with open(data_path, 'r', encoding='utf-8') as f:
        data = [json.loads(line) for line in f]
    print(f"Loaded {len(data)} training examples")
    return data

def train_model(config_path):
    """Start fine-tuning using LLaMA-Factory"""
    cmd = f"docker exec -it llama_factory python src/train.py {config_path}"
    process = subprocess.Popen(cmd, shell=True)
    process.wait()
    if process.returncode != 0:
        raise Exception("Training failed")

def deploy_model(model_name, adapter_path, modelfile_path):
    """Deploy model to Ollama"""
    # Create new model
    cmd = f"ollama create {model_name} -f {modelfile_path}"
    process = subprocess.Popen(cmd, shell=True)
    process.wait()
    
    # Test model
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": model_name,
            "prompt": "Xin chào!"
        }
    )
    if response.status_code == 200:
        print(f"Model {model_name} deployed successfully")
    else:
        raise Exception("Model deployment failed") 