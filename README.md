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
cp .env.example .env
# Edit .env with your Supabase credentials
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
