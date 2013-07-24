$(document).ready(function() {
	
	$('.day_header').click(function() {
		$(this).parent().find('.body').slideToggle(); 
	});
	
	$(".day_header:not(:last)").click();
	
	var pps = 0;
	var audio = $('<audio>', {
		controls: 'controls',
		id: 'audiotag',
		preload: 'auto'});
	audio.appendTo('#playerbody');
	audio.bind('timeupdate', function() {
		var tag = audio.get(0);
		var progress = tag.currentTime;
		var prog2 = tag.duration;
		for (var i=0; i<window.txlens.length; i++) {
			if (progress < window.txlens[i]) {
				break;
			}
		}
		var txstart = window.txstarts[i];
		var prevtxlen = 0;
		if (i > 0) prevtxlen = window.txlens[i-1];
		$("#redline").css('left',((window.pps * (progress - prevtxlen))+txstart)+'px');
	});
});

function player(date,time){
		var audiotag = $('#audiotag').get(0);
		var file = "output/"+date+"/rec"+time+".ogg";
		audiotag.setAttribute('src',file);
		audiotag.load();
		audiotag.play();
		//$('#audiotag').bind("load",function() {
		//});
		
		$("#Player").html("Player - "+file);
		//timeline.py?20120213-0010
		$.getJSON('timeline/'+date+"-"+time,function(data){
			$("#playerlist").html(data["timebar"]);
			window.pps = data["pps"];
			window.txlens = data["lengths"];
			window.txstarts = data["starts"];
		});
		$.getJSON('details/'+date+time,function(data){
			$("#filecomments").html('<form action="details/update" method="post" id="commentform"><input type="hidden" name="datetime" value="'+date+time+'"><textarea class="tacomments" name="tac" rows="2" cols="80">' + data["comment"] + '</textarea><br/><input type="submit" value="Update"> Last update by ' + data["user"] + '</form>');
			$("#commentform").submit(function(event) {
				event.preventDefault();
				data = $(this).serialize();
				$.ajax({url: 'details/update',
					 data: data,
									  type: 'POST',
									  success: function(data) { alert(data['message']); },
									  dataType: 'json',
									});
			});
		});
	}

	