# Create your views here.


#openid authentication views
def openid_begin(request):
    """
    This function takes the openid_provider url as an
    get arguments and proceedes with the openid authentication
    prcedure
    """
    openid_op = request.GET['openid_provider']
    answ = openid_auth.preAuthenticate(openid_op,
                                        settings.OPENID_COMPLETE_URL,
                                        sreg = ((), ()),
                                        ax = ((), ())
                                        )

    request.session['id_claim'] = answ[1]
    return answ[0]
    
def openid_complete(request):
    """
    This function takes the response from the openid provider

    if the user has not logged in before with the openid it will register a
    user and connect the user with the openid claim

    if the user has logged in before then the same user is authenticated and logged
    in
    """
    user = django_authenticate(request=request,
                                claim=request.GET['openid.identity'])
  
    if(user.is_anonymous()):
        search_user_name = True
        i = 0
        while(search_user_name):
            try:
                username = "anonymous-" + str(i)
                new_user = User.objects.create_user(username=username,
                                                    password="no-pass",
                                                    email="")
                new_user.save()
                openid_auth.linkOpenID(new_user, request.GET['openid.identity'])
                new_user = django_authenticate(username=username,
                                                password="no-pass")
                search_user_name = False
            except IntegrityError:
                i = i + 1
                django.db.connection.close()
                
        django_login(request, new_user)
        
        new_user.set_unusable_password()
        new_user.save()
        
    else:
        django_login(request, user)
    
    return HttpResponseRedirect(getattr(settings, "OPENID_REDIRECT_URL", "/"))
    