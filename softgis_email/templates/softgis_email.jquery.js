function get_email(callback){
     
     add_CSRF_token_in_request_header();
      
	$.ajax({
	  url: '{% url api_manage_email %}',
	  type: "GET",
	  data: {},
	  success: function(data){
			if(callback !== undefined) {
			    callback(data);
			}
	    },
	  error: function(e) { alert(e); }, 
	  dataType: "json"
	});
}


function save_email(email_address, callback){
	var email = jQuery.parseJSON(email_address);
		
	if (!validate_email(email.email)){
	  alert ("Email address is not valid.");
	  return false;
	}

	$.ajax({
	  url: '{% url api_manage_email %}',
	  type: "POST",
	  data: email_address,
	  success: function(data){
				if(callback !== undefined) {
				    callback(data);
				}
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
function delete_email(callback){
	$.ajax({
	  url: '{% url api_manage_email %}',
	  type: "DELETE",
	  data: {},
	  success: function(data){
				if(callback !== undefined) {
				    callback(data);	
				}	
			},
	  error: function(e) { alert(e); }, 
	  dataType: "text"
	});
}
