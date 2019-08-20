function make_embed_code(id){
	if ($("#" + id + "_embeditem").css("display") == 'none'){
    $("#" + id + "_embeditem").css("display", "flex")
    $("#" + id + "_button").html("Hide embed code")
  } else {
    $("#" + id + "_embeditem").css("display", "none")
    $("#" + id + "_button").html("Show embed code")
  }
}

function copytoclipboard(id) {
	var copyText = document.getElementById(id);
	copyText.select();
	document.execCommand("copy");
	var tooltip_id = id.replace("_embedcode", "_tooltip")
	var tooltip = document.getElementById(tooltip_id);
  tooltip.innerHTML = "Copied!";
}

function outFunc(id) {
  var tooltip = document.getElementById(id);
  tooltip.innerHTML = "Copy to clipboard";
}
