# bundle_from_existing

Demo flow: **"I already have a job in the Workflows UI — how do I get it
into a bundle?"**

Almost every customer has this. They've been clicking through the Jobs UI
for months and want to move to infrastructure-as-code without rewriting
everything. The Databricks CLI ships a `bundle generate` command for
exactly this case.

## Setup (one-time, already done)

A pre-existing job called **`existing_customer_report_job`** lives in the
dev workspace (`fe-sandbox-zg-aws-sandbox`). It's deliberately
customer-realistic:

- A **notebook task** (not a `.py` file in a repo — a real notebook the
  customer created in the workspace UI months ago)
- **Widgets** for `catalog` and `schema` — the typical pattern for a
  notebook shared across environments
- Two **PyPI dependencies** in the job's serverless environment:
  - `faker` — generates sample customer rows
  - `humanize` — formats the report output
- A **paused weekly schedule** (Monday 7am) — common production pattern
- **Notebook lives** at
  `/Users/zach.goehring@databricks.com/dabs_demo_existing/customer_report`
  in the workspace (imported directly, not bundle-managed — that's the
  whole point)

**Job ID: `898648320693456`**

Verify any time:

```bash
databricks jobs list --profile dabs-demo-dev | grep existing_customer_report_job
```

## The demo flow

### 1. Show the job in the UI

Workspace → Workflows → click `existing_customer_report_job`. Walk through it:
- one task, runs the `customer_report` notebook
- widgets / base_parameters: `catalog`, `schema`
- a paused weekly schedule
- the `Environment` block: `faker`, `humanize`
- run history (one successful run already there)

This is the "before" state — config exists, but only as clicks in the UI.

### 2. Open the notebook itself

Click the notebook from the task. Show the customer what they wrote:
- widget definitions at the top
- `from faker import Faker` and `import humanize` — both PyPI deps
- a few cells of generate → aggregate → print

This is the kind of notebook every customer has. The deps + widgets are
the "are they covered?" question they care about.

### 3. Generate bundle YAML from the job

In an empty directory (so the generated files don't collide with anything):

```bash
mkdir /tmp/generated && cd /tmp/generated
databricks bundle generate job --existing-job-id 898648320693456 --profile dabs-demo-dev
```

This produces:

- `databricks.yml` — minimal bundle config
- `resources/<job-name>.job.yml` — the job spec extracted from the live job
- the notebook file(s) the job references, downloaded into `src/`

### 4. Walk through what got captured

Open `resources/*.job.yml` next to the workspace UI side-by-side:

- task definition with notebook path → captured
- base_parameters (widgets) → captured
- `environments` block with both deps → **captured cleanly**
- schedule + pause status → captured
- email notifications → captured
- the notebook source itself → downloaded to `src/`

This is the "aha" moment — the customer can see that *everything* they
configured in the UI, including PyPI deps for notebook tasks, came along
into YAML. No re-work.

### 5. Refine the generated bundle

Generated YAML is a starting point, not the final form. Typical cleanup:

- Replace hardcoded user email in `run_as` / `notebook_path` with
  `${workspace.current_user.userName}` (or a workspace files path)
- Add a `${var.catalog}` variable instead of the hardcoded catalog in
  `base_parameters`
- Add `targets:` blocks for dev/staging/prod instead of the single workspace
- Add `mode: development` to dev to get auto-pause + per-user prefixes

### 6. Deploy from the bundle

```bash
databricks bundle validate
databricks bundle deploy
```

Open the workspace UI. You'll now see the original job
(`existing_customer_report_job`) **plus** a bundle-deployed copy. Once the
customer is happy that the bundle reproduces the original, they can
delete the original via the UI — the bundle copy takes over.

## Files in this folder

| Path | Purpose |
|---|---|
| `source/customer_report.py` | The notebook source the customer wrote. Imported into the workspace when the job was created. Local copy lives here for git history; the workspace copy is what the job runs. |
| (no `databricks.yml`) | Intentional — this folder is the *starting point*. The bundle gets generated during the demo. |

## What `bundle generate` covers (and doesn't)

**Generates cleanly:**
- jobs, pipelines, dashboards, ML experiments
- notebook source files referenced by the resource (downloaded automatically)
- task config: parameters/widgets, schedules, notifications, retries
- **serverless `environments[]` with PyPI deps** ← the notebook-task dep story
- email + webhook notifications

**Doesn't cover (you add manually):**
- variables — generated YAML has hardcoded values where vars should be
- multi-target configs — generated for one workspace; you split it
- permissions blocks
- artifact builds (wheels)
- secrets refs (you'll see literal references; rewrite to `${secrets/...}`)

The mental model: `bundle generate` gets you from "clicked-together job"
to "deployable single-target bundle" in one command. Going from there to
"production-grade bundle with dev/staging/prod, variables, CI/CD" is
manual but mostly mechanical.

## A note on notebook-task deps specifically

For *notebook tasks* (not python_wheel_task / python_task), Databricks
has three places dependencies can come from:

1. **`environments[].spec.dependencies`** in the job spec (what we use here).
   Captured by `bundle generate`. Recommended.
2. **`%pip install` magic commands inside the notebook itself.** *Not*
   captured by `bundle generate` — it grabs the notebook contents but
   doesn't reason about them. If a generated bundle deploys but tasks
   fail with `ModuleNotFoundError`, look here first.
3. **Cluster libraries** (only on classic compute, not serverless).
   Captured if the job uses a `job_cluster_key` with libraries declared.

Moral: if you're going to bundle-ize an existing notebook task, get the
deps into the job's `environments[]` block first. `%pip install` works
when clicking around, but doesn't survive the bundle round-trip.
