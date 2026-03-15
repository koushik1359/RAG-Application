"""
evaluate.py — RAGAS Evaluation Pipeline for the Enterprise RAG Engine.

Runs a set of test questions through the RAG pipeline, then uses the RAGAS
framework to measure answer quality with industry-standard metrics:

  - Faithfulness:       Is the answer grounded in the retrieved context?
  - Answer Relevancy:   Does the answer actually address the question?
  - Context Precision:  Were the retrieved chunks relevant to the question?

Usage:
    python evaluate.py                          # Run with default test questions
    python evaluate.py --file test_questions.json  # Run with custom test file

Output:
    - Console table with per-question scores
    - Saved JSON report in evaluation_results/
"""

import os
import sys
import json
import time
from datetime import datetime

# Add the project root to path so we can import app modules
sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv()

# RAGAS imports
from ragas import evaluate
from ragas.metrics import Faithfulness, ResponseRelevancy, ContextPrecision
from ragas.dataset_schema import SingleTurnSample, EvaluationDataset
from ragas.llms import LangchainLLMWrapper

# Our RAG Engine imports
from app.rag_engine import run_rag_pipeline, llm, embeddings
from ragas.embeddings import LangchainEmbeddingsWrapper


# --- Default Test Questions ---
# These questions test different retrieval scenarios
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


def run_evaluation(test_questions=None):
    """
    Run the full RAGAS evaluation pipeline.
    
    1. For each test question, run our RAG pipeline to get answer + contexts
    2. Package results as RAGAS SingleTurnSamples
    3. Evaluate with RAGAS metrics
    4. Save and display results
    """
    if test_questions is None:
        test_questions = DEFAULT_TEST_QUESTIONS
    
    print("=" * 70)
    print("  RAGAS EVALUATION PIPELINE")
    print("  Enterprise RAG Engine — Quality Assessment")
    print("=" * 70)
    print(f"\n  Test Questions: {len(test_questions)}")
    print(f"  Metrics: Faithfulness, Answer Relevancy, Context Precision")
    print(f"  Evaluator LLM: GPT-3.5-Turbo")
    print()
    
    # Step 1: Run each question through our RAG pipeline
    samples = []
    pipeline_results = []
    
    for i, tq in enumerate(test_questions):
        question = tq["question"]
        ground_truth = tq.get("ground_truth", "")
        
        print(f"  [{i+1}/{len(test_questions)}] Running: {question[:60]}...")
        
        t0 = time.time()
        result = run_rag_pipeline(question, chat_history=[])
        elapsed = round(time.time() - t0, 2)
        
        # Extract context strings from documents
        contexts = [doc.page_content for doc in result["context"]]
        
        # Create a RAGAS sample
        sample = SingleTurnSample(
            user_input=question,
            retrieved_contexts=contexts,
            response=result["answer"],
            reference=ground_truth
        )
        samples.append(sample)
        
        # Save individual result for the report
        pipeline_results.append({
            "question": question,
            "answer": result["answer"],
            "contexts": contexts,
            "ground_truth": ground_truth,
            "performance": result["performance"],
            "latency_seconds": elapsed
        })
        
        print(f"         Answer: {result['answer'][:80]}...")
        print(f"         Latency: {elapsed}s\n")
    
    # Step 2: Build RAGAS evaluation dataset
    print("\n" + "=" * 70)
    print("  SCORING WITH RAGAS...")
    print("=" * 70 + "\n")
    
    eval_dataset = EvaluationDataset(samples=samples)
    
    # Wrap our LLM and embeddings for RAGAS
    evaluator_llm = LangchainLLMWrapper(llm)
    evaluator_embeddings = LangchainEmbeddingsWrapper(embeddings)
    
    # Step 3: Run RAGAS evaluation
    metrics = [
        Faithfulness(llm=evaluator_llm),
        ResponseRelevancy(llm=evaluator_llm, embeddings=evaluator_embeddings),
        ContextPrecision(llm=evaluator_llm),
    ]
    
    ragas_results = evaluate(
        dataset=eval_dataset,
        metrics=metrics,
    )
    
    # Step 4: Display results
    print("\n" + "=" * 70)
    print("  EVALUATION RESULTS")
    print("=" * 70)
    
    # Overall scores
    print("\n  📊 OVERALL SCORES:")
    print("  " + "-" * 40)
    
    df = ragas_results.to_pandas()
    
    overall_scores = {}
    for col in df.columns:
        if col not in ['user_input', 'retrieved_contexts', 'response', 'reference']:
            score = df[col].mean()
            overall_scores[col] = round(score, 4)
            emoji = "✅" if score >= 0.7 else "⚠️" if score >= 0.5 else "❌"
            bar = "█" * int(score * 20) + "░" * (20 - int(score * 20))
            print(f"  {emoji} {col:25s} {bar} {score:.4f}")
    print("\n  📋 PER-QUESTION BREAKDOWN:")
    print("  " + "-" * 40)
    
    df = ragas_results.to_pandas()
    for idx, row in df.iterrows():
        print(f"\n  Q{idx+1}: {pipeline_results[idx]['question'][:55]}...")
        for col in df.columns:
            if col not in ['user_input', 'retrieved_contexts', 'response', 'reference']:
                val = row[col]
                if isinstance(val, (int, float)):
                    emoji = "✅" if val >= 0.7 else "⚠️" if val >= 0.5 else "❌"
                    print(f"      {emoji} {col}: {val:.4f}")
    
    # Average latency
    avg_latency = sum(r["latency_seconds"] for r in pipeline_results) / len(pipeline_results)
    print(f"\n  ⚡ Average Query Latency: {avg_latency:.2f}s")
    
    # Step 5: Save results to file
    os.makedirs("evaluation_results", exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_path = f"evaluation_results/ragas_report_{timestamp}.json"
    
    report = {
        "timestamp": datetime.now().isoformat(),
        "num_questions": len(test_questions),
        "overall_scores": overall_scores,
        "average_latency_seconds": round(avg_latency, 2),
        "per_question_results": pipeline_results,
        "config": {
            "retriever_top_k": 10,
            "reranker_top_k": 3,
            "reranker_model": "cross-encoder/ms-marco-MiniLM-L-6-v2",
            "llm_model": "gpt-3.5-turbo",
            "embedding_model": "all-MiniLM-L6-v2"
        }
    }
    
    with open(report_path, "w") as f:
        json.dump(report, f, indent=2, default=str)
    
    print(f"\n  💾 Report saved to: {report_path}")
    print("=" * 70)
    
    return report


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="RAGAS Evaluation for Enterprise RAG")
    parser.add_argument("--file", type=str, help="Path to custom test questions JSON file")
    args = parser.parse_args()
    
    test_questions = None
    if args.file:
        with open(args.file, "r") as f:
            test_questions = json.load(f)
        print(f"Loaded {len(test_questions)} questions from {args.file}")
    
    run_evaluation(test_questions)
