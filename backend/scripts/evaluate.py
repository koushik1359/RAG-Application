"""
evaluate.py — RAGAS Evaluation Pipeline for the Enterprise RAG Engine.
Refactored for async RAGEngine.
"""

import os
import sys
import json
import time
import asyncio
from datetime import datetime

# Add the project root to path
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

from ragas import evaluate
from ragas.metrics import Faithfulness, ResponseRelevancy, ContextPrecision
from ragas.dataset_schema import SingleTurnSample, EvaluationDataset
from ragas.llms import LangchainLLMWrapper
from ragas.embeddings import LangchainEmbeddingsWrapper

# New Imports
from backend.src.core.rag_engine import RAGEngine

DEFAULT_TEST_QUESTIONS = [
    {
        "question": "What are the technical skills listed in the resume?",
        "ground_truth": "The resume lists various technical skills including programming languages and frameworks."
    },
    {
        "question": "What is the educational background mentioned in the document?",
        "ground_truth": "The document mentions the educational qualifications and degrees obtained."
    }
]

async def run_evaluation(test_questions=None):
    if test_questions is None:
        test_questions = DEFAULT_TEST_QUESTIONS
    
    print("=" * 70)
    print("  RAGAS EVALUATION PIPELINE (Async)")
    print("=" * 70)
    
    # Initialize Engine
    engine = RAGEngine()
    
    samples = []
    pipeline_results = []
    
    for i, tq in enumerate(test_questions):
        question = tq["question"]
        ground_truth = tq.get("ground_truth", "")
        
        print(f"  [{i+1}/{len(test_questions)}] Running: {question[:60]}...")
        
        t0 = time.time()
        result = await engine.run_pipeline(question, chat_history=[])
        elapsed = round(time.time() - t0, 2)
        
        contexts = [doc.page_content for doc in result["context"]]
        
        sample = SingleTurnSample(
            user_input=question,
            retrieved_contexts=contexts,
            response=result["answer"],
            reference=ground_truth
        )
        samples.append(sample)
        
        pipeline_results.append({
            "question": question,
            "answer": result["answer"],
            "contexts": contexts,
            "ground_truth": ground_truth,
            "performance": result["performance"],
            "latency_seconds": elapsed
        })
    
    eval_dataset = EvaluationDataset(samples=samples)
    evaluator_llm = LangchainLLMWrapper(engine.llm)
    evaluator_embeddings = LangchainEmbeddingsWrapper(engine.embeddings)
    
    metrics = [
        Faithfulness(llm=evaluator_llm),
        ResponseRelevancy(llm=evaluator_llm, embeddings=evaluator_embeddings),
        ContextPrecision(llm=evaluator_llm),
    ]
    
    ragas_results = evaluate(dataset=eval_dataset, metrics=metrics)
    
    # Save results
    os.makedirs("evaluation_results", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = f"evaluation_results/ragas_report_{timestamp}.json"
    
    df = ragas_results.to_pandas()
    overall_scores = {}
    for col in df.columns:
        if col not in ['user_input', 'retrieved_contexts', 'response', 'reference']:
            overall_scores[col] = round(df[col].mean(), 4)

    report = {
        "timestamp": datetime.now().isoformat(),
        "overall_scores": overall_scores,
        "per_question_results": pipeline_results
    }
    
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n  💾 Report saved to: {report_path}")
    print("  Scores:", overall_scores)
    return report

if __name__ == "__main__":
    asyncio.run(run_evaluation())
