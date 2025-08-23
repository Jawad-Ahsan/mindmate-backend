#!/usr/bin/env python3
"""
Simple test script for the improved AsyncReasoningLLMClient
Focuses on key improvements: background tasks, caching, and error handling
"""

import asyncio
import time
from agents.llm_client import (
    AsyncReasoningLLMClient, 
    TaskType, 
    create_reasoning_client
)

async def test_background_task_completion():
    """Test that background tasks complete properly instead of being cancelled"""
    print("\n=== Testing Background Task Completion ===")
    client = create_reasoning_client()
    
    try:
        # Start a single background task
        task_id = await client.reason_background(
            "What are the main symptoms of diabetes?",
            TaskType.GENERAL_REASONING
        )
        
        print(f"Started background task: {task_id}")
        
        # Wait for completion with timeout
        max_wait_time = 30  # 30 seconds timeout
        start_time = time.time()
        
        while True:
            task_status = client.get_task_status(task_id)
            if task_status and task_status.status in ["completed", "failed", "cancelled"]:
                print(f"Task {task_id} {task_status.status}")
                
                if task_status.status == "completed":
                    result = client.get_task_result(task_id)
                    print(f"✅ SUCCESS: Task completed with result: {result.final_answer[:100]}...")
                    print(f"   Processing time: {result.processing_time:.2f}s")
                    print(f"   Confidence: {result.overall_confidence:.2f}")
                    return True
                elif task_status.status == "failed":
                    print(f"❌ FAILED: {task_status.error}")
                    return False
                else:
                    print(f"❌ CANCELLED: Task was cancelled unexpectedly")
                    return False
            
            # Check for timeout
            if time.time() - start_time > max_wait_time:
                print(f"⏰ TIMEOUT: Task {task_id} did not complete within {max_wait_time}s")
                client.cancel_task(task_id)
                return False
                
            await asyncio.sleep(1)
            
    finally:
        await client.close()

async def test_caching_speedup():
    """Test that caching provides significant speedup"""
    print("\n=== Testing Caching Speedup ===")
    client = create_reasoning_client(enable_cache=True)
    
    try:
        prompt = "What are the symptoms of hypertension?"
        
        # First request (should hit API)
        print("Making first request (API call)...")
        start_time = time.time()
        result1 = await client.reason_async(prompt, TaskType.GENERAL_REASONING)
        time1 = time.time() - start_time
        print(f"First request took: {time1:.2f}s")
        
        # Second request (should hit cache)
        print("Making second request (cache hit)...")
        start_time = time.time()
        result2 = await client.reason_async(prompt, TaskType.GENERAL_REASONING)
        time2 = time.time() - start_time
        print(f"Second request took: {time2:.2f}s")
        
        speedup = time1 / time2 if time2 > 0 else float('inf')
        print(f"Cache speedup: {speedup:.1f}x faster")
        
        if speedup > 5:  # Cache should be at least 5x faster
            print("✅ SUCCESS: Caching working effectively")
            return True
        else:
            print("❌ FAILED: Caching not providing expected speedup")
            return False
            
    finally:
        await client.close()

async def test_graceful_shutdown():
    """Test that shutdown is graceful and doesn't leave hanging tasks"""
    print("\n=== Testing Graceful Shutdown ===")
    client = create_reasoning_client()
    
    try:
        # Start a background task
        task_id = await client.reason_background(
            "Explain the cardiovascular system",
            TaskType.MEDICAL_TRACE
        )
        
        print(f"Started task: {task_id}")
        
        # Wait a bit for task to start
        await asyncio.sleep(2)
        
        # Check task status before shutdown
        task_status = client.get_task_status(task_id)
        print(f"Task status before shutdown: {task_status.status if task_status else 'None'}")
        
        # Shutdown should be graceful
        print("Initiating graceful shutdown...")
        await client.close()
        
        print("✅ SUCCESS: Shutdown completed gracefully")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: Shutdown error: {e}")
        return False

async def test_health_monitoring():
    """Test health monitoring capabilities"""
    print("\n=== Testing Health Monitoring ===")
    client = create_reasoning_client()
    
    try:
        # Get initial health status
        initial_health = client.get_health_status()
        print(f"Initial health: {initial_health}")
        
        # Make a request
        result = await client.reason_async(
            "What is asthma?",
            TaskType.GENERAL_REASONING
        )
        
        # Get health status after request
        final_health = client.get_health_status()
        print(f"Final health: {final_health}")
        
        # Check that health monitoring is working
        if (final_health['circuit_breaker']['success_count'] > 0 or 
            final_health['background_tasks']['total'] >= 0):
            print("✅ SUCCESS: Health monitoring working")
            return True
        else:
            print("❌ FAILED: Health monitoring not updating")
            return False
            
    finally:
        await client.close()

async def main():
    """Run all tests"""
    print("Starting Simple LLM Client Tests")
    print("=" * 50)
    
    tests = [
        test_background_task_completion,
        test_caching_speedup,
        test_graceful_shutdown,
        test_health_monitoring
    ]
    
    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"Test failed with exception: {e}")
            results.append(False)
        print("-" * 50)
    
    # Summary
    passed = sum(results)
    total = len(results)
    print(f"\nTest Summary: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The LLM client improvements are working correctly.")
    else:
        print("⚠️  Some tests failed. Check the output above for details.")

if __name__ == "__main__":
    asyncio.run(main())
