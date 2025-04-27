from django import template
register = template.Library()

@register.filter(name="mul")
def mul(value, arg):
    """Multiply the given value by the given argument."""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return ""
    
@register.filter(name="percentage")
def percentage(value, total):
    """
    Return (value / total) * 100 rounded to an int.
    Safe‑returns 0 on bad input or divide‑by‑zero.
    """
    try:
        return round(float(value) / float(total) * 100)
    except (ZeroDivisionError, ValueError, TypeError):
        return 0
    

@register.filter(name="filter_by")
def filter_by(queryset, arg):
    """
    Usage in template:
        {% load query_filters %}
        {{ User.objects.all|filter_by:"user_type,student"|count }}

    `arg` must be "field,value".
    Returns queryset.filtered(**{field: value}) or queryset.none() on error.
    """
    if queryset is None:
        return queryset

    try:
        field, value = [part.strip() for part in arg.split(",", 1)]
        return queryset.filter(**{field: value})
    except Exception:
        # Bad input or filter failure – return empty set to avoid crashing
        return queryset.none()


@register.filter(name="count")
def count(obj):
    """
    Smart length helper for templates.

    ▸ Uses obj.count() when available (efficient for QuerySets).
    ▸ Falls back to len(obj).
    ▸ Returns 0 on None or non‑countables.

    Usage in template:
        {% load count_tags %}
        {% count some_queryset as total %}
        {{ total }}
    """
    if obj is None:
        return 0
    if hasattr(obj, "count"):
        try:
            return obj.count()
        except Exception:
            pass
    try:
        return len(obj)
    except (TypeError, AttributeError):
        return 0