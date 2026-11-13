# Nexora Digital Premium eBook Studio

This upgraded Streamlit + GroqCloud app generates:
- A chapter outline and full eBook draft
- A branded A4 eBook PDF
- A separate printable worksheet-pack PDF with selectable worksheets

## Run locally
1. Install Python 3.10+.
2. `pip install -r requirements.txt`
3. Set `GROQ_API_KEY` as an environment variable.
4. Run `streamlit run app.py`

## Deploy to Streamlit Community Cloud
1. Upload `app.py` and `requirements.txt` to a GitHub repository.
2. Create an app at https://share.streamlit.io/
3. Set the main file to `app.py`.
4. In App settings → Secrets, add:
   `GROQ_API_KEY = "your-real-key"`

Never commit your API key to GitHub or share it in screenshots. Keep the app private during testing where possible. A public app using your key can consume your API quota.

## Important
The worksheet pack currently includes six reusable blank templates: Monthly Budget Planner, Daily Spending Tracker, Debt Payoff Tracker, Savings Challenge, Paycheck Planner and Weekly Financial Review. Review generated financial content and all calculations before selling. This is educational material, not personalised financial, tax or legal advice.
