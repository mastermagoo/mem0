import os, re
from pathlib import Path
p = Path('/app/main.py')
s = p.read_text()
# Replace hard-coded base_url keys with env-driven
s = re.sub(r'"ollama_base_url":\s*"[^"]+"', '"ollama_base_url": os.environ.get("OLLAMA_BASE_URL", "http://ollama:11434")', s)
# Add infer to MemoryCreate
s = re.sub(r'(class MemoryCreate\(BaseModel\):\n\s*messages:[\s\S]*?metadata: Optional\[Dict\[str, Any\]\] = None\n)', r'\1    infer: Optional[bool] = False\n', s)
# Pass infer to add(...)
s = re.sub(r'(response = MEMORY_INSTANCE.add\(messages=\[m.model_dump\(\) for m in memory_create.messages\]\, )', r'\1infer=memory_create.infer, ', s)
Path('/app/main.py').write_text(s)
print('Patched /app/main.py for OLLAMA_BASE_URL and infer')
