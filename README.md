# CX Tech Radar

A Streamlit application for discovering and evaluating Customer Experience (CX) tools with AI-powered analysis and interactive radar visualization.

## Features

- 🤖 **AI-Powered Analysis**: Uses Anthropic Claude to analyze tools and generate structured insights
- 🔍 **Full-Text Search**: FTS5-powered search with relevance ranking (falls back to LIKE if FTS5 unavailable)
- 📊 **Interactive Radar**: Plotly-based tech radar with stable point placement and filtering
- ⚙️ **Configurable Scoring**: Weighted scoring system (configurable via `settings.yaml`)
- 💾 **Local-First**: SQLite database with migration system and backup scripts
- 📥 **Data Export**: CSV export functionality for tools and search results

## Setup

### Prerequisites

- Python 3.9.6+
- Anthropic API key

### Installation

1. Clone the repository:
```bash
git clone https://github.com/seanwarner-tfh/cx-tech-radar.git
cd cx-tech-radar
```

2. Create a virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Create a `.env` file with your Anthropic API key:
```bash
echo "ANTHROPIC_API_KEY=your-api-key-here" > .env
```

4. (Optional) Set the Anthropic model (defaults to `claude-3-haiku-20240307`):
```bash
echo "ANTHROPIC_MODEL=claude-3-haiku-20240307" >> .env
```

5. Run database migrations:
```bash
python scripts/migrate.py
```

6. Start the application:
```bash
streamlit run app.py
```

## Usage

### Adding Tools

1. Navigate to the "➕ Add Tool" page
2. Paste tool information (description, website content, etc.)
3. Click "🤖 Analyze with AI" to generate analysis
4. Review the analysis and click "💾 Save to Radar" to add to the database

### Searching

- Use the "🔍 Search" page to find tools by name, category, or keyword
- FTS5 provides relevance-ranked results when available
- Export search results as CSV

### Radar View

- View all tools on an interactive radar chart
- Use filters to narrow down by:
  - Category
  - Radar position (Adopt, Trial, Assess, Hold)
  - CX and Integration score ranges
- Toggle labels on/off for cleaner visualization

## Configuration

Edit `settings.yaml` to customize:

- **Scoring weights**: Adjust `cx_weight` and `integration_weight` (must sum to 1.0)
- **Categories**: Modify the list of available categories
- **Cost bands**: Update cost rating definitions

## Database Management

### Migrations

Apply database migrations:
```bash
python scripts/migrate.py
```

Migrations are tracked and only new ones will be applied.

### Backups

Create a timestamped backup:
```bash
python scripts/backup.py
```

Backups are saved to `data/backups/`.

## Testing

Make sure your virtual environment is activated, then run the test suite:
```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
python tests/run_tests.py
```

Or use unittest directly:
```bash
python -m unittest discover tests
```

Tests cover:
- Database operations (CRUD, filtering, search)
- Configuration loading and weighted scoring
- Stable offset computation

Test files use temporary databases, so your production data is safe.

## Logging

Logging is configured automatically when the app starts. Logs are written to:
- `logs/cx_tech_radar.log` - All log messages
- `logs/cx_tech_radar_errors.log` - Error and above only

Set log level via environment variable:
```bash
export LOG_LEVEL=DEBUG  # Options: DEBUG, INFO, WARNING, ERROR, CRITICAL
streamlit run app.py
```

Logs rotate automatically (10MB max, 5 backups).

## Project Structure

```
cx-tech-radar/
├── app.py                 # Main Streamlit application
├── settings.yaml          # Configuration file
├── requirements.txt       # Python dependencies
├── migrations/           # Database migration SQL files
├── scripts/              # Utility scripts (migrate, backup)
├── src/
│   ├── database.py      # Database operations (TechRadarDB)
│   ├── analyzer.py      # AI analysis (TechAnalyzer)
│   ├── visualizer.py    # Radar chart generation
│   └── config.py        # Configuration loader
└── data/
    ├── radar.db         # SQLite database (gitignored)
    └── backups/          # Database backups (gitignored)
```

## Improvements Made

This version includes several enhancements:

1. **Stability & Correctness**
   - Fixed Anthropic model selection with environment variable support
   - Added retry logic with exponential backoff for API calls
   - Robust JSON parsing with Pydantic validation

2. **Search Quality**
   - FTS5 full-text search with BM25 ranking
   - Graceful fallback to LIKE search if FTS5 unavailable

3. **Radar UX**
   - Stable point placement (deterministic offsets stored in DB)
   - Sidebar filters for category, position, and scores
   - Toggle for label visibility

4. **Config & Scoring**
   - Externalized weights in `settings.yaml`
   - Weighted scoring calculation (default: 60% CX, 40% Integration)

5. **DX & Operations**
   - Migration system for database schema changes
   - Backup script for data safety
   - Caching for improved performance
   - CSV export functionality

## License

Internal tool for Tools For Humanity - Customer Experience Team

## Contributing

This is an internal tool. For improvements or issues, please contact the CX team.

