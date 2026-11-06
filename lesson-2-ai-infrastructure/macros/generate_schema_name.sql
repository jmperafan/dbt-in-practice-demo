{#
    One macro, every target. Overriding dbt's default generate_schema_name
    is what turns "dev", "ci", and "prod" from three labels into three real,
    isolated sets of tables — see ../lesson-1-setup/README.md.

        dev target,  +schema: staging  -> dev_staging
        ci  target,  +schema: staging  -> ci_pr_123_staging
        prod target, +schema: staging  -> staging   (clean, no prefix)

    A model with no custom +schema config (none of this project's models,
    but worth knowing) always resolves to the target's own base schema,
    untouched.
#}
{% macro generate_schema_name(custom_schema_name, node) -%}
    {%- set default_schema = target.schema -%}
    {%- if custom_schema_name is none -%}
        {{ default_schema }}
    {%- elif target.name == 'prod' -%}
        {{ custom_schema_name | trim }}
    {%- else -%}
        {{ default_schema }}_{{ custom_schema_name | trim }}
    {%- endif -%}
{%- endmacro %}
