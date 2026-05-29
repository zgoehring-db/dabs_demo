# Databricks notebook source
# MAGIC %md
# MAGIC # summarize
# MAGIC
# MAGIC Second task in the `generate_customers` job. Reads the table that the
# MAGIC first task just wrote, computes a tiny per-run summary row, and
# MAGIC appends it to `${catalog}.${schema}.run_log`.
# MAGIC
# MAGIC One row per run, with a timestamp. Run the job twice and you'll see
# MAGIC two rows in `run_log` — easy visual confirmation that the bundle's
# MAGIC schedule + DAG actually fire.

# COMMAND ----------

dbutils.widgets.text("catalog", "")
dbutils.widgets.text("schema", "dabs_demo")
dbutils.widgets.text("source_table", "synthetic_customers")
dbutils.widgets.text("log_table", "run_log")
dbutils.widgets.text("bundle_target", "")

catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")
source_table = dbutils.widgets.get("source_table")
log_table = dbutils.widgets.get("log_table")
bundle_target = dbutils.widgets.get("bundle_target")

assert catalog, "catalog parameter is required"

source = f"{catalog}.{schema}.{source_table}"
log = f"{catalog}.{schema}.{log_table}"

# COMMAND ----------

# Create the log table on first run. Idempotent thanks to IF NOT EXISTS.
spark.sql(f"""
    CREATE TABLE IF NOT EXISTS {log} (
        run_at TIMESTAMP,
        bundle_target STRING,
        source_table STRING,
        row_count BIGINT,
        unique_countries BIGINT,
        avg_annual_spend DOUBLE
    )
""")

# COMMAND ----------

from pyspark.sql import functions as F

summary = (
    spark.table(source)
    .agg(
        F.current_timestamp().alias("run_at"),
        F.lit(bundle_target).alias("bundle_target"),
        F.lit(source).alias("source_table"),
        F.count("*").alias("row_count"),
        F.countDistinct("country").alias("unique_countries"),
        F.round(F.avg("annual_spend"), 2).alias("avg_annual_spend"),
    )
)

summary.write.mode("append").saveAsTable(log)

# COMMAND ----------

# Show the latest few entries so the run logs have something to look at.
display(spark.table(log).orderBy(F.col("run_at").desc()).limit(5))
