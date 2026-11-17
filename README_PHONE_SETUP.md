# My Routine & Study Tracker — phone-friendly Python app

## Open it on your phone without using a laptop

This is a Python web app built with Streamlit. You do **not** need a laptop to use
the published app on your phone. You do need to publish it once from your phone
using a GitHub account and Streamlit Community Cloud.

### Phone-only publishing steps

1. Install/open GitHub in your phone browser: https://github.com/
2. Sign in or create an account.
3. Create a new **public** repository, for example `my-routine-tracker`.
4. Upload these two files from this ZIP:
   - `routine_tracker.py`
   - `requirements.txt`
5. Open https://share.streamlit.io/ and sign in with GitHub.
6. Tap **Create app** and select your repository.
7. Set the main file path to `routine_tracker.py`, then deploy.
8. Streamlit will give you a public address ending in `.streamlit.app`.
9. Open that address on your phone. In Chrome, use **⋮ > Add to Home screen**
   (or **Install app**, if shown) for an app-like shortcut.

### Important limitations

- The app is mobile-friendly and works in a phone browser.
- In-app reminders are checked while the app page remains open. They are not
  reliable push notifications when the browser is closed or the phone is asleep.
- The included SQLite database is local to the running app. Free hosting can
  reset local files on restart/redeploy. Download CSV backups regularly.
  For persistent multi-device cloud storage, a hosted database such as Supabase
  should be connected before relying on it as your only record.
- Do not put passwords, private keys, or personal sensitive information in the
  repository.

## Run on a computer (optional)

```bash
pip install -r requirements.txt
streamlit run routine_tracker.py
```
