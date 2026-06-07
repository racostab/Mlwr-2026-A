from django.urls import path

from . import servicios

urlpatterns = [
    path('',         servicios.index,   name='index'),
    path('history/', servicios.history, name='history'),
    path('rules/',   servicios.rules,   name='rules'),
    path('stats/',   servicios.stats,   name='stats'),
    path('status/',  servicios.status,  name='status'),
    path('docs/',    servicios.docs,    name='docs'),
]
