# Quick Setup Guide

Get CX Tech Radar running on your machine in 5 minutes.

## Prerequisites

- **Python 3.9.6 or higher**
- **Anthropic API key** ([Get one here](https://console.anthropic.com/))

## Step-by-Step Setup

### 1. Clone the Repository

```bash
git clone https://github.com/seanwarner-tfh/cx-tech-radar.git
cd cx-tech-radar
```

### 2. Create Virtual Environment

```bash
python3 -m venv venv
```

**Activate it:**
- **macOS/Linux:** `source venv/bin/activate`
- **Windows:** `venv\Scripts\activate`

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure API Key

Create a `.env` file in the project root:

```bash
echo "ANTHROPIC_API_KEY=your-api-key-here" > .env
```

Replace `your-api-key-here` with your actual Anthropic API key.

**Optional:** Set a custom model (defaults to `claude-3-haiku-20240307`):
```bash
echo "ANTHROPIC_MODEL=claude-3-haiku-20240307" >> .env
```

### 5. Initialize Database

```bash
python scripts/migrate.py
```

This creates the database schema and sets up full-text search.

### 6. Run the Application

```bash
streamlit run app.py
```

The app will open in your browser at `http://localhost:8501`

## That's It! 🎉

You should now see the CX Tech Radar homepage. Start by:
1. Going to the **"➕ Add Tool"** page
2. Pasting some tool information
3. Clicking **"🤖 Analyze with AI"**

## Troubleshooting

### "ANTHROPIC_API_KEY not found"
- Make sure your `.env` file exists in the project root
- Check that the file contains: `ANTHROPIC_API_KEY=sk-ant-...`

### "Module not found" errors
- Make sure your virtual environment is activated
- Run `pip install -r requirements.txt` again

### Database errors
- Run `python scripts/migrate.py` to ensure the database is initialized
- Check that the `data/` directory exists and is writable

### Port already in use
- Streamlit defaults to port 8501. If it's taken, use:
  ```bash
  streamlit run app.py --server.port 8502
  ```

## Next Steps

- **Add your first tool:** Use the "➕ Add Tool" page
- **Explore the radar:** Check out the "📊 Radar View" page
- **Customize settings:** Edit `settings.yaml` to adjust scoring weights
- **Read the full docs:** See `README.md` for detailed information

## Need Help?

Check the main [README.md](README.md) for:
- Detailed feature documentation
- Configuration options
- Database management
- Testing instructions
- Logging setup

