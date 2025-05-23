import psutil
import os

def get_memory_text():
    pid = os.getpid()
    process = psutil.Process(pid)
    memory_info = process.memory_info()
    memory = memory_info.rss
    unit = "bytes"
    
    if memory > 1024.0:
        memory = memory / 1024.0
        unit = "KB"

    if memory > 1024.0:
        memory = memory / 1024.0
        unit = "MB"

    if memory > 1024.0:
        memory = memory / 1024.0
        unit = "GB"

    return f"Memory Usage: {memory:.2f} {unit}"