from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def book_status_badge(book):
    """
    Returns an HTML span badge based on book availability
    """
    if book.available_copies > 0:
        return mark_safe('<span class="badge bg-success mb-2">Available</span>')
    else:
        return mark_safe('<span class="badge bg-danger mb-2">Fully Borrowed</span>')