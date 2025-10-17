from flask import Flask, render_template, jsonify, request
from flask_socketio import SocketIO, emit
import subprocess
import os
import threading
import pty 

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key!' 
socketio = SocketIO(app, async_mode='threading', ws_server='simple-websocket') 

pipeline_running = False
pipeline_thread = None

@app.route('/')
def index():
    return render_template('realtime_ui.html') 

def run_pipeline_thread():
    global pipeline_running
    process = None # Define process variable outside try block
    master_fd = -1 # Define master_fd outside try block

    try:
        socketio.emit('status_update', {'status': 'Building & Running Pipeline...'})
        master_fd, slave_fd = pty.openpty()
        
        process = subprocess.Popen(
            ['./run_ci.sh'], 
            stdout=slave_fd, 
            stderr=slave_fd, 
            text=True, 
            bufsize=1,
            cwd=os.path.dirname(os.path.abspath(__file__))
        )
        os.close(slave_fd)

        with open(master_fd, 'r') as stdout_reader:
            while True:
                try:
                    line = stdout_reader.readline()
                    if not line:
                        break # Process finished normally
                    socketio.emit('pipeline_log', {'log': line.strip()})
                    socketio.sleep(0.01)
                # --- THIS IS THE FIX ---
                except OSError as e:
                    # If we get an Input/Output error, assume the pty was closed because the process ended
                    if e.errno == 5: 
                        socketio.emit('pipeline_log', {'log': f'[INFO] End of stream detected (OSError 5).'})
                        break 
                    else:
                        raise # Re-raise other OSErrors
                # --- END FIX ---

        return_code = process.wait() 

        if return_code == 0:
            socketio.emit('status_update', {'status': 'Pipeline Finished Successfully ✅'})
        else:
            socketio.emit('status_update', {'status': f'Pipeline Finished with Error (Code: {return_code}) ❌'})
            
    except Exception as e:
        socketio.emit('status_update', {'status': f'Error running pipeline: {str(e)} ❌'})
        socketio.emit('pipeline_log', {'log': f'BACKEND ERROR: {str(e)}'})
    finally:
        pipeline_running = False
        # Ensure master_fd is closed if it was opened
        if master_fd != -1:
            try:
                os.close(master_fd)
            except OSError:
                pass # Ignore errors if already closed

@app.route('/run', methods=['POST'])
def run_pipeline():
    global pipeline_running, pipeline_thread
    if pipeline_running:
        return jsonify({"status": "error", "message": "Pipeline already running."}), 409
    pipeline_running = True
    socketio.emit('status_update', {'status': 'Pipeline run requested...'})
    socketio.emit('clear_logs', {}) 
    pipeline_thread = threading.Thread(target=run_pipeline_thread)
    pipeline_thread.start()
    return jsonify({"status": "success", "message": "Pipeline started."}), 202

if __name__ == '__main__':
    print("Starting Flask server with SocketIO on http://localhost:5000")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False, allow_unsafe_werkzeug=True) 
