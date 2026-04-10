import requests
import json
import sys

print('Connecting to Ollama to pull llama3.2:1b...')
try:
    response = requests.post(
        'http://localhost:11434/api/pull',
        json={'model': 'llama3.2:1b'},
        stream=True
    )
    for line in response.iter_lines():
        if line:
            data = json.loads(line.decode('utf-8'))
            status = data.get('status', '')
            if 'completed' in data and 'total' in data:
                pct = data['completed'] / data['total'] * 100
                sys.stdout.write(f'\r{status}: {pct:.1f}% ({data["completed"]}/{data["total"]} bytes)')
                sys.stdout.flush()
            else:
                print(f'\r{status}')
    print("\nDownload completed successfully.")
except Exception as e:
    print(f"\nError: {e}")
