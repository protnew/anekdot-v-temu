import sys, os, time
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# Write to a log file directly from Python
log = open(r"C:\6FBA~1\server_log.txt", "w", buffering=1)

def log_print(msg):
    print(msg, flush=True)
    log.write(msg + "\n")
    log.flush()

log_print(f"Python {sys.version}")
log_print(f"CWD: {os.getcwd()}")

try:
    sys.path.insert(0, r"C:\6FBA~1\SCRUM~1\70AA~1\5806~1")
    log_print("Importing main...")
    import main
    log_print(f"Main imported! Routes: {len(main.app.routes)}")
    
    log_print("Starting uvicorn on :8000...")
    import uvicorn
    uvicorn.run(main.app, host='0.0.0.0', port=8000, log_level='info')
except Exception as e:
    log_print(f"FATAL: {e}")
    import traceback
    traceback.print_exc(file=log)
    log.flush()
