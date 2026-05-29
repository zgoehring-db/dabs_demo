# bundle_from_existing

Demo flow: **"I already have a job in the Workflows UI — how do I get it
into a bundle?"**

Almost every customer has this. They opened a notebook in the workspace,
attached some pip dependencies, and clicked **Schedule** to make a job
out of it. Now they want to move to infrastructure-as-code without
rewriting anything. The Databricks CLI ships a `bundle generate` command
for exactly this case.

## The pre-existing job (already set up in dev)

A job called **`existing_job_customer_report_notebook`** lives in the dev
workspace (`fe-sandbox-zg-aws-sandbox`). It's deliberately
customer-realistic — every piece matches what someone would actually have
in production:

- A real **`.ipynb` notebook** created in the workspace UI:
  `/Users/zach.goehring@databricks.com/dabs_demo/bundle_from_existing/source/customer_report_notebook`
- **Notebook widgets** for `catalog` and `schema` (the typical pattern for
  a shared notebook running across environments)
- **Two PyPI dependencies** — `faker` and `humanize` — attached via the
  notebook's **Environment side panel** (not `%pip install`, not job-level
  `environments[]`). The deps live in the notebook's metadata.
- A job created from that notebook with **no job-level `environment_key`**,
  so the runtime auto-uses the notebook's environment

**Job ID: `954844862799777`**

Why this shape matters: when `bundle generate job` runs against this job,
the downloaded notebook is `.ipynb` and its environment metadata travels
with it. The generated `job.yml` has *no* `environments[]` block —
because the job itself doesn't need one. Deps follow the notebook.

## The demo flow

### 1. Show the job in the UI

Workspace → Workflows → `existing_job_customer_report_notebook`. Walk through:
- one task, runs the `customer_report_notebook` notebook
- base_parameters: `catalog`, `schema`
- run history (one successful run)

This is the "before" state — config exists, but only as clicks in the UI.

### 2. Open the notebook itself

Click into the notebook. Show the **Environment** side panel on the right
— `faker` and `humanize` listed there with no `%pip install` in any cell.
Walk through the cells to show widgets at the top, then `import` lines
that depend on the side-panel deps.

This is the part customers always ask about: *"if I bundle this, do my
deps come along?"* — and yes, because they're in the notebook's metadata,
not free-floating.

### 3. Generate bundle YAML from the job

In an empty directory:

```bash
mkdir /tmp/generated && cd /tmp/generated
databricks bundle generate job --existing-job-id 954844862799777 --profile dabs-demo-dev
```

This produces:

- `databricks.yml` — minimal bundle config
- `resources/<job-name>.job.yml` — the job spec extracted from the live job
- the notebook the job references, downloaded as `.ipynb` into `src/`
  (with its Environment side-panel metadata intact)

### 4. Walk through what got captured

Open the generated files side-by-side with the workspace UI:

- Task definition with notebook path → captured
- `base_parameters` (widget defaults from the job) → captured
- **No `environments[]` block** in the generated YAML → because the job
  didn't have one. The deps live in the `.ipynb` instead.
- The downloaded `.ipynb` opens fine in any Jupyter viewer and carries
  the environment metadata Databricks reads at runtime.

This is the "aha" — *deps follow the notebook*. Customers worry that
moving to bundles means re-declaring every dependency in YAML. It
doesn't.

### 5. Refine the generated bundle

Generated YAML is a starting point. Typical cleanup before merging:

- Replace the hardcoded user email in paths with workspace-relative refs
- Add `${var.catalog}` instead of the hardcoded `catalog` value in
  `base_parameters`
- Add `targets:` blocks for dev/staging/prod
- Add `mode: development` to dev for auto-pause + per-user prefixes

### 6. Deploy from the bundle

```bash
databricks bundle validate
databricks bundle deploy
```

Open the workspace UI. You'll now see the original job
(`existing_job_customer_report_notebook`) **plus** a bundle-deployed copy.
Once the customer is happy the bundle reproduces the original, they can
delete the original in the UI — the bundle copy takes over.

## What's intentionally NOT in this folder

There's no `databricks.yml` here. There's no local notebook file. That's
on purpose:

- The customer's starting point is **a notebook in the workspace, owned
  by them, that they've been editing for months**. The repo doesn't
  pre-stage a copy.
- `bundle generate` is what produces the local files for the first time,
  during the demo.

If you want to look at the notebook's source before running the demo,
open it in the workspace at the path above, or just `bundle generate`
once and open the downloaded `.ipynb`.

## Where notebook-task dependencies can live

There are four real options. Only one of them is what this demo uses:

| # | Mechanism | Persists in | Captured by `bundle generate` |
|---|---|---|---|
| 1 | Job's `environments[].spec.dependencies` (via `environment_key`) | `databricks.yml` / `*.job.yml` | ✅ yes |
| 2 | **Notebook's own Environment side panel** ← **what this demo uses** | `.ipynb` metadata | ✅ yes (notebook file carries the metadata) |
| 3 | `%pip install` inside the notebook | notebook source content | ⚠️ source travels but the install is brittle |
| 4 | Cluster libraries (classic compute only) | `job_clusters[].new_cluster.libraries` | ✅ yes |

Most customers start with option 2 — they configure the Environment panel
once and click Schedule. That's the path this demo replicates. Once
they're comfortable with bundles, some teams shift toward option 1
(job-level env) because it keeps all the config in YAML — same place as
the rest of the bundle. Both are equally valid; neither requires
rewriting the notebook.

## The mental model

`bundle generate` gets you from "clicked-together job + notebook in
workspace" to "deployable single-target bundle" in one command. Going
from there to "production-grade bundle with dev/staging/prod, variables,
CI/CD" is manual but mechanical.

The deps story specifically: if the customer used the Environment panel
(option 2), nothing changes — the deps stay with the notebook. If they
used `%pip install` (option 3), they should move those into the
Environment panel *before* bundle-generating, otherwise the generated
bundle deploys but tasks fail with `ModuleNotFoundError`.
