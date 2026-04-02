from flask import Flask, jsonify, request, send_from_directory, abort
from flask_cors import CORS
from azure.eventhub import EventHubProducerClient, EventHubConsumerClient, EventData

app = Flask(__name__, static_folder="static", template_folder="templates")
CORS(app)

# --- Configuration ---
CONNECTION_STR = os.environ.get("EVENT_HUB_CONNECTION_STR", "")
EVENT_HUB_NAME = os.environ.get("EVENT_HUB_NAME", "clickstream")

_event_buffer = []
_buffer_lock = threading.Lock()
MAX_BUFFER = 50

# --- Helper: Send to Event Hubs ---
def send_to_event_hubs(event_dict: dict):
    if not CONNECTION_STR:
        app.logger.warning("EVENT_HUB_CONNECTION_STR is not set – skipping publish")
        return

    producer = EventHubProducerClient.from_connection_string(
        conn_str=CONNECTION_STR,
        eventhub_name=EVENT_HUB_NAME,
    )
    with producer:
        event_batch = producer.create_batch()
        # Ensure we are sending the full dictionary as a JSON string
        event_batch.add(EventData(json.dumps(event_dict)))
        producer.send_batch(event_batch)

# --- Background Consumer Logic ---
def _on_event(partition_context, event):
    body = event.body_as_str(encoding="UTF-8")
    try:
        data = json.loads(body)
    except json.JSONDecodeError:
        data = {"raw": body}

    with _buffer_lock:
        _event_buffer.append(data)
        if len(_event_buffer) > MAX_BUFFER:
            _event_buffer.pop(0)
    partition_context.update_checkpoint(event)

def start_consumer():
    if not CONNECTION_STR:
        return
    consumer = EventHubConsumerClient.from_connection_string(
        conn_str=CONNECTION_STR,
        consumer_group="$Default",
        eventhub_name=EVENT_HUB_NAME,
    )
    def run():
        with consumer:
            consumer.receive(on_event=_on_event, starting_position="-1")
    thread = threading.Thread(target=run, daemon=True)
    thread.start()

# --- Routes ---

@app.route("/")
def index():
    return send_from_directory("templates", "client.html")

@app.route("/dashboard")
def dashboard():
    return send_from_directory("templates", "dashboard.html")

@app.route("/track", methods=["POST"])
def track():
    if not request.json:
        abort(400)

    # FIXED: Take the entire JSON payload from the browser 
    # (this includes deviceType, browser, and os)
    event = request.json
    
    # Add/Overwrite the server-side timestamp
    event["timestamp"] = datetime.now(timezone.utc).isoformat()

    # Send the FULL enriched event to Azure
    send_to_event_hubs(event)

    with _buffer_lock:
        _event_buffer.append(event)
        if len(_event_buffer) > MAX_BUFFER:
            _event_buffer.pop(0)

    return jsonify({"status": "ok", "event": event}), 201

@app.route("/api/events", methods=["GET"])
def get_events():
    try:
        limit = min(int(request.args.get("limit", 20)), MAX_BUFFER)
    except ValueError:
        limit = 20
    with _buffer_lock:
        recent = list(_event_buffer[-limit:])
    summary = {}
    for e in recent:
        et = e.get("event_type", "unknown")
        summary[et] = summary.get(et, 0) + 1
    return jsonify({"events": recent, "summary": summary, "total": len(recent)}), 200

if __name__ == "__main__":
    start_consumer()
    app.run(debug=False, host="0.0.0.0", port=8000)