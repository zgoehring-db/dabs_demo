# Databricks notebook source
# MAGIC %md
# MAGIC # say_hello
# MAGIC
# MAGIC The notebook backing the dummy "existing" job. Deliberately trivial —
# MAGIC the point of the demo is the *bundle generate* flow, not the
# MAGIC notebook's logic.

# COMMAND ----------

dbutils.widgets.text("greeting", "Hello")
dbutils.widgets.text("name", "World")

greeting = dbutils.widgets.get("greeting")
name = dbutils.widgets.get("name")

print(f"{greeting}, {name}!")
print(f"running as: {spark.sql('SELECT current_user()').collect()[0][0]}")
