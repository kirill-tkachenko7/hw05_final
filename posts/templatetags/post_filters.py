from django import template
from django.template.defaultfilters import stringfilter

register = template.Library()


@register.filter
def addclass(field, css):
    return field.as_widget(attrs={'class': css})

@register.filter
def russianplural(value):
    value = int(value)
    if value % 10 == 1 and value % 100 != 11:
        return 0
    elif value % 10 >= 2 and value % 10 <= 4 and (value % 100 < 12 or value % 100 > 14):
        return 1
    else: # value % 10 == 0 or (value % 10 >= 5 and value % 10 <= 9) or (value % 100 >= 11 and value % 100 <= 14):
        return 2
    # else:
    #     return 3