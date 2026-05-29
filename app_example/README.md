# app_example

A minimal Streamlit "hello world" deployed as a Databricks App via DABs.

See `../README.md` for the full demo flow.

## Files

| File | Purpose |
|---|---|
| `databricks.yml` | Bundle config — defines the app resource and two targets |
| `app/app.py` | The Streamlit code |
| `app/app.yaml` | Tells Databricks Apps how to launch (`streamlit run app.py`) |
| `app/requirements.txt` | Python deps for the app's compute |

## Commands

```bash
databricks bundle validate --target dev
databricks bundle deploy   --target dev          # uploads source, registers the app (STOPPED state)
databricks bundle run hello_app --target dev      # starts the app + deploys source to its compute

# The run command prints the app URL when it finishes:
#   https://dev-dabs-demo-hello-app-<workspace-id>.aws.databricksapps.com

# To redeploy after editing app/app.py:
databricks bundle deploy --target dev             # re-uploads source
databricks bundle run hello_app --target dev     # rolls out the new version

# Clean up
databricks bundle destroy --target dev
```

> **First deploy is slow.** Provisioning the app compute the first time takes
> ~1–2 min (you'll see "App is starting..." 10+ times). Subsequent deploys
> are faster because the compute already exists.

## What an "App" deployed via DABs gives you

- Source code lives in git, gets uploaded on every `bundle deploy`
- The runtime spec (`app.yaml` + `requirements.txt`) lives alongside the code
- The app's identity / permissions are managed by Databricks Apps, not the bundle
- Different `target:` blocks deploy the same app to different workspaces with
  different names — perfect for dev/staging/prod separation
