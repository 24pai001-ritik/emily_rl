# SYSTEM FLOW AND FUNCTION REFERENCE

## Section 1: High-Level Architecture

### What the System Does
This is a Reinforcement Learning (RL) system for social media content generation that automatically learns optimal posting strategies. The system generates social media posts with varying creative parameters (tone, length, creativity, visual style, etc.) and uses engagement metrics to continuously improve content performance across different platforms (Instagram, X/Twitter, LinkedIn, Facebook).

### What Problem It Solves
The system solves the challenge of consistently creating high-performing social media content by using machine learning to discover optimal combinations of creative parameters for different business types, industries, platforms, and time contexts. It eliminates guesswork in content strategy by learning from real engagement data.

### How RL Is Integrated
The system implements a contextual bandit RL approach with:
- **Discrete preferences**: Platform-specific action preferences stored in Supabase
- **Continuous embeddings**: Theta parameters for business/topic context generalization
- **Reward calculation**: Time-weighted engagement metrics with platform-specific scoring
- **Baseline tracking**: Per-platform baseline adjustment for reward normalization

## Section 2: End-to-End Flow Diagram (Textual)

### Complete Execution Flow

```
1. ENTRY POINT (main.py:run_one_post)
   ↓ topic_embedding, platform, date, time

2. BUSINESS CONTEXT LOADING
   ↓ BUSINESS_ID → db.get_profile_embedding_with_fallback()
   ↓ BUSINESS_ID → db.get_profile_business_data()
   ↓ Returns: business_embedding (384D), profile_data (dict)

3. PROMPT GENERATION (generate.py:generate_prompts)
   ↓ inputs dict + embeddings → build_context()
   ↓ context → rl_agent.select_action()
   ↓ RL action selected (HOOK_TYPE, LENGTH, TONE, etc.)
   ↓ if HOOK_TYPE == "trendy" → classify_trend_style() + build_grok_trend_prompt()
   ↓ else → PROMPT_TEMPLATE filling
   ↓ Returns: action, context, ctx_vec, mode, prompts

4. RL ACTION STORAGE
   ↓ post_id generated → db.insert_action()
   ↓ Stores: action parameters, context, platform

5. POST CONTENT STORAGE
   ↓ post_id, action_id → db.insert_post_content()
   ↓ Stores: prompts, business context, metadata, status="generated"

6. SIMULATED POSTING
   ↓ post_id → db.mark_post_as_posted()
<<<<<<< HEAD
   ↓ status remains "generated" (until media_id provided), posted_at timestamp set
=======
   ↓ status → "posted", posted_at timestamp
>>>>>>> 1da14f9b985884c988152cd658d6fac1637e6ce5

7. REWARD RECORD CREATION
   ↓ BUSINESS_ID, post_id → db.create_post_reward_record()
   ↓ Creates pending reward record, eligible_at = 24h later

8. REWARD CALCULATION (ASYNC - IMPLEMENTED)
   ↓ job_queue.queue_reward_calculation_job() after posting
   ↓ job_worker processes → db.fetch_or_calculate_reward()
   ↓ Gets snapshots → calculate_reward_from_snapshots()
   ↓ Platform engagement scoring → time-weighted reward
   ↓ Normalization with follower count + deletion penalties
   ↓ update_and_get_baseline() → proper baseline calculation

9. RL UPDATE (ASYNC - IMPLEMENTED)
   ↓ Automatic RL job queued after reward calculation
   ↓ job_worker processes → rl_agent.update_rl()
   ↓ Updates discrete preferences in Supabase
   ↓ Updates continuous theta parameters
   ↓ Uses calculated baseline for proper advantage computation

DATA FLOW SUMMARY:
- CREATED: post_id, action_id, reward records
- TRANSFORMED: embeddings → context → action → prompts
- STORED: actions, posts, rewards, preferences, theta
- READ: profile data, preferences, snapshots, baselines
```

## Section 3: Function Reference Table

| Function | File | Purpose | Called By | Writes DB? | Reads DB? | Notes |
|----------|------|---------|-----------|------------|-----------|--------|
| `run_one_post` | main.py | Orchestrates complete post generation cycle | main.py entry | Yes | Yes | Core - main execution flow |
| `generate_prompts` | generate.py | Generates prompts based on RL action selection | main.py | No | No | Core - RL integration point |
| `select_action` | rl_agent.py | RL policy: selects creative parameters | generate.py | No | Yes | Core - RL decision making |
| `update_rl` | rl_agent.py | Updates RL parameters based on reward | (simulated async) | Yes | Yes | Core - learning mechanism |
| `build_context` | generate.py | Converts inputs to RL context dict | generate.py | No | No | Supportive - data transformation |
| `build_context_vector` | rl_agent.py | Creates continuous context vector | rl_agent.py | No | No | Supportive - embedding concatenation |
| `classify_trend_style` | generate.py | Maps business profile to trend style | generate.py | No | No | Supportive - business intelligence |
| `build_grok_trend_prompt` | generate.py | Creates Grok prompt for trendy content | generate.py | No | No | Supportive - prompt engineering |
| `calculate_platform_engagement` | db.py | Platform-specific engagement scoring | db.py | No | No | Core - reward calculation |
| `calculate_reward_from_snapshots` | db.py | Time-weighted reward calculation | db.py | No | Yes | Core - reward computation |
| `fetch_or_calculate_reward` | db.py | Reward calculation orchestrator | (external async worker) | Yes | Yes | Core - reward lifecycle |
| `get_preference` | db.py | Retrieves RL preferences | rl_agent.py | No | Yes | Core - RL state reading |
| `update_preference` | db.py | Updates RL preferences | rl_agent.py | Yes | Yes | Core - RL learning |
| `update_and_get_baseline` | db.py | Updates platform baseline | rl_agent.py | Yes | Yes | Core - reward normalization |
| `get_profile_embedding` | db.py | Retrieves business embedding | db.py | No | Yes | Supportive - data loading |
| `get_profile_embedding_with_fallback` | db.py | Gets embedding with random fallback | main.py | No | Yes | Supportive - data loading |
| `get_profile_business_data` | db.py | Gets business profile data | main.py | No | Yes | Supportive - data loading |
| `insert_action` | db.py | Stores RL action record | main.py | Yes | No | Core - data persistence |
| `insert_post_content` | db.py | Stores generated content | main.py | Yes | No | Core - data persistence |
<<<<<<< HEAD
| `mark_post_as_posted` | db.py | Updates post status to posted only when media_id provided | main.py | Yes | No | Supportive - status management |
=======
| `mark_post_as_posted` | db.py | Updates post status to posted | main.py | Yes | No | Supportive - status management |
>>>>>>> 1da14f9b985884c988152cd658d6fac1637e6ce5
| `create_post_reward_record` | db.py | Creates pending reward record | main.py | Yes | No | Core - reward initialization |
| `get_post_reward` | db.py | Retrieves reward record | db.py | No | Yes | Supportive - reward checking |
| `get_post_snapshots` | db.py | Gets engagement snapshots | db.py | No | Yes | Supportive - data aggregation |
| `insert_post_snapshot` | db.py | Stores engagement metrics | (external) | Yes | No | Supportive - metrics collection |
| `get_post_metrics` | db.py | Gets latest post metrics | (external) | No | Yes | Supportive - metrics access |
| `queue_reward_calculation_job` | job_queue.py | Queues async reward calculation | main.py | No | No | Core - async job management |
| `process_reward_calculation_job` | job_queue.py | Processes reward calculation jobs | job_worker | Yes | Yes | Core - reward calculation |
| `process_rl_update_job` | job_queue.py | Processes RL learning updates | job_worker | Yes | Yes | Core - RL learning |
| `get_action_and_context_from_db` | job_queue.py | Retrieves stored action data for RL | job_queue.py | No | Yes | Supportive - data retrieval |
| `softmax` | rl_agent.py | Softmax probability calculation | rl_agent.py | No | No | Supportive - math utility |

## Section 4: RL Lifecycle Explanation

### How Action Is Selected
1. **Context Building**: Business embedding (384D) + topic embedding (384D) → 768D context vector
2. **Preference Lookup**: For each action dimension (HOOK_TYPE, LENGTH, etc.), retrieve platform/time-specific preference scores from Supabase
3. **Scoring**: Combine discrete preference H + continuous score (θ · context_vector)
4. **Probability**: Softmax over all dimension values
5. **Selection**: Random choice weighted by probabilities

### How Reward Is Calculated
1. **Engagement Scoring**: Platform-specific formula (Instagram: 3×saves + 2×shares + 1×comments + 0.3×likes)
2. **Time Weighting**: Apply exponential decay weights (6h: 0.396, 24h: 0.258, etc.)
3. **Normalization**: log(1 + reward) / log(1 + followers), then tanh bounding
4. **Deletion Penalty**: -0.7 × exp(-days_since_deletion/3.0) if post deleted
5. **Final Range**: [-1.0, 1.0] with 0.0 baseline

### How Preference + Theta Updates Work
- **Advantage**: reward - baseline (per-platform running average)
- **Discrete Update**: preference += learning_rate × advantage
- **Continuous Update**: θ[dimension,value] += learning_rate × advantage × context_vector
- **Baseline Update**: baseline += alpha × (reward - baseline)

### Where Learning Can Break
- **Reward Delay**: 24h eligibility window may miss early viral posts
- **Sparse Feedback**: Low engagement posts provide weak learning signal
- **Context Drift**: Business/topic embeddings may change over time
- **Platform Differences**: Engagement patterns vary significantly by platform
- **Deletion Noise**: Manual deletions introduce human bias in reward signal

## Section 5: Known Gaps & Assumptions

### Simulated Logic
- **Posting**: Currently simulated, no actual API integration
- **RL Updates**: Queued but not executed (commented out in main.py)
- **Metrics Collection**: No actual social media API polling
- **Async Workers**: Reward calculation and RL updates happen synchronously

### Missing Async Workers
- ✅ **Background job system**: Implemented for reward calculation and RL updates
- ✅ **RL update scheduler**: Automatic triggering after reward calculation
- No worker to collect engagement metrics from social platforms (handled by separate project)
- No monitoring/alerting for failed updates (basic error handling implemented)

### Critical Fixes Applied
- ✅ **Baseline Calculation**: `update_and_get_baseline()` now properly called after reward calculation
- ✅ **RL Rewards Table**: Now stores actual calculated baseline instead of hardcoded 0.0
- ✅ **Advantage Calculation**: RL updates will now have correct baseline when enabled
- ✅ **Async Job System**: Implemented background job processing for reward calculation and RL updates
- ✅ **Separation of Concerns**: RL system now runs independently of social media data fetching

### Assumed APIs
- **Supabase**: Real database operations (working)
- **Social APIs**: Instagram/X/Facebook APIs for metrics (not implemented)
- **AI APIs**: Grok for trendy content, Gemini for images (prompts generated but not called)
- **Posting APIs**: Platform-specific posting endpoints (simulated)

### Time-based Assumptions
- **Reward Window**: 24h eligibility assumes engagement peaks within 1 day
- **Time Buckets**: morning/evening categorization may not match user behavior
- **Snapshot Timing**: 6h, 24h, 48h, 72h, 168h intervals assumed optimal
- **Baseline Update**: alpha=0.1 assumes stable reward distributions

### Production Readiness Gaps
- No error handling for API failures
- No retry logic for failed database operations
- No data validation on embeddings/metrics
- No rate limiting for external API calls
- No monitoring/logging infrastructure
