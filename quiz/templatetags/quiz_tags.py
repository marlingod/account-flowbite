
# quiz/templatetags/quiz_tags.py
from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key, name="get_item"):
    """Get an item from a dictionary by key
    
    Usage: {{ dictionary|get_item:key }}
    Example: {{ my_dict|get_item:'key' }}
    """
    if dictionary is None:
        return None
    return dictionary.get(key)


@register.filter
def filter_by(queryset, filter_string):
    """Filter a queryset by a field and value
    
    Usage: {{ queryset|filter_by:"field_name,value" }}
    Example: {{ question_list|filter_by:"question_type,multiple_choice" }}
    """
    if not filter_string or ',' not in filter_string:
        return queryset
    
    field, value = filter_string.split(',', 1)
    
    # If we're filtering a dictionary of querysets by key
    if isinstance(queryset, dict):
        try:
            return queryset.get(field)
        except KeyError:
            return None
    
    # Handle boolean values
    if value.lower() == 'true':
        value = True
    elif value.lower() == 'false':
        value = False
    elif value.lower() == 'none':
        value = None
    
    # Create the filter
    filter_kwargs = {field: value}
    
    try:
        return queryset.filter(**filter_kwargs)
    except (ValueError, TypeError):
        return queryset


@register.filter
def percentage(value, total):
    """Calculate the percentage of value to total
    
    Usage: {{ value|percentage:total }}
    Example: {{ correct_count|percentage:total_count }} -> percentage
    """
    try:
        return float(value) / float(total) * 100
    except (ValueError, ZeroDivisionError, TypeError):
        return 0


@register.filter
def dictsortreversed(queryset, key):
    """Sort a queryset in reverse order by a given field
    
    Usage: {{ queryset|dictsortreversed:"field_name" }}
    Example: {{ attempts|dictsortreversed:"started_at" }}
    """
    if queryset:
        try:
            return sorted(queryset, key=lambda x: getattr(x, key), reverse=True)
        except (AttributeError, TypeError):
            return queryset
    return queryset