# -*- coding: utf-8 -*-
from django.conf.urls.defaults import patterns
from django.conf.urls.defaults import url

import sys, os

urlpatterns = patterns('softgis_profile.views',
                       
            #profile rest
            url(r'^profile/$',
                'profile',
                name="api_profile"),

        )
