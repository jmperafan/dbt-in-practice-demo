{#
    Three sources carry duration in minutes (lessons, matches) or hours
    (court_reservations) inconsistently. One macro, one place to change the
    rounding, instead of every model re-deciding how many decimal places a
    duration gets.
#}
{% macro duration_to_hours(minutes_column, precision=2) %}
    round({{ minutes_column }} / 60.0, {{ precision }})
{% endmacro %}
