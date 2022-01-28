// 模拟后台接口
function getData(params) {
	var data = [
		{id: 1, name: '小王', age: 10},
		{id: 2, name: '当', age: 23},
		{id: 3, name: '节点', age: 12},
		{id: 4, name: '科二', age: 23},
		{id: 5, name: '开心', age: 44},
		{id: 6, name: '为', age: 12},
		{id: 7, name: '看我', age: 22},
		{id: 8, name: '看', age: 43},
		{id: 9, name: '考虑', age: 15},
		{id: 10, name: '为额', age: 18},
		{id: 11, name: '熊', age: 32},
		{id: 12, name: '下', age: 51},
		{id: 13, name: '前往', age: 23},
		{id: 14, name: '我去', age: 28},
		{id: 15, name: '问', age: 36},
		{id: 16, name: '跳', age: 46},
		{id: 17, name: '欧文', age: 31}
	]

	var start = (params.current - 1) * params.size;
	var end = params.current *params.size;
	
	return {
		total: data.length,
		list: data.splice( (params.current - 1) * params.size, params.size )
	}
}

// 设置tbody的html
function setTbody (arr) {
	var html = '';
	for (var i = 0; i < arr.length; i++) {
		var item = arr[i];
		html += '<tr><td>' + item.id + '</td><td>' + item.name + '</td><td>' + item.age + '</td></tr>';
	}
	$('.tbody').html(html);
}



