
function get_email(callback)
{
	$.ajax({
	  url: '{% url api_manage_email %}',
	  type: "GET",
	  data: {},
	  success: function(data){
	    callback(data);
	    },
	  error: function(e) { alert(e); }, 
	  dataType: "json"
	});
}

function checkRegexp( o, regexp ) {
  if ( !( regexp.test( o ) ) ) {
     return false;
  }
  else {
    return true;
 }
}

function validate_email(email_address)
{
	if (email_address != null && email_address.length > 6)
	{
	  isEmailValid = checkRegexp( email_address, /^((([a-z]|\d|[!#\$%&'\*\+\-\/=\?\^_`{\|}~]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])+(\.([a-z]|\d|[!#\$%&'\*\+\-\/=\?\^_`{\|}~]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])+)*)|((\x22)((((\x20|\x09)*(\x0d\x0a))?(\x20|\x09)+)?(([\x01-\x08\x0b\x0c\x0e-\x1f\x7f]|\x21|[\x23-\x5b]|[\x5d-\x7e]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(\\([\x01-\x09\x0b\x0c\x0d-\x7f]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF]))))*(((\x20|\x09)*(\x0d\x0a))?(\x20|\x09)+)?(\x22)))@((([a-z]|\d|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(([a-z]|\d|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])*([a-z]|\d|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])))\.)+(([a-z]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])|(([a-z]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])([a-z]|\d|-|\.|_|~|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])*([a-z]|[\u00A0-\uD7FF\uF900-\uFDCF\uFDF0-\uFFEF])))\.?$/i);
   
	  if (!isEmailValid)
	  {
	    //alert ("Email address is not valid.")
	    return false;
	  }
	  else
	  {
	    return true;
	  }
	}
	else
	{
	  //alert ("Email address length should be at least 6 characters.")
	  return false;
  	}
}


function save_email(email_address, callback)
{
	//TO DO
	//move all validations into a file
	
	var email = jQuery.parseJSON(email_address);
	
	
	
	if (!validateEmail(email.email))
	{
	  alert ("Email address is not valid.");
	  return false;
	}

	
	$.ajax({
	  url: '{% url api_manage_email %}',
	  type: "POST",
	  data: email_address,
	  success: function(data)
			{
			    callback(data);
			},
	  error: function(e) { alert(e); }, 
	  dataType: "text"
	});
}

/*
typeString
Default: 'GET'

The type of request to make ("POST" or "GET"), default is "GET". 
Note: Other HTTP request methods, such as PUT and DELETE, can also be used here, but they are not supported by all browsers.
*/
function delete_email(callback)
{
	$.ajax({
	  url: '{% url api_manage_email %}',
	  type: "DELETE",
	  data: {},
	  success: function(data)
			{
			    callback(data);
			},
	  error: function(e) { alert(e); }, 
	  dataType: "text"
	});
}
