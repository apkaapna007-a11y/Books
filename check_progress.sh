#!/bin/bash
# Check if the upload script is still running
if ps aux | grep -v grep | grep upload_to_pinecone.py > /dev/null; then
    echo "Process is still running..."
    echo "Last 30 lines of log:"
    tail -30 /home/engine/project/pinecone_upload.log
else
    echo "Process completed!"
    echo "Full log:"
    cat /home/engine/project/pinecone_upload.log
fi
