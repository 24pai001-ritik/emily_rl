# Emily RL - Social Media Content Generation with Reinforcement Learning

An AI-powered social media content generation system that uses reinforcement learning to optimize content creation for different platforms and audiences.

## Features

- **Reinforcement Learning Agent**: Learns optimal content strategies based on engagement metrics
- **Multi-Platform Support**: Instagram, Twitter/X, LinkedIn, Facebook
- **Trend-Aware Generation**: Creates trendy content based on current social media trends
- **Business Profile Adaptation**: Tailors content to specific business types and industries
- **Real-time Optimization**: Continuously improves content performance

## Architecture

### Core Components

- `main.py`: Main orchestrator for the RL learning cycle
- `rl_agent.py`: Reinforcement learning agent with preference learning
- `generate.py`: Prompt generation with trendy/standard modes
- `db.py`: Supabase database operations

### Learning Cycle

1. **Generate Content**: RL agent selects creative parameters
2. **Publish & Collect Metrics**: Post content and gather engagement data
3. **Calculate Reward**: Evaluate performance based on platform-specific metrics
4. **Update Agent**: RL agent learns from feedback to improve future content

## Setup

### Prerequisites

- Python 3.8+
- Supabase account and project
- Social media API access (for production)

### Installation

1. Clone the repository:
```bash
git clone https://github.com/24pai001-ritik/emily_rl.git
cd emily_rl
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
```bash
cp env.example .env
# Edit .env with your Supabase credentials
```

4. Configure your Supabase database with the required tables (see Database Schema section below).

## Database Schema

Create these tables in your Supabase database:

### Required Tables

#### `rl_preferences`
```sql
CREATE TABLE rl_preferences (
  id SERIAL PRIMARY KEY,
  platform TEXT NOT NULL,
  time_bucket TEXT NOT NULL,
  day_of_week INTEGER NOT NULL,
  dimension TEXT NOT NULL,
  action_value TEXT NOT NULL,
  preference_score FLOAT DEFAULT 0.0,
  num_samples INTEGER DEFAULT 0,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW(),
  UNIQUE(platform, time_bucket, day_of_week, dimension, action_value)
);
```

#### `post_contents`
```sql
CREATE TABLE post_contents (
  id SERIAL PRIMARY KEY,
  post_id TEXT NOT NULL UNIQUE,
  action_id INTEGER,
  platform TEXT NOT NULL,
  business_id TEXT NOT NULL,
  topic TEXT,
  post_type TEXT,
  business_context TEXT,
  business_aesthetic TEXT,
  image_prompt TEXT,
  caption_prompt TEXT,
  generated_caption TEXT,
  generated_image_url TEXT,
  status TEXT DEFAULT 'generated',
  created_at TIMESTAMP DEFAULT NOW(),
  posted_at TIMESTAMP,
  updated_at TIMESTAMP DEFAULT NOW()
);
```

#### `rl_actions`
```sql
CREATE TABLE rl_actions (
  id SERIAL PRIMARY KEY,
  post_id TEXT NOT NULL,
  platform TEXT NOT NULL,
  time_bucket TEXT,
  day_of_week INTEGER,
  action JSONB,
  created_at TIMESTAMP DEFAULT NOW()
);
```

#### `post_snapshots`
```sql
CREATE TABLE post_snapshots (
  id SERIAL PRIMARY KEY,
  post_id TEXT NOT NULL,
  platform TEXT NOT NULL,
  likes INTEGER DEFAULT 0,
  comments INTEGER DEFAULT 0,
  shares INTEGER DEFAULT 0,
  saves INTEGER DEFAULT 0,
  replies INTEGER DEFAULT 0,
  retweets INTEGER DEFAULT 0,
  reactions INTEGER DEFAULT 0,
  followers INTEGER DEFAULT 0,
  created_at TIMESTAMP DEFAULT NOW()
);
```

#### `rl_rewards`
```sql
CREATE TABLE rl_rewards (
  id SERIAL PRIMARY KEY,
  post_id TEXT NOT NULL,
  reward FLOAT,
  baseline FLOAT,
  created_at TIMESTAMP DEFAULT NOW()
);
```

#### `rl_baselines`
```sql
CREATE TABLE rl_baselines (
  id SERIAL PRIMARY KEY,
  platform TEXT NOT NULL UNIQUE,
  value FLOAT DEFAULT 0.0,
  updated_at TIMESTAMP DEFAULT NOW()
);
```

#### `profiles`
```sql
CREATE TABLE profiles (
  id TEXT PRIMARY KEY,
  profile_embedding JSONB,
  created_at TIMESTAMP DEFAULT NOW(),
  updated_at TIMESTAMP DEFAULT NOW()
);
```

4. Configure your Supabase database with the required tables.

## Usage

Run a single content generation cycle:

```bash
python main.py
```

## Database Schema

Required Supabase tables:
- `rl_preferences`: Stores RL agent preferences
- `post_contents`: Content metadata and status
- `rl_actions`: RL agent action history
- `post_snapshots`: Engagement metrics snapshots
- `rl_rewards`: Reward calculation history
- `rl_baselines`: Performance baselines
- `profiles`: Business profile embeddings

## Deployment Considerations

⚠️ **Important**: This codebase currently uses simulated metrics for development. For production deployment:

1. Replace `simulate_platform_metrics()` with real API calls
2. Implement proper async metric collection (posts need time to accumulate engagement)
3. Add rate limiting and error handling for social media APIs
4. Set up proper monitoring and logging

## License

[Add your license here]

## Contributing

[Add contribution guidelines here]
