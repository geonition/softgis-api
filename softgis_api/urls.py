from django.conf.urls.defaults import patterns
from django.conf.urls.defaults import url

urlpatterns = patterns('api.views',
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
