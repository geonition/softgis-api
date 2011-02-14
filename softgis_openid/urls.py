# -*- coding: utf-8 -*-
from django.conf.urls.defaults import patterns
from django.conf.urls.defaults import url

import sys, os

urlpatterns = patterns('softgis_openid.views',
                       
            #openid login urls
            url(r'^openid/$',
                'openid_begin',
                name="api_openid_begin"),
            url(r'^openid/complete/$',
                'openid_complete',
                name="api_openid_complete"),

        )
