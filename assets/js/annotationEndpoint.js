(function($) {
  $.LocalAnnotationEndpoint = function(options) {
  	jQuery.extend(
      this,
      {
        token: null,
        uri: null,
        url: options.url,
        dfd: null,
        annotationsList: [],
        idMapper: {}
      },
      options
    );
    this.init();
  };

  $.LocalAnnotationEndpoint.prototype = {
    init: function() {
      // NOP
    },

    search: function(options) {
    	var _this = this;
      _this.uri = options.uri;
    	_this.annotationsList = [];
    	var id = options['uri'].split('/');
      id = id.filter(word => word.match(/(?=.*[0-9]$)/gm)).join("-")
    	for (var key in this.allannotations){
    		var listid = id.replace(/_/g, '-').replace(/:/g, "").replace(".json", "").replace(".", "") + '-list';
    		if (listid === key) {
    			var resources = JSON.parse(this.allannotations[key].output).resources;
	    		resources.forEach(function(a) {
	              a.endpoint = _this;
	            });
    			_this.annotationsList = resources;
    		}
    	}
      _this.dfd.resolve(false);
    },

    deleteAnnotation: function(annotationID, returnSuccess, returnError) {
      split = annotationID.split("/");
      ID = split[split.length - 1];
      jQuery.ajax({
        url: this.server + 'delete_annotations/',
        type: "DELETE",
        contentType: 'application/json',
        data: JSON.stringify({'id':ID, 'listuri': this.uri}),
        dataType: "json",
        success: function(data) {
          returnSuccess();
        },
        error: function() {
          console.log('error')
          returnError();
        }
      });
    },

    update: function(annotation, returnSuccess, returnError) {
      split = annotation["@id"].split("/");
      ID = split[split.length - 1];
      var _this = this;
      delete annotation.endpoint;
      var senddata = {'json': annotation,'id': ID, 'origin_url': this.origin_url}
      jQuery.ajax({
        url: _this.server + 'update_annotations/',
        type: "POST",
        dataType: "json",
        data: JSON.stringify(senddata),
        contentType: "application/json; charset=utf-8",
        success: function(data) {
          data.endpoint = _this;
          returnSuccess(data);
        },
        error: function() {
          returnError();
        }
      });
      annotation.endpoint = this;
    },

    create: function(annotation, returnSuccess, returnError) {
      var _this = this;
      listdata = _this.annotationsList.map(element => _.omit(element, 'endpoint'));
      var senddata = {'json': annotation, 'listdata': listdata, 'index': listdata.length, 'origin_url': _this.origin_url}
      jQuery.ajax({
        url: this.server + 'create_annotations/',
        type: "POST",
        dataType: "json",
        data: JSON.stringify(senddata),
        contentType: "application/json; charset=utf-8",
        success: function(data) {
          data.endpoint = _this;
          returnSuccess(data);
        },
        error: function() {
          returnError();
        }
      });
    },

    set: function(prop, value, options) {
      if (options) {
        this[options.parent][prop] = value;
      } else {
        this[prop] = value;
      }
    },
    userAuthorize: function(action, annotation) {
      return true; // allow all
    }
  };
})(Mirador);
