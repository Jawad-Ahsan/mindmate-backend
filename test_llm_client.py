#!/usr/bin/env python3
"""
Test script for the improved AsyncReasoningLLMClient
Demonstrates various capabilities including background tasks, caching, and error handling
"""

import asyncio
import time
from agents.llm_client import (
    AsyncReasoningLLMClient, 
    TaskType, 
    create_reasoning_client,
    extract_symptoms_async,
    generate_diagnosis_async
)

async def test_basic_reasoning():
    """Test basic synchronous reasoning"""
    print("\n=== Testing Basic Reasoning ===")
    client = create_reasoning_client()
    
    try:
        result = await client.reason_async(
            "What are the common symptoms of diabetes?",
            TaskType.GENERAL_REASONING
        )
        print(f"Basic reasoning result: {result.final_answer[:150]}...")
        print(f"Confidence: {result.overall_confidence:.2f}")
        print(f"Processing time: {result.processing_time:.2f}s")
    finally:
        await client.close()

async def test_symptom_extraction():
    """Test symptom extraction"""
    print("\n=== Testing Symptom Extraction ===")
    client = create_reasoning_client()
    
    try:
        patient_desc = """
        I've been experiencing severe chest pain for the last 3 days, especially when I breathe deeply.
        I also have a persistent cough with yellow sputum, fever around 101°F, and fatigue.
        The pain radiates to my left shoulder and gets worse with movement.
        """
        
        symptoms = await extract_symptoms_async(client, patient_desc)
        print(f"Extracted {len(symptoms)} symptoms:")
        for i, symptom in enumerate(symptoms, 1):
            print(f"  {i}. {symptom.name} (severity: {symptom.severity}, duration: {symptom.duration})")
    finally:
        await client.close()

async def test_background_tasks():
    """Test background task processing"""
    print("\n=== Testing Background Tasks ===")
    client = create_reasoning_client()
    
    try:
        # Start multiple background tasks
        task_ids = []
        prompts = [
            "Analyze the risk factors for cardiovascular disease",
            "What are the differential diagnoses for abdominal pain?",
            "Explain the pathophysiology of hypertension"
        ]
        
        for i, prompt in enumerate(prompts):
            task_id = await client.reason_background(
                prompt,
                TaskType.MEDICAL_TRACE
            )
            task_ids.append(task_id)
            print(f"Started task {i+1}: {task_id}")
        
        # Monitor all tasks
        print("\nMonitoring background tasks...")
        completed_tasks = set()
        
        while len(completed_tasks) < len(task_ids):
            for task_id in task_ids:
                if task_id in completed_tasks:
                    continue
                    
                task_status = client.get_task_status(task_id)
                if task_status and task_status.status in ["completed", "failed", "cancelled"]:
                    completed_tasks.add(task_id)
                    print(f"Task {task_id} {task_status.status}")
                    
                    if task_status.status == "completed":
                        result = client.get_task_result(task_id)
                        print(f"  Result: {result.final_answer[:100]}...")
            
            if len(completed_tasks) < len(task_ids):
                await asyncio.sleep(1)
        
        # Show final health status
        health = client.get_health_status()
        print(f"\nFinal health status: {health}")
        
    finally:
        await client.close()

async def test_error_handling():
    """Test error handling and circuit breaker"""
    print("\n=== Testing Error Handling ===")
    client = create_reasoning_client()
    
    try:
        # Test with invalid prompt (very long)
        long_prompt = "test " * 10000  # Very long prompt that might cause issues
        
        result = await client.reason_async(
            long_prompt,
            TaskType.GENERAL_REASONING,
            max_tokens=50  # Very low token limit
        )
        
        print(f"Error handling result: {result.final_answer[:100]}...")
        print(f"Confidence: {result.overall_confidence:.2f}")
        
        # Check circuit breaker status
        health = client.get_health_status()
        print(f"Circuit breaker status: {health['circuit_breaker']}")
        
    finally:
        await client.close()

async def test_caching():
    """Test caching functionality"""
    print("\n=== Testing Caching ===")
    client = create_reasoning_client(enable_cache=True)
    
    try:
        prompt = "What are the symptoms of influenza?"
        
        # First request (should hit API)
        print("Making first request...")
        start_time = time.time()
        result1 = await client.reason_async(prompt, TaskType.GENERAL_REASONING)
        time1 = time.time() - start_time
        print(f"First request took: {time1:.2f}s")
        
        # Second request (should hit cache)
        print("Making second request (should use cache)...")
        start_time = time.time()
        result2 = await client.reason_async(prompt, TaskType.GENERAL_REASONING)
        time2 = time.time() - start_time
        print(f"Second request took: {time2:.2f}s")
        
        print(f"Cache speedup: {time1/time2:.1f}x faster")
        print(f"Results match: {result1.final_answer[:50] == result2.final_answer[:50]}")
        
    finally:
        await client.close()

async def test_concurrent_requests():
    """Test concurrent request handling"""
    print("\n=== Testing Concurrent Requests ===")
    client = create_reasoning_client()
    
    try:
        prompts = [
            "What is diabetes?",
            "What is hypertension?",
            "What is asthma?",
            "What is arthritis?"
        ]
        
        async def process_prompt(prompt, index):
            start_time = time.time()
            result = await client.reason_async(prompt, TaskType.GENERAL_REASONING)
            duration = time.time() - start_time
            return index, result.final_answer[:50], duration
        
        # Process all prompts concurrently
        tasks = [process_prompt(prompt, i) for i, prompt in enumerate(prompts)]
        results = await asyncio.gather(*tasks)
        
        print("Concurrent processing results:")
        for index, answer, duration in results:
            print(f"  {index+1}. {answer}... (took {duration:.2f}s)")
        
        # Show rate limiter status
        health = client.get_health_status()
        print(f"Rate limiter status: {health['rate_limiter']}")
        
    finally:
        await client.close()

async def main():
    """Run all tests"""
    print("Starting LLM Client Tests")
    print("=" * 50)
    
    tests = [
        test_basic_reasoning,
        test_symptom_extraction,
        test_background_tasks,
        test_error_handling,
        test_caching,
        test_concurrent_requests
    ]
    
    for test in tests:
        try:
            await test()
        except Exception as e:
            print(f"Test failed: {e}")
        print("-" * 50)
    
    print("All tests completed!")

if __name__ == "__main__":
    asyncio.run(main())
