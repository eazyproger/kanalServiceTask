from django.shortcuts import render

from .models import Orders


def main_view(request):
    queryset = Orders.objects.values().order_by('id')

    total = 0
    for row in queryset.values_list('dollar_price'):
        total += row[0]

    context = {
        'orders': list(queryset),
        'total': total
    }

    return render(request, 'orders/main_page.html', context)
