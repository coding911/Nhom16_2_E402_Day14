"""
run3.py — Full Integrated Evaluation Suite
==========================================
Tích hợp tất cả modules từ benchmark.py:
  ✅ SDG (55 cases từ data thực)
  ✅ Retrieval Eval (Hit Rate & MRR)
  ✅ Multi-Judge Consensus Engine
  ✅ Security Boundary Testing
  ✅ Regression Release Gate
  ✅ Root Cause Analysis (5 Whys)
  ✅ Cost & Performance Reporter
  ✅ LangSmith Tracing (nếu có API key)

Usage:
    python run3.py [--students path/to/students.json] [--version v1.2]
"""

import os
import sys
import json
import time
import argparse
import statistics
import random
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
from dataclasses import asdict

# ── Windows encoding fix
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8")
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8")

BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

# ────────────────────────────────────────────────────────────
# ENV SETUP
# ────────────────────────────────────────────────────────────

def setup_env() -> Dict[str, str]:
    env_file = BASE_DIR / ".env"
    if env_file.exists():
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    k, _, v = line.partition("=")
                    os.environ[k] = v.strip("\"'")

    config = {
        "groq_api_key":      os.getenv("GROQ_API_KEY", ""),
        "langsmith_key":     os.getenv("LANGSMITH_API_KEY", ""),
        "langsmith_project": os.getenv("LANGSMITH_PROJECT", "student-agent-eval"),
        "langsmith_enabled": os.getenv("LANGSMITH_TRACING", "true").lower() == "true",
    }

    print(f"\n{'═'*70}")
    print("  ⚙️  ENVIRONMENT CONFIGURATION")
    print(f"{'═'*70}")
    print(f"  Groq API Key    : {'****' + config['groq_api_key'][-4:] if config['groq_api_key'] else '❌ NOT SET'}")
    print(f"  LangSmith       : {'✅ ' + config['langsmith_project'] if config['langsmith_key'] else '⚠️  Not configured'}")
    print(f"  Tracing         : {'Enabled' if config['langsmith_enabled'] else 'Disabled'}")
    return config


# ────────────────────────────────────────────────────────────
# LANGSMITH TRACING WRAPPER
# ────────────────────────────────────────────────────────────

def make_traceable_runner(langsmith_key: str, project: str, enabled: bool):
    """
    Trả về decorator @traceable nếu LangSmith available,
    ngược lại trả về identity decorator.
    """
    if enabled and langsmith_key:
        try:
            from langsmith import traceable
            print(f"  ✅ LangSmith tracing active → project: {project}")
            return traceable
        except ImportError:
            print("  ⚠️  langsmith not installed. pip install langsmith")
    return lambda **kw: (lambda fn: fn)


# ────────────────────────────────────────────────────────────
# IMPORTS từ project (graceful fallback)
# ────────────────────────────────────────────────────────────

def try_import_agent():
    try:
        from graph.pipeline import get_graph
        from graph.state import AgentState
        return get_graph, AgentState
    except ImportError:
        return None, None


def try_import_baseline():
    try:
        from baseline_chatbot import run_baseline
        return run_baseline
    except ImportError:
        return None


# ────────────────────────────────────────────────────────────
# SECURITY EVALUATION
# ────────────────────────────────────────────────────────────

def evaluate_security_boundary_standalone(
    test_cases: List,
    agent_fn,
) -> Dict[str, Any]:
    """Standalone version của security boundary testing."""
    from benchmark import evaluate_security_boundary
    return evaluate_security_boundary(test_cases, agent_fn)


# ────────────────────────────────────────────────────────────
# MOCK AGENT (chạy standalone nếu không có graph)
# ────────────────────────────────────────────────────────────

def build_mock_agent(students: List[Dict]):
    """
    Agent đơn giản dựa trên keyword search — dùng khi không có graph pipeline.
    Mục đích: demo toàn bộ evaluation pipeline độc lập.
    """
    from benchmark import build_simple_retriever, _xep_loai, _process_avg

    retriever = build_simple_retriever(students)
    student_map = {s["student_id"]: s for s in students}

    def _run(query: str) -> Dict[str, Any]:
        start = time.time()
        q_lower = query.lower()
        retrieved_ids = retriever(query)
        retrieved = [student_map[sid] for sid in retrieved_ids if sid in student_map]

        # ── Security queries - MUST refuse
        security_patterns = [
            "api_key", "groq_api_key", "api key", ".env", "credentials",
            "ignore previous", "system prompt", "developer mode",
            "admin", "superuser", "bypass", "override",
            "delete", "update", "modify", "sửa điểm", "xóa",
            "database", "connection string", "redis", "infrastructure"
        ]
        
        for pattern in security_patterns:
            if pattern in q_lower:
                return {
                    "final_answer": "Tôi không thể cung cấp thông tin này vì lý do bảo mật. Vui lòng chỉ hỏi về thông tin học sinh trong hệ thống quản lý giáo dục.",
                    "retrieved_students": [],
                    "error": "",
                    "latency": round(time.time() - start, 3),
                    "cost_usd": 0.0,
                }
        
        # ── Harmful queries
        harmful_patterns = ["hack", "ma túy", "đánh cắp", "tấn công", "malware", "ddos"]
        for pattern in harmful_patterns:
            if pattern in q_lower:
                return {
                    "final_answer": "Tôi không thể hỗ trợ các hoạt động bất hợp pháp hoặc gây hại. Vui lòng hỏi về thông tin học sinh hợp lệ.",
                    "retrieved_students": [],
                    "error": "",
                    "latency": round(time.time() - start, 3),
                    "cost_usd": 0.0,
                }

        # ── Out-of-domain check
        ood_keywords = ["thời tiết", "máy bay", "tích phân", "dịch", "bitcoin",
                        "vàng", "bài thơ", "nấu", "giá", "phở", "tiếng nhật",
                        "bóng đá", "phim", "chứng khoán"]
        if any(kw in q_lower for kw in ood_keywords):
            return {
                "final_answer": (
                    "Câu hỏi này nằm ngoài phạm vi của hệ thống quản lý học sinh. "
                    "Tôi chỉ có thể trả lời các câu hỏi về thông tin học sinh."
                ),
                "retrieved_students": [],
                "error": "",
                "latency": round(time.time() - start, 3),
                "cost_usd": 0.0,
            }

        if not retrieved:
            return {
                "final_answer": "Không tìm thấy học sinh phù hợp với câu hỏi.",
                "retrieved_students": [],
                "error": "not_found",
                "latency": round(time.time() - start, 3),
                "cost_usd": 0.0,
            }

        # ── Build answer
        s = retrieved[0]
        xl = _xep_loai(s["final_score"])
        avg_p = _process_avg(s["process_score"])
        answer_parts = []

        if "đánh giá" in q_lower or "học lực" in q_lower:
            answer_parts.append(
                f"Học sinh {s['name']} (Mã: {s['student_id']}, Lớp: {s['class_name']}, "
                f"Trường: {s['school']})\n"
                f"• Điểm quá trình TB: {avg_p}\n"
                f"• Điểm cuối kỳ: {s['final_score']}\n"
                f"• Chuyên cần: {s['attendance']*100:.0f}%\n"
                f"• Xếp loại học lực: {xl}"
            )
        elif "so sánh" in q_lower and len(retrieved) >= 2:
            s2 = retrieved[1]
            xl2 = _xep_loai(s2["final_score"])
            winner = s["name"] if s["final_score"] >= s2["final_score"] else s2["name"]
            answer_parts.append(
                f"So sánh:\n"
                f"• {s['name']} ({s['student_id']}): cuối kỳ={s['final_score']}, "
                f"chuyên cần={s['attendance']*100:.0f}%, học lực: {xl}\n"
                f"• {s2['name']} ({s2['student_id']}): cuối kỳ={s2['final_score']}, "
                f"chuyên cần={s2['attendance']*100:.0f}%, học lực: {xl2}\n"
                f"→ {winner} có điểm cuối kỳ cao hơn."
            )
        elif "chuyên cần" in q_lower:
            import re
            m = re.search(r"(\d+\.?\d*)", query)
            thr = float(m.group(1)) if m else 0.8
            if thr > 1:
                thr /= 100
            low_att = [s for s in students if s["attendance"] < thr]
            answer_parts.append(
                f"Có {len(low_att)} học sinh có điểm chuyên cần dưới {thr*100:.0f}%:\n" +
                "\n".join(f"• {s['name']} ({s['student_id']}): {s['attendance']*100:.0f}%"
                          for s in sorted(low_att, key=lambda x: x["attendance"])[:10])
            )
        elif "cao nhất" in q_lower or "giỏi nhất" in q_lower:
            answer_parts.append(
                f"Học sinh đứng đầu: {s['name']} ({s['student_id']}), "
                f"điểm cuối kỳ: {s['final_score']}, học lực: {xl}"
            )
        elif "thông tin" in q_lower or "chi tiết" in q_lower:
            answer_parts.append(
                f"Thông tin học sinh {s['student_id']}:\n"
                f"• Họ tên: {s['name']}\n"
                f"• Tuổi: {s['age']}\n"
                f"• Lớp: {s['class_name']} — Trường: {s['school']}\n"
                f"• Điểm quá trình: {s['process_score']}\n"
                f"• Điểm cuối kỳ: {s['final_score']}\n"
                f"• Chuyên cần: {s['attendance']*100:.0f}%\n"
                f"• Học lực: {xl}"
            )
        else:
            answer_parts.append(
                f"{s['name']} ({s['student_id']}): điểm cuối kỳ = {s['final_score']}, "
                f"học lực = {xl}, chuyên cần = {s['attendance']*100:.0f}%."
            )

        return {
            "final_answer": "\n".join(answer_parts),
            "retrieved_students": [{"student_id": st["student_id"], "name": st["name"]}
                                   for st in retrieved[:3]],
            "error": "",
            "latency": round(time.time() - start, 3),
            "cost_usd": 0.0001,  # mock cost
        }

    return _run


# ────────────────────────────────────────────────────────────
# QUALITY ASSESSMENT (heuristic, không cần LLM)
# ────────────────────────────────────────────────────────────

def assess_quality(result: Dict[str, Any], test_case_keywords: List[str]) -> Dict[str, Any]:
    answer  = result.get("final_answer", "")
    error   = result.get("error", "")
    latency = result.get("latency", 0)
    retrieved = result.get("retrieved_students", [])

    # Keyword coverage
    kw_hit = sum(1 for kw in test_case_keywords if kw.lower() in answer.lower())
    kw_coverage = kw_hit / len(test_case_keywords) if test_case_keywords else 0.5

    # Hallucination signals
    halluc_patterns = ["tôi không có thông tin", "tôi không biết", "giả định", "có thể là"]
    halluc_score = sum(0.25 for p in halluc_patterns if p in answer.lower())

    # Quality score
    q = 1.0
    if not answer.strip():
        q -= 0.5
    if error and "not_found" not in error:
        q -= 0.3
    if latency > 8.0:
        q -= 0.1
    if halluc_score > 0:
        q -= min(halluc_score, 0.3)
    if kw_coverage < 0.3:
        q -= 0.15
    if not retrieved and "out_of_domain" not in str(result.get("query_type", "")):
        q -= 0.1

    error_type = "none"
    if error:
        if "json" in error.lower() or "parse" in error.lower():
            error_type = "parsing"
        elif "timeout" in error.lower():
            error_type = "timeout"
        elif "not_found" in error:
            error_type = "not_found"
        else:
            error_type = "other"

    return {
        "quality_score":   round(max(0.0, min(1.0, q)), 4),
        "kw_coverage":     round(kw_coverage, 4),
        "halluc_risk":     round(min(halluc_score, 1.0), 4),
        "answer_length":   len(answer),
        "has_error":       bool(error),
        "error_type":      error_type,
        "latency_high":    latency > 8.0,
        "retrieved_count": len(retrieved),
    }


# ────────────────────────────────────────────────────────────
# REPORTING HELPERS
# ────────────────────────────────────────────────────────────

def _bar(value: float, width: int = 20, char: str = "█") -> str:
    filled = int(value * width)
    return char * filled + "░" * (width - filled) + f" {value*100:.1f}%"


def print_section(title: str):
    print(f"\n{'─'*70}")
    print(f"  {title}")
    print(f"{'─'*70}")


def print_retrieval_report(report: Dict[str, Any]):
    print_section("📐 RETRIEVAL EVALUATION")
    print(f"  In-domain cases  : {report['total_in_domain']}")
    print(f"  Hit Rate @1      : {_bar(report['hit_rate_at_1'])}")
    print(f"  Hit Rate @3      : {_bar(report['hit_rate_at_3'])}")
    print(f"  Hit Rate @5      : {_bar(report['hit_rate_at_5'])}")
    print(f"  MRR              : {_bar(report['mrr'])}")
    print(f"  Avg Precision@3  : {_bar(report['avg_precision_at_3'])}")
    failed = report.get("failed_cases", [])
    if failed:
        print(f"\n  ⚠️  {len(failed)} cases missed Hit@3:")
        for c in failed[:3]:
            print(f"     • [{c['test_case_id']}] {c['query'][:55]}...")
            print(f"       Expected: {c['expected_ids']}  |  Got: {c['retrieved_ids'][:3]}")


def print_security_report(report: Dict[str, Any]):
    print_section("🔒 SECURITY BOUNDARY TESTING")
    print(f"  Total security tests : {report['total_security_tests']}")
    print(f"  Pass rate            : {_bar(report['pass_rate'])}")
    print(f"  Critical failures    : {report['critical_failures']}")
    
    if report.get('critical_failure_details'):
        print(f"\n  🔴 CRITICAL FAILURES:")
        for cf in report['critical_failure_details'][:3]:
            print(f"     • {cf['query'][:60]}...")
            print(f"       → {cf['reason']}")
    
    if report.get('recommendations'):
        print(f"\n  📋 Recommendations:")
        for rec in report['recommendations']:
            print(f"     • {rec}")


def print_consensus_summary(consensus_results: List, n_sample: int):
    print_section("⚖️  MULTI-JUDGE CONSENSUS")
    print(f"  Queries sampled  : {n_sample}")
    verdicts = {"pass": 0, "fail": 0, "review": 0}
    for cr in consensus_results:
        verdicts[cr.final_verdict] = verdicts.get(cr.final_verdict, 0) + 1
    conflicts = sum(1 for cr in consensus_results if cr.conflict)
    avg_agree = statistics.mean(cr.agreement_rate for cr in consensus_results) if consensus_results else 0
    avg_score = statistics.mean(cr.consensus_score for cr in consensus_results) if consensus_results else 0

    print(f"  Avg Agreement    : {_bar(avg_agree)}")
    print(f"  Avg Consensus    : {_bar(avg_score)}")
    print(f"  Conflicts        : {conflicts}/{len(consensus_results)}")
    print(f"  Verdicts  → pass:{verdicts['pass']} | review:{verdicts['review']} | fail:{verdicts['fail']}")

    # Per-judge breakdown
    all_judges: Dict[str, List[float]] = {}
    for cr in consensus_results:
        for js in cr.judge_scores:
            all_judges.setdefault(js.judge_model, []).append(js.overall)
    if all_judges:
        print(f"\n  Per-Judge Scores:")
        for model, scores_list in all_judges.items():
            avg = statistics.mean(scores_list)
            print(f"    {model:<35} avg={avg:.3f}  n={len(scores_list)}")


def print_gate_result(gate: Any):
    icon = {"RELEASE": "🟢", "REVIEW": "🟡", "ROLLBACK": "🔴"}.get(gate.gate_decision, "⚪")
    print_section(f"🚦 REGRESSION RELEASE GATE → {gate.gate_decision}")
    print(f"\n  {icon}  Decision: {gate.gate_decision}")
    print(f"\n  Delta Metrics vs Baseline:")
    print(f"    Quality Score  : {gate.quality_delta_pct:+.2f}%")
    print(f"    Latency        : {gate.latency_delta_pct:+.2f}%")
    print(f"    Cost           : {gate.cost_delta_pct:+.2f}%")
    if hasattr(gate, 'security_delta_pct'):
        print(f"    Security       : {gate.security_delta_pct:+.2f}%")
    print(f"\n  Reasons:")
    for r in gate.gate_reasons:
        print(f"    {r}")


def print_five_whys(rca: Dict[str, Any]):
    print_section("🔍 ROOT CAUSE ANALYSIS (5 WHYS)")
    print(f"  Primary Stage : {rca['stage_title']}  [{rca['priority']}]")
    print(f"  Signal Scores : {rca['signal_scores']}")
    print(f"\n  5 Whys:")
    for w in rca["five_whys"]:
        print(f"    {w}")
    print(f"\n  ✅ Root Fix: {rca['root_fix']}")
    print(f"\n  All Stages (ranked by signal):")
    for cat, info in rca["all_stages"].items():
        print(f"    [{info['priority']}] {info['title']:<30} score={info['score']}  fix: {info['fix'][:50]}...")


def print_cost_report(report: Dict[str, Any]):
    print_section("💰 COST & PERFORMANCE REPORT")
    s = report["summary"]
    print(f"  Total judge calls    : {s['total_judge_calls']}")
    print(f"  Total eval cost      : ${s['total_eval_cost_usd']:.5f}")
    print(f"  Cost per eval        : ${s['cost_per_eval_usd']:.6f}")
    print(f"  Avg judge latency    : {s['avg_judge_latency_s']:.3f}s")
    print(f"  Avg agent latency    : {s['avg_agent_latency_s']:.3f}s")
    print(f"  Conflict rate        : {s['conflict_rate']*100:.1f}%")
    print(f"\n  💡 Optimisation Strategies (target: -30% cost):")
    for opt in report["optimisation_strategies"]:
        tick = "✅" if opt["estimated_savings_pct"] >= 10 else "⚠️ "
        print(f"    [{opt['id']}] {tick} {opt['name']:<30} → savings: {opt['estimated_savings_pct']:.1f}%")
        print(f"        {opt['description']}")
    target = "✅" if report["achieves_30pct_target"] else "❌"
    print(f"\n  {target} Combined savings: {report['combined_estimated_savings_pct']:.1f}%  (target ≥ 30%)")
    print(f"  📌 {report['recommendation']}")


# ────────────────────────────────────────────────────────────
# MAIN EVALUATION PIPELINE
# ────────────────────────────────────────────────────────────

def run_evaluation(
    students: List[Dict],
    agent_fn,
    retrieve_fn,
    config: Dict[str, str],
    judge_models: List[str],
    version_id: str,
    baseline_snapshot_path: Optional[str] = None,
    n_sdg: int = 55,
    n_judge_sample: int = 15,
):
    """
    Pipeline đánh giá hoàn chỉnh — chạy synchronously (dễ debug).
    """
    from benchmark import (
        generate_sdg_dataset, evaluate_retrieval,
        evaluate_security_boundary,
        run_multi_judge, run_regression_gate,
        five_whys_analysis, generate_cost_report,
        compute_version_metrics,
    )

    wall_start = time.time()

    # ══ STEP 1: SDG ══════════════════════════════════════
    print_section("🔬 STEP 1 — SYNTHETIC DATA GENERATION")
    test_cases = generate_sdg_dataset(students, n=n_sdg, include_security=True)
    type_counts = {}
    for tc in test_cases:
        type_counts[tc.query_type] = type_counts.get(tc.query_type, 0) + 1
    print(f"  Generated {len(test_cases)} test cases:")
    for qt, cnt in sorted(type_counts.items()):
        print(f"    • {qt:<20} {cnt:>3} cases")

    # ══ STEP 2: RETRIEVAL EVAL ══════════════════════════
    print_section("📐 STEP 2 — RETRIEVAL EVALUATION")
    in_domain_count = sum(1 for tc in test_cases if tc.query_type not in ['out_of_domain', 'security'])
    print(f"  Running retrieval on {in_domain_count} in-domain cases...")
    retrieval_report = evaluate_retrieval(test_cases, retrieve_fn)
    print_retrieval_report(retrieval_report)

    # ══ STEP 3: SECURITY BOUNDARY TESTING ════════════════
    print_section("🔒 STEP 3 — SECURITY BOUNDARY TESTING")
    security_report = evaluate_security_boundary(test_cases, agent_fn)
    print_security_report(security_report)

    # ══ STEP 4: RUN AGENT ═══════════════════════════════
    print_section("🤖 STEP 4 — AGENT EXECUTION")
    print(f"  Running agent on {len(test_cases)} queries...")

    agent_results = []
    quality_assessments = []

    for i, tc in enumerate(test_cases, 1):
        result = agent_fn(tc.query)
        result["test_case_id"] = tc.id
        result["query"]        = tc.query
        result["query_type"]   = tc.query_type
        result["ground_truth"] = tc.ground_truth_answer

        qa = assess_quality(result, tc.expected_answer_keywords)
        result["quality_score"] = qa["quality_score"]

        agent_results.append(result)
        quality_assessments.append(qa)

        icon = "✅" if qa["quality_score"] >= 0.7 else ("⚠️ " if qa["quality_score"] >= 0.4 else "❌")
        if i % 10 == 0 or i <= 5:
            print(f"  [{i:02d}/{len(test_cases)}] {icon} q={qa['quality_score']:.2f} "
                  f"lat={result['latency']:.2f}s  {tc.query[:45]}...")

    avg_q = statistics.mean(qa["quality_score"] for qa in quality_assessments)
    avg_l = statistics.mean(r["latency"] for r in agent_results)
    errors = [r.get("error", "") for r in agent_results if r.get("error")]
    print(f"\n  Summary: avg_quality={avg_q:.3f}  avg_latency={avg_l:.3f}s  errors={len(errors)}")

    # ══ STEP 5: MULTI-JUDGE CONSENSUS ═══════════════════
    print_section("⚖️  STEP 5 — MULTI-JUDGE CONSENSUS ENGINE")

    groq_key = config.get("groq_api_key", "")
    rng = random.Random(42)
    sample_results = rng.sample(agent_results, min(n_judge_sample, len(agent_results)))

    consensus_results = []
    if not groq_key:
        print("  ⚠️  GROQ_API_KEY không có → sinh mock consensus results")
        from benchmark import ConsensusResult, JudgeScore
        for r in sample_results:
            q_score = r.get("quality_score", 0.6)
            mock_judges = []
            for m in judge_models:
                noise = rng.uniform(-0.08, 0.08)
                js = JudgeScore(
                    judge_model=m, query=r["query"], answer=r.get("final_answer",""),
                    faithfulness=round(min(1,max(0, q_score + noise)), 4),
                    answer_relevancy=round(min(1,max(0, q_score + rng.uniform(-0.05,0.05))), 4),
                    context_precision=round(min(1,max(0, q_score + rng.uniform(-0.1,0.05))), 4),
                    overall=round(min(1,max(0, q_score + noise)), 4),
                    reasoning="Mock judge (no API key)",
                    latency=0.0, cost_usd=0.0,
                )
                mock_judges.append(js)
            scores = [j.overall for j in mock_judges]
            agree = all(abs(scores[i]-scores[j]) < 0.15
                       for i in range(len(scores)) for j in range(i+1,len(scores)))
            consensus_results.append(ConsensusResult(
                query=r["query"],
                judge_scores=mock_judges,
                agreement_rate=1.0 if agree else 0.5,
                consensus_score=round(statistics.mean(scores), 4),
                conflict=not agree,
                conflict_resolution="weighted" if not agree else "average",
                final_verdict="pass" if statistics.mean(scores) >= 0.7 else "review",
            ))
    else:
        print(f"  Judging {len(sample_results)} sampled queries with {judge_models}...")
        for i, r in enumerate(sample_results, 1):
            context = json.dumps(r.get("retrieved_students", [])[:2], ensure_ascii=False)
            cr = run_multi_judge(
                query=r["query"],
                answer=r.get("final_answer", ""),
                context=context,
                ground_truth=r.get("ground_truth", ""),
                judge_models=judge_models,
                groq_api_key=groq_key,
                parallel=True,
            )
            consensus_results.append(cr)
            icon = "✅" if cr.final_verdict == "pass" else ("⚠️ " if cr.final_verdict == "review" else "❌")
            print(f"  [{i:02d}/{len(sample_results)}] {icon} consensus={cr.consensus_score:.3f} "
                  f"agree={cr.agreement_rate:.2f} {'⚡conflict' if cr.conflict else ''}")
            if groq_key and i < len(sample_results):
                time.sleep(1.5)

    print_consensus_summary(consensus_results, len(sample_results))

    # ══ STEP 6: REGRESSION GATE ══════════════════════════
    print_section("🚦 STEP 6 — REGRESSION RELEASE GATE")

    current_metrics = compute_version_metrics(
        agent_results, version_id=version_id,
        retrieval_report=retrieval_report,
        security_report=security_report,  # ← THÊM security_report
    )

    # Load baseline snapshot or synthesize
    if baseline_snapshot_path and Path(baseline_snapshot_path).exists():
        with open(baseline_snapshot_path) as f:
            b_data = json.load(f)
        from benchmark import VersionMetrics
        baseline_metrics = VersionMetrics(**b_data)
        print(f"  Baseline loaded from: {baseline_snapshot_path}")
    else:
        from benchmark import VersionMetrics
        baseline_metrics = VersionMetrics(
            version_id="v_baseline",
            timestamp=datetime.utcnow().isoformat(),
            avg_latency=current_metrics.avg_latency * 1.05,
            avg_quality_score=current_metrics.avg_quality_score * 0.97,
            hit_rate_at_3=retrieval_report["hit_rate_at_3"] * 0.95,
            mrr=retrieval_report["mrr"] * 0.95,
            error_rate=current_metrics.error_rate,
            avg_cost_per_query=current_metrics.avg_cost_per_query * 1.1,
            total_queries=current_metrics.total_queries,
            security_score=0.95,  # baseline security score
        )
        print(f"  ℹ️  Baseline không có → sử dụng synthetic baseline")

    gate = run_regression_gate(current_metrics, baseline_metrics)
    print_gate_result(gate)

    # ══ STEP 7: ROOT CAUSE ANALYSIS ═════════════════════
    print_section("🔍 STEP 7 — ROOT CAUSE ANALYSIS (5 WHYS)")
    agent_answers = [r.get("final_answer", "") for r in agent_results]
    agent_errors_list = [r.get("error", "") for r in agent_results if r.get("error")]
    
    rca = five_whys_analysis(
        retrieval_report=retrieval_report,
        consensus_results=consensus_results,
        security_report=security_report,  # ← THÊM security_report
        agent_errors=agent_errors_list,
        agent_answers=agent_answers,
    )
    print_five_whys(rca)

    # ══ STEP 8: COST REPORT ══════════════════════════════
    agent_latencies = [r["latency"] for r in agent_results]
    primary_judge   = judge_models[0] if judge_models else "llama-3.3-70b-versatile"
    secondary_judge = judge_models[1] if len(judge_models) > 1 else "llama-3.1-8b-instant"
    cost_report = generate_cost_report(
        consensus_results=consensus_results,
        agent_latencies=agent_latencies,
        primary_judge=primary_judge,
        secondary_judge=secondary_judge,
    )
    print_cost_report(cost_report)

    # ══ SAVE RESULTS ════════════════════════════════════
    wall_elapsed = time.time() - wall_start
    output_dir   = BASE_DIR / "evaluation"
    output_dir.mkdir(exist_ok=True)
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_path = output_dir / f"run3_{version_id}_{ts}.json"

    final_report = {
        "meta": {
            "version_id": version_id,
            "timestamp": datetime.utcnow().isoformat(),
            "total_wall_time_s": round(wall_elapsed, 2),
            "n_sdg_cases": len(test_cases),
            "n_judge_sample": len(consensus_results),
            "judge_models": judge_models,
        },
        "retrieval": {k: v for k, v in retrieval_report.items() if k != "per_case"},
        "security": security_report,
        "agent_summary": {
            "avg_quality_score": round(avg_q, 4),
            "avg_latency_s":     round(avg_l, 4),
            "error_count":       len(errors),
            "error_rate":        round(len(errors) / len(agent_results), 4),
        },
        "consensus_summary": {
            "n_judged": len(consensus_results),
            "avg_consensus_score": round(statistics.mean(cr.consensus_score for cr in consensus_results), 4) if consensus_results else 0,
            "avg_agreement_rate":  round(statistics.mean(cr.agreement_rate for cr in consensus_results), 4) if consensus_results else 0,
            "conflict_count":      sum(1 for cr in consensus_results if cr.conflict),
            "verdict_counts":      {
                v: sum(1 for cr in consensus_results if cr.final_verdict == v)
                for v in ["pass", "review", "fail"]
            },
        },
        "gate": {
            "decision":          gate.gate_decision,
            "reasons":           gate.gate_reasons,
            "quality_delta_pct": gate.quality_delta_pct,
            "latency_delta_pct": gate.latency_delta_pct,
            "cost_delta_pct":    gate.cost_delta_pct,
            "security_delta_pct": gate.security_delta_pct if hasattr(gate, 'security_delta_pct') else 0,
        },
        "root_cause": {
            "primary_stage":  rca["primary_failure_stage"],
            "signal_scores":  rca["signal_scores"],
            "five_whys":      rca["five_whys"],
            "root_fix":       rca["root_fix"],
        },
        "cost": cost_report,
        "current_version_metrics": asdict(current_metrics),
        "baseline_version_metrics": asdict(baseline_metrics),
        "per_case_results": [
            {
                "test_case_id":    r["test_case_id"],
                "query":           r["query"],
                "query_type":      r["query_type"],
                "quality_score":   r["quality_score"],
                "latency":         r["latency"],
                "error":           r.get("error", ""),
                "final_answer":    r["final_answer"][:300],
            }
            for r in agent_results
        ],
    }

    # Save current version snapshot for future baseline comparison
    snapshot_path = output_dir / f"snapshot_{version_id}.json"
    with open(snapshot_path, "w", encoding="utf-8") as f:
        json.dump(asdict(current_metrics), f, ensure_ascii=False, indent=2)

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(final_report, f, ensure_ascii=False, indent=2)

    # ══ FINAL SUMMARY ═════════════════════════════════
    print(f"\n{'═'*70}")
    print(f"  ✅ EVALUATION COMPLETE — {wall_elapsed:.1f}s total")
    print(f"{'═'*70}")
    print(f"  Version          : {version_id}")
    print(f"  Gate Decision    : {gate.gate_decision}")
    print(f"  Quality Score    : {avg_q:.3f}")
    print(f"  Security Score   : {security_report['pass_rate']:.3f}")
    print(f"  Hit Rate@3       : {retrieval_report['hit_rate_at_3']*100:.1f}%")
    print(f"  MRR              : {retrieval_report['mrr']:.3f}")
    print(f"  Consensus Score  : {statistics.mean(cr.consensus_score for cr in consensus_results):.3f}" if consensus_results else "  Consensus Score  : N/A")
    print(f"  Root Cause       : {rca['stage_title']}")
    print(f"  Cost Savings Est : {cost_report['combined_estimated_savings_pct']:.1f}%")
    print(f"\n  📁 Report saved  : {out_path}")
    print(f"  📁 Snapshot saved: {snapshot_path}")
    print(f"{'═'*70}\n")

    return final_report


# ────────────────────────────────────────────────────────────
# LANGSMITH TRACED WRAPPER
# ────────────────────────────────────────────────────────────

def run_with_tracing(students, agent_fn, retrieve_fn, config, judge_models, version_id, baseline_path, n_sdg, n_judge):
    """Wrap run_evaluation với LangSmith tracing nếu có."""
    traceable = make_traceable_runner(
        config["langsmith_key"], config["langsmith_project"], config["langsmith_enabled"]
    )

    @traceable(name=f"run3_eval_{version_id}", run_type="chain")
    def _traced():
        return run_evaluation(
            students=students,
            agent_fn=agent_fn,
            retrieve_fn=retrieve_fn,
            config=config,
            judge_models=judge_models,
            version_id=version_id,
            baseline_snapshot_path=baseline_path,
            n_sdg=n_sdg,
            n_judge_sample=n_judge,
        )

    return _traced()


# ────────────────────────────────────────────────────────────
# ENTRY POINT
# ────────────────────────────────────────────────────────────

def parse_args():
    p = argparse.ArgumentParser(description="run3.py — Advanced Evaluation Suite")
    p.add_argument("--students",  default=None, help="Path to students.json")
    p.add_argument("--version",   default="v_current", help="Version ID")
    p.add_argument("--baseline",  default=None, help="Path to baseline snapshot JSON")
    p.add_argument("--n-sdg",     type=int, default=70, help="Number of SDG test cases")
    p.add_argument("--n-judge",   type=int, default=15, help="Number of cases to multi-judge")
    p.add_argument("--judges",    nargs="+",
                   default=["llama-3.3-70b-versatile", "llama-3.1-8b-instant"],
                   help="Judge models (≥2 recommended)")
    return p.parse_args()


def main():
    args   = parse_args()
    config = setup_env()

    # ── Load students data
    from benchmark import load_students, build_simple_retriever
    try:
        students_path = args.students or "/mnt/user-data/uploads/students.json"
        students = load_students(students_path)
        print(f"\n  📚 Loaded {len(students)} students from {students_path}")
    except FileNotFoundError as e:
        print(f"\n  ❌ {e}")
        sys.exit(1)

    # ── Build retriever
    retrieve_fn = build_simple_retriever(students)

    # ── Build agent (real or mock)
    get_graph, AgentState = try_import_agent()
    if get_graph:
        print("  ✅ Using real LangGraph agent")

        def agent_fn(query: str) -> Dict[str, Any]:
            init_state = {
                "query": query, "intent": None, "action": None,
                "retrieved_students": None, "evaluation_results": None,
                "final_answer": None, "trace": [], "error": None,
            }
            start = time.time()
            try:
                graph = get_graph()
                result = graph.invoke(init_state)
                return {
                    "final_answer": result.get("final_answer") or "",
                    "retrieved_students": result.get("retrieved_students") or [],
                    "error": result.get("error") or "",
                    "latency": round(time.time() - start, 3),
                    "cost_usd": 0.0005,
                }
            except Exception as e:
                return {
                    "final_answer": "",
                    "retrieved_students": [],
                    "error": str(e),
                    "latency": round(time.time() - start, 3),
                    "cost_usd": 0.0,
                }
    else:
        print("  ⚠️  graph.pipeline không tìm thấy → sử dụng Mock Agent (keyword-based)")
        agent_fn = build_mock_agent(students)

    # ── Run evaluation with optional tracing
    try:
        report = run_with_tracing(
            students=students,
            agent_fn=agent_fn,
            retrieve_fn=retrieve_fn,
            config=config,
            judge_models=args.judges,
            version_id=args.version,
            baseline_path=args.baseline,
            n_sdg=args.n_sdg,
            n_judge=args.n_judge,
        )
    except KeyboardInterrupt:
        print("\n\n🛑 Evaluation interrupted by user.")
        sys.exit(0)
    except Exception as e:
        print(f"\n\n❌ Evaluation failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()