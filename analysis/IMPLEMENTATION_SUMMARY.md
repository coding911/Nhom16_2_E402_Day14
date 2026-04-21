# Benchmarking Implementation Summary

## Overview

You now have a complete benchmarking and evaluation framework for your Student Agent using **Langfuse** (tracing) and **RAGAS** (evaluation).

## Files Created/Modified

### New Files ✨

1. **`run2.py`** (18.9 KB)
   - Main benchmarking runner
   - Executes 7 benchmark queries
   - Integrates Langfuse for tracing
   - Runs RAGAS evaluation
   - Saves results to JSON
   - ~530 lines of code

2. **`BENCHMARKING.md`** (10.7 KB)
   - Comprehensive documentation
   - Setup instructions for Langfuse
   - Metrics explanation
   - Troubleshooting guide
   - Example output and result format

3. **`SETUP_BENCHMARKING.md`** (4.3 KB)
   - Quick start guide
   - Installation steps
   - File structure overview
   - Next steps checklist

### Modified Files ✏️

4. **`requirements.txt`**
   - Added `langfuse==2.36.1`
   - Added `ragas==0.1.16`
   - Added `datasets==2.19.1`

### Unchanged Files ✅

5. **`run.py`** — No changes, still works as before

## What run2.py Does

### 1. Tracing with Langfuse
```python
@observe(name="run_agent_with_tracing")
def run_agent_with_tracing(query: str, langfuse_client: Langfuse):
    # Traces every agent execution step
    # Captures query, output, latency, errors
    # Sends to Langfuse cloud (optional)
```

**Features:**
- Records query input
- Logs agent reasoning steps
- Captures final answer
- Measures execution latency
- Traces error events
- Generates trace IDs

### 2. Quality Assessment
Each query is evaluated on:
- **Answer completeness** — Is response empty?
- **Error detection** — Error type classification
- **Performance** — Is latency within threshold?
- **Hallucination detection** — Contradictory statements
- **Data retrieval** — Number of relevant docs found
- **Combined quality score** — 0-1 rating

### 3. RAGAS Evaluation
Four LLM-based metrics:
- **Answer Relevancy** — Query-answer alignment
- **Faithfulness** — Answer grounding in context
- **Context Recall** — All relevant docs retrieved
- **Context Precision** — Only relevant docs retrieved

### 4. Benchmarking Queries
7 test queries covering:
- Student performance evaluation
- Score comparison
- Attendance filtering
- Detailed student info
- Ranking queries
- Full list queries
- Out-of-domain queries

### 5. Results Export
- JSON file with per-query metrics
- Aggregate statistics
- Quality assessments
- Trace IDs for Langfuse lookup

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. (Optional) Start Langfuse locally
docker run --name langfuse -e NODE_ENV=production -p 3000:3000 langfuse/langfuse:latest

# 3. Run benchmarks
python run2.py

# 4. View results
cat evaluation/benchmark_YYYY-MM-DD.json
```

## Output Example

```
════════════════════════════════════════════════════════════════════════════════
  🎓 STUDENT AGENT — BENCHMARKING & EVALUATION SUITE
════════════════════════════════════════════════════════════════════════════════

🔄 Running 7 benchmark queries with tracing...

[ 1/ 7] Đánh giá học lực của học sinh Lê Minh Cường              ✅ (2.45s, score: 0.89)
[ 2/ 7] So sánh điểm số của Hoàng Văn Em và Nguyễn Thị Linh      ✅ (1.82s, score: 0.85)
[ 3/ 7] Học sinh nào có điểm chuyên cần dưới 0.8?               ✅ (1.53s, score: 0.91)
[ 4/ 7] Thông tin chi tiết về học sinh HS035                    ✅ (1.21s, score: 0.88)
[ 5/ 7] Học sinh nào đạt điểm toán cao nhất?                    ⚠️  (3.12s, score: 0.72)
[ 6/ 7] Danh sách tất cả học sinh                                ✅ (2.05s, score: 0.83)
[ 7/ 7] Sáng nay có mưa không?                                   ⚠️  (0.89s, score: 0.45)

📊 AGGREGATE METRICS
────────────────────────────────────────────────────────────────
  Total Queries        : 7
  Avg Latency          : 1.906s
  Avg Quality Score    : 0.791
  Queries with Errors  : 0/7
  Hallucination Risk   : 1/7
────────────────────────────────────────────────────────────────

📈 RAGAS EVALUATION SCORES
────────────────────────────────────────────────────────────────
  answer_relevancy       : 0.857
  faithfulness           : 0.823
  context_recall         : 0.891
  context_precision      : 0.756
────────────────────────────────────────────────────────────────

💾 Results saved to: evaluation/benchmark_2024-12-XX.json
════════════════════════════════════════════════════════════════════════════════
```

## Results File Format

`evaluation/benchmark_YYYY-MM-DD.json`:

```json
[
  {
    "timestamp": "2024-12-XX...",
    "query": "Đánh giá học lực của học sinh Lê Minh Cường",
    "query_type": "evaluation",
    "final_answer": "...",
    "latency_seconds": 2.450,
    "trace_id": "trace_xyz123",
    "error": "",
    "quality_assessment": {
      "has_error": false,
      "error_type": "none",
      "answer_length": 1247,
      "answer_empty": false,
      "latency_high": false,
      "retrieved_data": 3,
      "hallucination_risk": 0.0,
      "quality_score": 0.89
    },
    "metrics": {
      "retrieved_students": 3,
      "trace_steps": 4
    }
  }
]
```

## Integration Points

### With Langfuse
```python
from langfuse.decorators import observe, langfuse_context

@observe(name="run_agent_with_tracing")
def run_agent_with_tracing(query, langfuse_client):
    trace = langfuse_context.get_current_trace()
    # Trace is automatically sent to Langfuse
```

### With RAGAS
```python
from ragas import evaluate
from ragas.metrics import answer_relevancy, faithfulness

results = ragas_evaluate(
    dataset=dataset,
    metrics=[answer_relevancy, faithfulness, ...],
)
```

### With Agent Graph
```python
from graph.pipeline import get_graph
from graph.state import AgentState

graph = get_graph()
result = graph.invoke(initial_state)
```

## Customization

### Add Custom Benchmarks
Edit `BENCHMARK_QUERIES` in `run2.py`:

```python
BENCHMARK_QUERIES = [
    {
        "query": "Your question here",
        "expected_context": "what to expect",
        "expected_answer_type": "evaluation|comparison|list|details|ranking",
    },
]
```

### Adjust Quality Thresholds
Modify `assess_quality()` function:

```python
def assess_quality(result):
    # Adjust scoring weights
    quality = 1.0
    if assessment["latency_high"]:
        quality -= 0.2  # Change penalty weight
```

### Configure Langfuse
Set in `.env`:

```
LANGFUSE_PUBLIC_KEY=pk_your_key
LANGFUSE_SECRET_KEY=sk_your_key
LANGFUSE_HOST=https://cloud.langfuse.com
```

## Metrics Explained

### Quality Score (0-1)
- **1.0** = Perfect (fast, complete, accurate)
- **0.7** = Good (minor issues)
- **0.5** = Fair (multiple issues)
- **<0.5** = Poor (errors, hallucination, empty response)

### Error Types
- **parsing** — JSON or data parse error
- **timeout** — Query exceeded time limit
- **not_found** — Requested data not available
- **other** — Other errors

### Hallucination Risk (0-1)
- Detects contradictory statements
- Flags "I don't know" in non-error contexts
- Higher = more risk of fabricated content

## Workflow

```
run2.py
│
├─ setup_env()
│  └─ Load .env and verify GROQ_API_KEY
│
├─ init_langfuse()
│  └─ Connect to Langfuse (optional)
│
├─ run_benchmark_suite()
│  │
│  ├─ For each benchmark query:
│  │  ├─ run_agent_with_tracing()
│  │  │  ├─ Execute agent graph
│  │  │  ├─ Measure latency
│  │  │  └─ Send trace to Langfuse
│  │  │
│  │  └─ assess_quality()
│  │     ├─ Check for errors
│  │     ├─ Detect hallucination
│  │     └─ Calculate quality score
│  │
│  ├─ print_results_table()
│  │
│  ├─ print_aggregate_metrics()
│  │
│  ├─ prepare_ragas_dataset()
│  │  └─ Format results for RAGAS
│  │
│  ├─ evaluate_with_ragas()
│  │  └─ Run RAGAS metrics
│  │
│  ├─ print_ragas_results()
│  │
│  └─ save_results()
│     └─ Write to evaluation/benchmark_*.json
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| RAGAS fails | Ensure GROQ_API_KEY set, or disable RAGAS |
| Langfuse connection error | Script falls back to local tracing |
| Low quality scores | Check evaluation JSON for error details |
| Missing .env | Run `python run.py` first to generate it |
| Import errors | Run `pip install -r requirements.txt` |

## Next Steps

1. ✅ Install dependencies: `pip install -r requirements.txt`
2. ✅ Run first benchmark: `python run2.py`
3. ✅ Review results in `evaluation/benchmark_*.json`
4. ✅ Set up Langfuse for cloud tracing (optional)
5. ✅ Customize benchmark queries for your use cases
6. ✅ Integrate into CI/CD pipeline
7. ✅ Set quality gates and alerts

## Support

- **Full docs**: See `BENCHMARKING.md`
- **Quick start**: See `SETUP_BENCHMARKING.md`
- **Results analysis**: Check `evaluation/benchmark_*.json`

---

**Status**: ✅ Complete and ready to use

**Files**: 
- `run2.py` ✨ (NEW)
- `BENCHMARKING.md` 📖 (NEW)
- `SETUP_BENCHMARKING.md` 📖 (NEW)
- `requirements.txt` ✏️ (UPDATED)
- `run.py` ✅ (UNCHANGED)
