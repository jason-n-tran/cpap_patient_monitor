from flask import Flask, request, jsonify
import requests
import logging
from datetime import datetime


# Create an instance of the Flask server
app = Flask(__name__)


if __name__ == "__main__":
    logging.basicConfig(filename="log_file.log", filemode="w",
                        level=logging.INFO)
    app.run()
