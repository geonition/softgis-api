# -*- coding: utf-8 -*-
from django.conf.urls.defaults import patterns
from django.conf.urls.defaults import url

import sys, os

urlpatterns = patterns('softgis_gis.views',
                       
            #feature rest
            url(r'^feature/$',
                'feature',
                name="api_feature"),
               
        )
