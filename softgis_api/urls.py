# -*- coding: utf-8 -*-
from django.conf.urls.defaults import patterns
from django.conf.urls.defaults import url

import sys, os

urlpatterns = patterns('softgis_api.views',
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
            #openid login urls
            url(r'^openid/$',
                'openid_begin',
                name="api_openid_begin"),
            url(r'^openid/complete/$',
                'openid_complete',
                name="api_openid_complete"),
            url(r'^openid/signout/$',
                'openid_signout',
                name="api_openid_signout"),
            

            #feature rest
            url(r'^feature/$',
                'feature',
                name="api_feature"),
                
            #profile rest
            url(r'^profile/$',
                'profile',
                name="api_profile"),
                
            #javascript API for the REST
            url(r'^softgis.js',
                'javascript_api',
                name="api_javascript"),

        )
