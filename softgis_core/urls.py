# -*- coding: utf-8 -*-
from django.conf.urls.defaults import patterns
from django.conf.urls.defaults import url

import sys, os

urlpatterns = patterns('softgis_core.views',
            url(r'^register/$',
                'register',
                name="api_register"),
               
            url(r'^newpassword/$',
                'new_password',
                name="api_new_password"),
            url(r'^changepassword/$',
                'change_password',
                name="api_change_password"),

            url(r'^login/$',
                'login',
                name="api_login"),
            url(r'^logout/$',
                'logout',
                name="api_logout"),
                
            #javascript API for the REST
            url(r'^softgis.js',
                'javascript_api',
                name="api_javascript"),
            
            #javascript API for the REST
            url(r'^test.html',
                'test_api',
                name="api_test"),

        )
