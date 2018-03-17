$('#custom-type-selector').on('change', function(){
	$('#no-filters').css('display', 'none');
	var flag = $(this).val() == 'membership';
	$('#student-filters').css('display', flag ? 'block' : '');
	$('#semester-filters').css('display', flag ? '' : 'block');
});