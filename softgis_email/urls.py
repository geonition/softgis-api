# -*- coding: utf-8 -*-
from django.conf.urls.defaults import patterns
from django.conf.urls.defaults import url

urlpatterns = patterns('softgis_email.views',
                       
            url(r'^',
                'email',
                name="api_email"),
        )
