function get_email(callback_function){
     
     add_CSRF_token_in_request_header();
      
	$.ajax({
	  url: '{% url api_manage_email %}',
	  type: "GET",
	  data: {},
	  success: function(data){
			if(callback_function !== undefined) {
			    callback_function(data);
			}
	    },
	  error: function(e) {
                      if(callback_function !== undefined) {
                          callback_function(e);    
                      }
        },  
	  dataType: "json"
	});
}


function save_email(email_address, callback_function){

	var email = jQuery.parseJSON(email_address);
	
	if (!validate_email(email.email)){
	   if(callback_function !== undefined) {
              var e = {"status" : 400, "responseText" : "Email address is invalid"}; 
              callback_function(e);    
       }
	}

	$.ajax({
	  url: '{% url api_manage_email %}',
	  type: "POST",
	  data: email_address,
	  success: function(data){
				if(callback_function !== undefined) {
				    callback_function(data);
				}
			},
	   error: function(e) {
                      if(callback_function !== undefined) {
                          callback_function(e);    
                      }
       },  
	  dataType: "text"
	});
}

/*
typeString
Default: 'GET'

The type of request to make ("POST" or "GET"), default is "GET". 
Note: Other HTTP request methods, such as PUT and DELETE, can also be used here, but they are not supported by all browsers.
*/
function delete_email(callback_function){
	$.ajax({
	  url: '{% url api_manage_email %}',
	  type: "DELETE",
	  data: {},
	  success: function(data){
				if(callback_function !== undefined) {
				    callback_function(data);	
				}	
	   },
       error: function(e) {
                      if(callback_function !== undefined) {
                          callback_function(e);    
                      }
       },  
	  dataType: "text"
	});
}
