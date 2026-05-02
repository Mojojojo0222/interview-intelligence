"""Run this once to update all agent files to use config instead of hardcoded URLs"""
import os

agents_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                          'services', 'agent-service', 'agents')

old_header = '''import os
from crewai import Agent, LLM

llm = LLM(model="ollama/llama3.2:3b", base_url=os.getenv("OLLAMA_BASE_URL", "http://localhost:11434"))'''

new_header = '''import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                '..', '..', '..', 'interview-service'))
from config import OLLAMA_BASE_URL, OLLAMA_MODEL
from crewai import Agent, LLM

llm = LLM(model=f"ollama/{OLLAMA_MODEL}", base_url=OLLAMA_BASE_URL)'''

for fname in os.listdir(agents_dir):
    if fname.endswith('.py') and fname != '__init__.py':
        fpath = os.path.join(agents_dir, fname)
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
        if 'OLLAMA_BASE_URL' not in content or 'from config' not in content:
            content = content.replace(old_header, new_header)
            with open(fpath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"Updated: {fname}")
        else:
            print(f"Already updated: {fname}")

print("Done.")
