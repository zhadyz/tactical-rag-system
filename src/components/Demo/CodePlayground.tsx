import { useState } from 'react';
import { Sandpack } from '@codesandbox/sandpack-react';
import { motion } from 'framer-motion';
import { Code, Copy, Check, ExternalLink, Terminal } from 'lucide-react';

interface CodePlaygroundProps {
  className?: string;
}

type Framework = 'python' | 'nodejs' | 'curl';

interface CodeExample {
  id: string;
  name: string;
  description: string;
  framework: Framework;
  code: string;
  response: string;
  tags: string[];
}

const examples: CodeExample[] = [
  {
    id: 'python-basic',
    name: 'Basic Query (Python)',
    description: 'Simple RAG query using Python requests',
    framework: 'python',
    code: `import requests
import json

# Apollo RAG API endpoint
API_URL = "http://localhost:8000/api/query"

def query_apollo(question: str, mode: str = "adaptive") -> dict:
    """Query Apollo RAG system"""
    payload = {
        "question": question,
        "mode": mode,
        "use_context": True,
        "rerank_preset": "quality"
    }

    response = requests.post(API_URL, json=payload)
    response.raise_for_status()

    return response.json()

# Example usage
if __name__ == "__main__":
    result = query_apollo(
        "What are the key principles of Air Force leadership?",
        mode="adaptive"
    )

    print("Answer:", result["answer"])
    print("Processing time:", result["metadata"]["processing_time_ms"], "ms")
    print("Confidence:", result["metadata"]["confidence"])

    # Print sources
    print("\\nSources:")
    for i, source in enumerate(result.get("sources", []), 1):
        print(f"{i}. {source['metadata']['source']} (score: {source['metadata']['score']:.2f})")`,
    response: `Answer: The key principles of Air Force leadership include integrity first, service before self, and excellence in all we do. These core values guide all airmen in their duties and responsibilities...

Processing time: 1847 ms
Confidence: 0.89

Sources:
1. AFM 200-1: Fundamentals of Air Force Leadership (score: 0.94)
2. Leadership Doctrine (score: 0.87)
3. Core Values Framework (score: 0.82)`,
    tags: ['python', 'basic', 'query']
  },
  {
    id: 'nodejs-streaming',
    name: 'Streaming Response (Node.js)',
    description: 'Stream answers token-by-token for better UX',
    framework: 'nodejs',
    code: `const axios = require('axios');

async function streamQuery(question, onToken) {
  const API_URL = 'http://localhost:8000/api/query/stream';

  const response = await axios.post(
    API_URL,
    {
      question: question,
      mode: 'adaptive',
      use_context: true,
      rerank_preset: 'quality'
    },
    {
      responseType: 'stream'
    }
  );

  let buffer = '';

  response.data.on('data', (chunk) => {
    buffer += chunk.toString();

    // Process SSE events
    const lines = buffer.split('\\n\\n');
    buffer = lines.pop() || '';

    for (const line of lines) {
      if (line.startsWith('data: ')) {
        const data = JSON.parse(line.slice(6));

        if (data.type === 'token') {
          onToken(data.content);
        } else if (data.type === 'sources') {
          console.log('Sources:', data.content);
        } else if (data.type === 'metadata') {
          console.log('Metadata:', data.content);
        }
      }
    }
  });

  return new Promise((resolve) => {
    response.data.on('end', resolve);
  });
}

// Example usage
streamQuery(
  'What are the key principles of Air Force leadership?',
  (token) => {
    process.stdout.write(token);
  }
).then(() => {
  console.log('\\n\\nStreaming complete!');
});`,
    response: `The key principles... of Air Force... leadership include... integrity first... service before self... and excellence... in all we do...

Sources: [
  { source: "AFM 200-1", score: 0.94 },
  { source: "Leadership Doctrine", score: 0.87 }
]

Metadata: {
  processing_time_ms: 1847,
  confidence: 0.89,
  mode_used: "adaptive"
}

Streaming complete!`,
    tags: ['nodejs', 'streaming', 'advanced']
  },
  {
    id: 'curl-upload',
    name: 'Document Upload (curl)',
    description: 'Upload and process a new document',
    framework: 'curl',
    code: `# Upload a PDF document
curl -X POST http://localhost:8000/api/documents/upload \\
  -F "file=@leadership-manual.pdf" \\
  -H "Content-Type: multipart/form-data"

# Response:
# {
#   "file_name": "leadership-manual.pdf",
#   "file_size_bytes": 1245678,
#   "file_hash": "a1b2c3...",
#   "num_chunks": 218,
#   "processing_time_seconds": 4.23
# }

# List all documents
curl -X GET http://localhost:8000/api/documents/list

# Query with specific rerank preset
curl -X POST http://localhost:8000/api/query \\
  -H "Content-Type: application/json" \\
  -d '{
    "question": "What are the leadership competencies?",
    "mode": "adaptive",
    "use_context": true,
    "rerank_preset": "deep"
  }'`,
    response: `{
  "file_name": "leadership-manual.pdf",
  "file_size_bytes": 1245678,
  "file_hash": "a1b2c3d4e5f6...",
  "num_chunks": 218,
  "processing_time_seconds": 4.23
}

Documents: {
  "total_documents": 3,
  "total_chunks": 574,
  "documents": [...]
}

Query Response: {
  "answer": "The leadership competencies include...",
  "metadata": {
    "processing_time_ms": 2734,
    "confidence": 0.91
  }
}`,
    tags: ['curl', 'upload', 'api']
  },
  {
    id: 'python-batch',
    name: 'Batch Processing (Python)',
    description: 'Process multiple queries efficiently',
    framework: 'python',
    code: `import requests
import concurrent.futures
from typing import List, Dict

API_URL = "http://localhost:8000/api/query"

def batch_query(questions: List[str], max_workers: int = 5) -> List[Dict]:
    """Process multiple queries in parallel"""

    def query_single(question: str) -> Dict:
        payload = {
            "question": question,
            "mode": "adaptive",
            "use_context": True,
            "rerank_preset": "quality"
        }
        response = requests.post(API_URL, json=payload)
        return response.json()

    # Use ThreadPoolExecutor for parallel requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=max_workers) as executor:
        results = list(executor.map(query_single, questions))

    return results

# Example usage
questions = [
    "What are the core values?",
    "How do leaders inspire teams?",
    "What is servant leadership?",
    "Define transformational leadership",
    "How to build trust?"
]

results = batch_query(questions)

# Print summary
for question, result in zip(questions, results):
    print(f"Q: {question}")
    print(f"A: {result['answer'][:100]}...")
    print(f"Time: {result['metadata']['processing_time_ms']}ms")
    print(f"Confidence: {result['metadata']['confidence']:.2f}")
    print("-" * 80)`,
    response: `Q: What are the core values?
A: The Air Force core values are integrity first, service before self, and excellence in all we do...
Time: 1523 ms
Confidence: 0.92
--------------------------------------------------------------------------------
Q: How do leaders inspire teams?
A: Leaders inspire teams through clear communication, leading by example, and recognizing achievem...
Time: 1689 ms
Confidence: 0.88
--------------------------------------------------------------------------------
Q: What is servant leadership?
A: Servant leadership is a philosophy where the leader prioritizes the needs of the team and helps...
Time: 1734 ms
Confidence: 0.85
--------------------------------------------------------------------------------
Q: Define transformational leadership
A: Transformational leadership is a style that focuses on inspiring and motivating followers to ac...
Time: 1812 ms
Confidence: 0.87
--------------------------------------------------------------------------------
Q: How to build trust?
A: Building trust requires consistency, transparency, competence, and genuine care for team member...
Time: 1598 ms
Confidence: 0.90
--------------------------------------------------------------------------------`,
    tags: ['python', 'batch', 'advanced']
  }
];

export default function CodePlayground({ className = '' }: CodePlaygroundProps) {
  const [activeFramework, setActiveFramework] = useState<Framework>('python');
  const [activeExample, setActiveExample] = useState(examples[0]);
  const [copiedCode, setCopiedCode] = useState(false);

  const filteredExamples = examples.filter(e => e.framework === activeFramework);

  const copyCode = async () => {
    await navigator.clipboard.writeText(activeExample.code);
    setCopiedCode(true);
    setTimeout(() => setCopiedCode(false), 2000);
  };

  return (
    <div className={`bg-gradient-to-br from-slate-900 to-slate-800 rounded-2xl p-8 border border-slate-700 ${className}`}>
      {/* Header */}
      <div className="mb-6">
        <div className="flex items-center gap-3 mb-3">
          <div className="p-3 bg-gradient-to-br from-indigo-500 to-purple-500 rounded-xl">
            <Code className="w-6 h-6 text-white" />
          </div>
          <div>
            <h2 className="text-2xl font-bold text-white">Live Code Playground</h2>
            <p className="text-slate-400">Pre-configured Apollo examples across frameworks</p>
          </div>
        </div>
      </div>

      {/* Framework Selector */}
      <div className="flex gap-2 mb-6">
        {(['python', 'nodejs', 'curl'] as Framework[]).map((framework) => (
          <button
            key={framework}
            onClick={() => {
              setActiveFramework(framework);
              setActiveExample(examples.find(e => e.framework === framework) || examples[0]);
            }}
            className={`px-4 py-2 rounded-lg font-semibold transition-all ${
              activeFramework === framework
                ? 'bg-gradient-to-r from-indigo-600 to-purple-600 text-white'
                : 'bg-slate-700 text-slate-300 hover:bg-slate-600'
            }`}
          >
            {framework === 'nodejs' ? 'Node.js' : framework.toUpperCase()}
          </button>
        ))}
      </div>

      {/* Example Selector */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-3 mb-6">
        {filteredExamples.map((example) => (
          <button
            key={example.id}
            onClick={() => setActiveExample(example)}
            className={`text-left p-4 rounded-lg border transition-all ${
              activeExample.id === example.id
                ? 'bg-indigo-500/10 border-indigo-500/50'
                : 'bg-slate-800/50 border-slate-700 hover:border-slate-600'
            }`}
          >
            <h4 className="font-semibold text-white text-sm mb-1">{example.name}</h4>
            <p className="text-xs text-slate-400 line-clamp-2">{example.description}</p>
            <div className="flex gap-1 mt-2">
              {example.tags.slice(0, 2).map((tag) => (
                <span
                  key={tag}
                  className="text-xs px-2 py-0.5 bg-slate-700 text-slate-300 rounded"
                >
                  {tag}
                </span>
              ))}
            </div>
          </button>
        ))}
      </div>

      {/* Code Editor */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Editor */}
        <div className="bg-slate-800/50 rounded-xl border border-slate-700 overflow-hidden">
          <div className="flex items-center justify-between px-4 py-3 bg-slate-900/50 border-b border-slate-700">
            <div className="flex items-center gap-2">
              <Terminal className="w-4 h-4 text-slate-400" />
              <span className="text-sm font-medium text-slate-300">{activeExample.name}</span>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={copyCode}
                className="p-2 hover:bg-slate-700 rounded-lg transition-colors"
                title="Copy code"
              >
                {copiedCode ? (
                  <Check className="w-4 h-4 text-green-400" />
                ) : (
                  <Copy className="w-4 h-4 text-slate-400" />
                )}
              </button>
              <a
                href="http://localhost:8000/docs"
                target="_blank"
                rel="noopener noreferrer"
                className="p-2 hover:bg-slate-700 rounded-lg transition-colors"
                title="Open API docs"
              >
                <ExternalLink className="w-4 h-4 text-slate-400" />
              </a>
            </div>
          </div>
          <div className="p-4 overflow-x-auto">
            <pre className="text-sm font-mono text-slate-300">
              <code>{activeExample.code}</code>
            </pre>
          </div>
        </div>

        {/* Output */}
        <div className="bg-slate-800/50 rounded-xl border border-slate-700 overflow-hidden">
          <div className="px-4 py-3 bg-slate-900/50 border-b border-slate-700">
            <div className="flex items-center gap-2">
              <div className="w-3 h-3 rounded-full bg-green-400 animate-pulse" />
              <span className="text-sm font-medium text-slate-300">Output</span>
            </div>
          </div>
          <div className="p-4 overflow-x-auto">
            <pre className="text-sm font-mono text-green-400">
              <code>{activeExample.response}</code>
            </pre>
          </div>
        </div>
      </div>

      {/* API Reference Link */}
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="mt-6 bg-blue-500/10 rounded-xl p-4 border border-blue-500/30"
      >
        <div className="flex items-start gap-3">
          <Code className="w-5 h-5 text-blue-400 flex-shrink-0 mt-0.5" />
          <div>
            <h4 className="font-semibold text-white mb-1">Want to run this locally?</h4>
            <p className="text-sm text-slate-300 mb-2">
              Start the Apollo backend with GPU acceleration and run these examples yourself.
            </p>
            <a
              href="http://localhost:8000/docs"
              target="_blank"
              rel="noopener noreferrer"
              className="inline-flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-500 rounded-lg text-white text-sm font-medium transition-colors"
            >
              View API Documentation
              <ExternalLink className="w-4 h-4" />
            </a>
          </div>
        </div>
      </motion.div>
    </div>
  );
}
