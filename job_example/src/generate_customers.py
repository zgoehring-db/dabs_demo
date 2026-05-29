# Databricks notebook source
# MAGIC %md
# MAGIC # generate_customers
# MAGIC
# MAGIC The job's only task. Uses `faker` (installed by the serverless
# MAGIC environment spec in `resources/job.yml`) to generate synthetic
# MAGIC customer rows, then writes them to `${catalog}.${schema}.synthetic_customers`.
# MAGIC
# MAGIC Parameters come from the bundle's variables:
# MAGIC - `catalog` — set per target in `databricks.yml`, overridable at the CLI
# MAGIC - `schema` — defaults to `dabs_demo`
# MAGIC - `row_count` — defaults to 1000

# COMMAND ----------

dbutils.widgets.text("catalog", "")
dbutils.widgets.text("schema", "dabs_demo")
dbutils.widgets.text("row_count", "1000")

catalog = dbutils.widgets.get("catalog")
schema = dbutils.widgets.get("schema")
row_count = int(dbutils.widgets.get("row_count"))

assert catalog, "catalog parameter is required"
target = f"{catalog}.{schema}.synthetic_customers"
print(f"writing {row_count} rows to {target}")

# COMMAND ----------

# Make sure the schema exists; safe to re-run.
spark.sql(f"CREATE SCHEMA IF NOT EXISTS {catalog}.{schema}")

# COMMAND ----------

# faker is installed by the serverless environment spec, not %pip install.
from faker import Faker

fake = Faker()
Faker.seed(42)

rows = [
    (
        i,
        fake.name(),
        fake.email(),
        fake.country_code(),
        round(fake.pyfloat(min_value=0, max_value=100000), 2),
    )
    for i in range(row_count)
]

df = spark.createDataFrame(
    rows,
    schema="customer_id INT, name STRING, email STRING, country STRING, annual_spend DOUBLE",
)

df.write.mode("overwrite").saveAsTable(target)

# COMMAND ----------

n = spark.table(target).count()
print(f"wrote {n} rows to {target}")
display(spark.table(target).limit(10))
