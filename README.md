# DABs Demo — Two Examples

A starter pack for showing a customer who's never used Databricks Asset
Bundles what they look like in practice. Two minimal bundles, two targets
each (dev + prod), and the full command flow you'd walk through live.

## What's in here

```
dabs_demo/
├── README.md                       ← you are here
├── job_example/                    ← serverless job + python dependency
│   ├── databricks.yml              ← bundle config: variables, targets
│   ├── resources/job.yml           ← the job resource
│   └── src/generate_customers.py   ← the notebook the job runs
├── app_example/                    ← minimal Streamlit Databricks App
│   ├── databricks.yml              ← bundle config
│   └── app/
│       ├── app.py                  ← Streamlit hello-world
│       ├── app.yaml                ← Databricks Apps runtime spec
│       └── requirements.txt        ← streamlit
└── bundle_from_existing/           ← "I already have a job — how do I bundle it?"
    ├── README.md                   ← the bundle generate flow
    └── source/say_hello.py         ← the notebook the pre-existing job runs
```

## The two workspaces

| Target | Workspace | CLI profile |
|---|---|---|
| `dev` | `https://fe-sandbox-zg-aws-sandbox.cloud.databricks.com` | `dabs-demo-dev` |
| `prod` | `https://fevm-dabs-prod.cloud.databricks.com` | `dabs-demo-prod` |

Both bundles point at the same workspaces via target-specific config blocks.
Switch which one you deploy to with `--target dev` or `--target prod`.

## Prerequisites

- Databricks CLI v1.0+: `databricks --version`
- Auth set up for both workspaces:
  ```bash
  databricks auth login --host https://fe-sandbox-zg-aws-sandbox.cloud.databricks.com --profile dabs-demo-dev
  databricks auth login --host https://fevm-dabs-prod.cloud.databricks.com --profile dabs-demo-prod
  ```

---

## Demo flow

### 1. Show the bundle structure

Open `job_example/databricks.yml`. Walk through the top-level blocks:

- `bundle:` — the bundle's identity.
- `include:` — pulls in `resources/*.yml`. Splits big bundles into focused files.
- `variables:` — declared up top with descriptions. `${var.catalog}` references
  them anywhere in the YAML.
- `targets:` — two environments. Each target overrides the workspace host,
  the `catalog` variable, and (in prod) `mode: production` rules.

Open `job_example/resources/job.yml`. Walk through:

- **Two tasks with `depends_on`** — `summarize` runs after `generate`,
  appending one row to a `run_log` table per run. Customer can re-run the
  job and watch the log grow.
- **`schedule:` block** — hourly cron, PAUSED for the demo. In dev mode the
  bundle force-pauses regardless; in prod mode the YAML value wins.
- **`tags:` block** — separate from any tags inherited from a budget
  policy. Shows up in billing and the Workflows UI.
- **`environments:` block** — how serverless tasks get Python deps:

  ```yaml
  environments:
    - environment_key: serverless_env
      spec:
        environment_version: "2"
        dependencies:
          - "faker>=30,<31"   # PyPI package; quote anything with a glob char
  ```

  No init scripts, no cluster libraries, no notebook `%pip install`. Declared
  once in YAML, installed automatically.

### Prod-only override: budget policy

Open `databricks.yml` and look at the prod target — it has a
`resources.jobs.generate_customers.budget_policy_id` block that dev
doesn't. This is the **target override** pattern: same job everywhere,
but prod attaches a serverless budget policy so compute spend rolls up
under the policy and inherits its tags.

### 2. Validate the bundle (no deploy)

```bash
cd job_example
databricks bundle validate --target dev
```

Catches typos in YAML, references to undeclared variables, missing files.
Doesn't touch the workspace yet.

### 3. Deploy to dev

```bash
databricks bundle deploy --target dev
```

The CLI:
1. Uploads notebooks and source files to the workspace.
2. Creates the `generate_customers` job in Workflows.

Open the workspace UI → Workflows. You should see
`[dev zach_goehring] generate_customers`.

### 4. Run the job

```bash
databricks bundle run generate_customers --target dev
```

The CLI tails logs. The job:
1. Creates the schema if needed.
2. Calls `faker` (installed via the serverless environment spec) to generate
   synthetic customer rows.
3. Writes `${catalog}.dabs_demo.synthetic_customers`.

### 5. Show the variable override

The whole point of `variables:` is per-environment values without changing
code. Two ways to override at the CLI:

```bash
# One-off — same command, different catalog
databricks bundle deploy --target dev --var catalog=some_other_catalog

# Env var form (useful in CI)
BUNDLE_VAR_catalog=some_other_catalog databricks bundle deploy --target dev
```

### 6. Promote to prod

```bash
databricks bundle validate --target prod   # confirms prod config is valid
databricks bundle deploy --target prod
databricks bundle run generate_customers --target prod
```

`mode: production` means:
- No `[dev <user>]` prefix on the job name.
- `run_as` is required (we set it to the deploying user; in a real prod
  setup this would be a service principal).
- Schedules deploy as-written (no auto-pause).

### 7. Tear down

```bash
databricks bundle destroy --target dev    # removes everything in dev
databricks bundle destroy --target prod   # removes everything in prod
```

Removes bundle-managed resources (the job, uploaded files). Does **not**
delete UC tables the job created — you clean those up separately if you
need to.

---

## Same flow for the app

```bash
cd ../app_example
databricks bundle validate --target dev
databricks bundle deploy --target dev              # uploads source, registers app
databricks bundle run hello_app --target dev      # starts the app's compute, deploys source to it
```

The `bundle run` step prints the app URL when it finishes. First-time start
takes ~1–2 min while the app compute provisions. Subsequent runs are faster.

To redeploy after an edit to `app/app.py`:

```bash
databricks bundle deploy --target dev
databricks bundle run hello_app --target dev      # rolls out the new version
```

Tear down:

```bash
databricks bundle destroy --target dev
```

---

## Quick reference — the commands the customer needs

| Command | What it does |
|---|---|
| `databricks bundle validate --target X` | Parse + lint locally and against the workspace. No changes. |
| `databricks bundle deploy --target X` | Upload files, create/update resources. |
| `databricks bundle run NAME --target X` | Trigger a job/pipeline; stream logs. |
| `databricks bundle destroy --target X` | Remove bundle-managed resources. |
| `databricks bundle summary --target X` | Show what's currently deployed. |
| `databricks bundle deploy --var catalog=Y` | Override a variable for one deploy. |

## When something goes wrong

| Symptom | Likely cause |
|---|---|
| `Invalid access token` | Your CLI profile's OAuth token expired — re-run `databricks auth login --profile X` |
| `unknown variable: foo` | `${var.foo}` referenced but not declared or no default given |
| `bundle validate` fails on prod only | `mode: production` requires `run_as` set; pre-prod targets are more forgiving |
| `App does not exist` after a state mismatch | wipe `.databricks/` locally and redeploy (caveat: only if bundle state is the only thing broken) |
| Job fails with `ModuleNotFoundError: faker` | dependency missing from `environments[].spec.dependencies` |

---

---

## Bonus: bundle-ify an existing UI-created job

Most customers already have jobs in the Workflows UI and want to know how
to bring them into a bundle without rewriting. `bundle_from_existing/`
walks through it.

A pre-existing job (`existing_job_customer_report_notebook`, job ID
`954844862799777`) is already in the dev workspace. It runs an `.ipynb`
notebook with two PyPI dependencies (`faker`, `humanize`) attached via
the notebook's Environment side panel — the most common customer setup.
The demo:

```bash
# 1. Show the customer the job in Workflows UI, then click into the
#    notebook to show the Environment side panel with the deps
# 2. Set up an empty bundle directory with a minimal databricks.yml
#    (bundle generate needs one to write into):
mkdir ~/dabs_live_demo && cd ~/dabs_live_demo
cat > databricks.yml <<'EOF'
bundle:
  name: generated_customer_report

include:
  - resources/*.yml      # required — DABs won't auto-include the generated file

targets:
  dev:
    mode: development
    default: true
    workspace:
      host: https://fe-sandbox-zg-aws-sandbox.cloud.databricks.com
EOF

# 3. Generate the job resource from the live job. --key names it.
databricks bundle generate job \
  --existing-job-id 954844862799777 \
  --key customer_report \
  --profile dabs-demo-dev

# 4. Walk through the produced resources/*.job.yml
#    Note: NO environments[] block in the generated YAML — the deps live
#    in the downloaded .ipynb's metadata, not in the bundle.

# 5. Validate, deploy, run from the bundle (all from the same directory):
databricks bundle validate --profile dabs-demo-dev
databricks bundle deploy   --profile dabs-demo-dev
databricks bundle run customer_report --profile dabs-demo-dev

# 6. Clean up the bundle-deployed copy (original job is untouched):
databricks bundle destroy --profile dabs-demo-dev
```

See `bundle_from_existing/README.md` for the full flow + the four places
notebook deps can live and which survive bundle generation.

---

## What this demo deliberately leaves out

- Service-principal-based `run_as` (real prod uses a SP, not a user)
- CI/CD with GitHub Actions + OIDC federation
- Custom Python wheels (the job depends on a PyPI package, not on-repo code)
- Permissions blocks (CAN_VIEW for groups, etc.)
- Multi-task DAGs with `depends_on`
- Pipelines, dashboards, ML resources

That's the bigger story — see `~/isaac/swdev_best_practices/` for an
end-to-end CI/CD-driven version.
