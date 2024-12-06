"""
If you are in the same directory as this file (app.py), you can run run the app using gunicorn:
    
    $ gunicorn --bind 0.0.0.0:<PORT> app:app

gunicorn can be installed via:

    $ pip install gunicorn

"""
import os
import logging
from flask import Flask, jsonify, request
import pandas as pd
import joblib
from wandb import Api

LOG_FILE = 'flask.log'
MODEL_DIR = 'models'
DEFAULT_MODEL = 'lg_distance.pkl'

model = None

def create_app():
    app = Flask(__name__)
    app.logger.setLevel(logging.INFO)

    initialize_app(app)
    register_routes(app)

    return app


def initialize_app(app):
    """Initializes the app: setup logging and load the default model."""
    logging.basicConfig(filename=LOG_FILE, level=logging.INFO, format="%(asctime)s - %(message)s")
    os.makedirs(MODEL_DIR, exist_ok=True)

    global model
    model_path = os.path.join(MODEL_DIR, DEFAULT_MODEL)

    if os.path.exists(model_path):
        model = joblib.load(model_path)
        app.logger.info(f'Loaded default model: {DEFAULT_MODEL} from local storage')
    else:
        app.logger.warning(f"Default model {DEFAULT_MODEL} not found locally. Attempting to fetch from WandB...")

        try:
            workspace = 'IFT6758.2024-B08'
            model_name = 'lg_distance'

            api_key = os.getenv('WANDB_API_KEY', None)
            if not api_key:
                raise ValueError("WANDB_API_KEY is not set. Please set your WandB API key.")

            api = Api(api_key=api_key)
            artifact = api.artifact(f"{workspace}/{model_name}:latest")
            artifact.download(MODEL_DIR)

            model = joblib.load(model_path)
            app.logger.info(f"Downloaded and loaded default model {DEFAULT_MODEL} from WandB")
        except Exception as e:
            model = None
            app.logger.error(f"Failed to download/load default model {DEFAULT_MODEL} from WandB: {e}")


def register_routes(app):
    @app.route("/logs", methods=["GET"])
    def logs():
        """Reads data from the log file and returns them as the response"""
        try:
            with open(LOG_FILE, "r") as log_file:
                log_data = log_file.readlines()
            return jsonify({"logs": log_data})
        except FileNotFoundError:
            return jsonify({"error": "Log file not found"}), 404


    @app.route("/download_registry_model", methods=["POST"])
    def download_registry_model():
        """
        Handles POST requests made to http://IP_ADDRESS:PORT/download_registry_model

        The comet API key should be retrieved from the ${COMET_API_KEY} environment variable.

        Recommend (but not required) json with the schema:

            {
                workspace: (required),
                model: (required),
                version: (required),
                ... (other fields if needed) ...
            }
        
        """
        json = request.get_json()
        app.logger.info(json)

        request_data = request.get_json()
        workspace = request_data.get("workspace")
        model_name = request_data.get("model")
        version = request_data.get("version")

        api = Api()
        
        try:
            model_path = os.path.join(MODEL_DIR, f"{model_name}_{version}.pkl")
            
            if os.path.exists(model_path):
                global model
                model = joblib.load(model_path)
                app.logger.info(f"Loaded model {model_name} version {version} from local storage")
                
                return jsonify({"message": f"Model {model_name} version {version} loaded from local storage"})

            artifact = api.artifact(f"{workspace}/{model_name}:{version}")
            artifact.download(MODEL_DIR)
            model = joblib.load(model_path)
            app.logger.info(f"Downloaded and loaded model {model_name} version {version}")

            return jsonify({"message": f"Model {model_name} version {version} downloaded and loaded"})

        except Exception as e:
            app.logger.error(f"Failed to download/load model {model_name} version {version}: {e}")
            return jsonify({"error": f"Failed to download/load model: {e}"}), 500


    @app.route("/predict", methods=["POST"])
    def predict():
        """
        Handles POST requests made to http://IP_ADDRESS:PORT/predict

        Returns predictions
        """
        json = request.get_json()
        app.logger.info(json)

        if model is None:
            return jsonify({"error": "No model is currently loaded"}), 500

        try:
            input_data = request.get_json()
            df = pd.DataFrame(input_data)

            predictions = model.predict_proba(df)[:, 1]
            response = {"predictions": predictions.tolist()}
            app.logger.info(f"Generated predictions: {response}")
            
            return jsonify(response)

        except Exception as e:
            app.logger.error(f"Prediction failed: {e}")
            return jsonify({"error": f"Prediction failed: {e}"}), 500
    

app = create_app() # this way we only have to do "python app.py" to run the app

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
