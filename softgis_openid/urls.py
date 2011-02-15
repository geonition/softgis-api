# -*- coding: utf-8 -*-
from django.conf.urls.defaults import patterns
from django.conf.urls.defaults import url

urlpatterns = patterns('softgis_openid.views',
                       
            #openid login urls
            url(r'^',
                'openid_begin',
                name="api_openid_begin"),
            url(r'^complete/$',
                'openid_complete',
                name="api_openid_complete"),

        )
