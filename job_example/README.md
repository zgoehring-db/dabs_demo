# job_example

A serverless job bundle. Walks the customer through:

- bundle anatomy (`databricks.yml`, `include:`, `variables:`, `targets:`)
- the dev → prod target pattern
- declaring a PyPI dependency on a serverless task
- overriding bundle variables per target and at the CLI
- a multi-task DAG (`generate` → `summarize`)
- an hourly schedule (PAUSED by default; dev mode also force-pauses)
- job tags
- a per-target override that attaches a serverless **budget policy** in
  prod only

See `../README.md` for the full demo flow.

## What the job does

Two tasks:

1. **generate** — uses `faker` to write `${var.row_count}` synthetic
   customer rows to `${var.catalog}.${var.schema}.synthetic_customers`.
2. **summarize** — reads that table, appends one row to a `run_log`
   table with timestamp + row counts + averages. Each job run adds one
   row to `run_log` — easy visual confirmation the schedule fires.

```sql
SELECT * FROM ${catalog}.dabs_demo.run_log ORDER BY run_at DESC;
```

## Files

| File | Purpose |
|---|---|
| `databricks.yml` | Bundle identity, variables, targets, prod-only budget policy override |
| `resources/job.yml` | Job resource — tasks, schedule, tags, serverless environment |
| `src/generate_customers.py` | Notebook the `generate` task runs |
| `src/summarize.py` | Notebook the `summarize` task runs |

## Commands

```bash
databricks bundle validate --target dev
databricks bundle deploy   --target dev
databricks bundle run generate_customers --target dev

# Override the catalog for one deploy
databricks bundle deploy --target dev --var catalog=some_other_catalog

# Promote to prod
databricks bundle deploy --target prod
databricks bundle run generate_customers --target prod

# Clean up
databricks bundle destroy --target dev
databricks bundle destroy --target prod
```
