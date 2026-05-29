# Databricks notebook source
# MAGIC %md
# MAGIC # Customer Report
# MAGIC
# MAGIC Pretend the customer wrote this notebook a few months ago and has been
# MAGIC running it from the Workflows UI ever since:
# MAGIC
# MAGIC - widgets for `catalog` and `schema` (typical for shared notebooks)
# MAGIC - generates sample customer rows with `faker`
# MAGIC - aggregates by country
# MAGIC - prints a human-readable summary using `humanize`
# MAGIC
# MAGIC Two PyPI dependencies. Neither is in the default serverless runtime,
# MAGIC so the job has them declared in its `environments` block. When we run
# MAGIC `databricks bundle generate job`, that whole spec — notebook + widgets +
# MAGIC dependencies — comes along into YAML.

# COMMAND ----------

dbutils.widgets.text("catalog", "")
dbutils.widgets.text("schema", "existing_demo")

catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")
assert catalog, "catalog parameter is required"

target_table = f"{catalog}.{schema}.customers"

# COMMAND ----------

spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{schema}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 1. Generate sample data with `faker`

# COMMAND ----------

from faker import Faker

fake = Faker()
Faker.seed(42)

rows = [
    (
        i,
        fake.name(),
        fake.country_code(),
        round(fake.pyfloat(min_value=0, max_value=100_000), 2),
    )
    for i in range(500)
]

df = spark.createDataFrame(
    rows,
    schema="customer_id INT, name STRING, country STRING, annual_spend DOUBLE",
)

df.write.mode("overwrite").saveAsTable(target_table)
print(f"wrote {df.count()} rows to {target_table}")

# COMMAND ----------

# MAGIC %md
# MAGIC ## 2. Aggregate top countries

# COMMAND ----------

from pyspark.sql import functions as F

top = (
    spark.table(target_table)
    .groupBy("country")
    .agg(
        F.count("*").alias("n_customers"),
        F.sum("annual_spend").alias("total_spend"),
    )
    .orderBy(F.col("total_spend").desc())
    .limit(10)
    .collect()
)

# COMMAND ----------

# MAGIC %md
# MAGIC ## 3. Pretty-print with `humanize`

# COMMAND ----------

import humanize

print("Top 10 countries by total annual spend:")
print()
for rank, row in enumerate(top, start=1):
    n = humanize.intcomma(row.n_customers)
    spend = humanize.intword(row.total_spend)
    print(f"  {rank:>2}. {row.country}  —  {n} customers, ${spend}")
