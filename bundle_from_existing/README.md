# bundle_from_existing

Demo flow: **"I already have a job in the Workflows UI — how do I get it
into a bundle?"**

Almost every customer has this. They've been clicking through the Jobs UI
for months and want to move to infrastructure-as-code without rewriting
everything. The Databricks CLI ships a `bundle generate` command for
exactly this case.

## Setup (one-time, already done)

A dummy job called **`existing_say_hello_job`** is sitting in the dev
workspace (`fe-sandbox-zg-aws-sandbox`). It runs a single notebook task
(`say_hello.py`) with two parameters (`greeting`, `name`), a paused weekly
schedule, and serverless compute. The notebook lives at
`/Users/zach.goehring@databricks.com/dabs_demo_existing/say_hello` in the
workspace (imported directly, not bundle-managed — that's the whole point).

**Job ID: `898648320693456`**

Verify any time:

```bash
databricks jobs list --profile dabs-demo-dev | grep existing_say_hello_job
```

## The demo flow

### 1. Show the job in the UI

Workspace → Workflows → click `existing_say_hello_job`. Walk through it:
- one task with notebook + parameters
- a paused schedule
- run history

This is the "before" state — config exists, but only as clicks in the UI.

### 2. Generate bundle YAML from the job

In an empty directory (so the generated files don't collide with anything):

```bash
mkdir generated && cd generated
databricks bundle generate job --existing-job-id <JOB_ID> --profile dabs-demo-dev
```

This produces:

- `databricks.yml` — minimal bundle config
- `resources/<job-name>.job.yml` — the job spec extracted from the live job
- the notebook file(s) the job references, downloaded into `src/`

### 3. Walk through the generated YAML

Open `resources/*.job.yml` next to the workspace UI side-by-side. Show
how every UI setting (parameters, schedule, notifications, task config)
became a line in the YAML.

This is the "aha" moment — the customer can see that their existing
clicked-together job and a bundle-managed job are the same thing,
just expressed differently.

### 4. Refine the generated bundle

Generated YAML is a starting point, not the final form. Typical cleanup:

- Replace the user's email in `run_as` with `${workspace.current_user.userName}`
- Add a `${var.catalog}` variable instead of any hardcoded catalog refs
- Add `targets:` blocks for dev/staging/prod instead of the single workspace
- Add `mode: development` to dev to get auto-pause + per-user prefixes

### 5. Deploy from the bundle

```bash
databricks bundle validate
databricks bundle deploy
```

Open the workspace UI. You'll now see the original job
(`existing_say_hello_job`) **plus** a bundle-deployed copy. Once the
customer is happy that the bundle reproduces the original, they can
delete the original via the UI — the bundle copy takes over.

## Files in this folder

| Path | Purpose |
|---|---|
| `source/say_hello.py` | The notebook the dummy job runs. Imported into the workspace when the job was created. |
| (no `databricks.yml`) | Intentional — this folder is the *starting point*. The bundle gets generated during the demo. |

## What `bundle generate` covers (and doesn't)

**Generates cleanly:**
- jobs, pipelines, dashboards, ML experiments
- notebook source files referenced by the resource
- most task config (parameters, schedules, notifications, dependencies)

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
