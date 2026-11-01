# D2: python:3.11-slim; all pip layers before the model COPY (last line) so a model-only
# change rebuilds only the final layer.
FROM python:3.11-slim
WORKDIR /app
COPY inference/requirements-runtime.txt .
RUN pip install --no-cache-dir -r requirements-runtime.txt
COPY data_pipeline/__init__.py data_pipeline/preprocessing.py /app/data_pipeline/
COPY inference/__init__.py inference/runtime.py inference/alert_store.py inference/safety.py inference/inference_service.py /app/inference/
COPY data_pipeline/training_stats.npy /app/training_stats.npy
ENV MODEL_PATH=/app/model.tflite STATS_PATH=/app/training_stats.npy MQTT_HOST=localhost TRUCK_ID=T001 STATE_DIR=/state
CMD ["python", "-m", "inference.inference_service"]
COPY inference/model.tflite inference/model.tflite.pipeline.json ./
