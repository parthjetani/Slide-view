$(document).ready(function() {

	// Bar Chart
	if (document.getElementById('bar-charts') != null) {
		Morris.Bar({
			element: 'bar-charts',
			data: [
				{ y: '2014', a: 100, b: 90 },
				{ y: '2015', a: 75,  b: 65 },
				{ y: '2016', a: 50,  b: 40 },
				{ y: '2017', a: 75,  b: 65 },
				{ y: '2018', a: 50,  b: 40 },
				{ y: '2019', a: 75,  b: 65 },
				{ y: '2020', a: 100, b: 90 }
			],
			xkey: 'y',
			ykeys: ['a', 'b'],
			labels: ['Total Income', 'Total Outcome'],
			lineColors: ['#00c5fb','#0253cc'],
			lineWidth: '3px',
			barColors: ['#00c5fb','#0253cc'],
			resize: true,
			redraw: true
		});
	}
	
	// Line Chart
	if (document.getElementById('line-charts') != null) {
		Morris.Line({
			element: 'line-charts',
			data: [
				{ y: '2014', a: 50, b: 90 },
				{ y: '2015', a: 75,  b: 65 },
				{ y: '2016', a: 50,  b: 40 },
				{ y: '2017', a: 75,  b: 65 },
				{ y: '2018', a: 50,  b: 40 },
				{ y: '2019', a: 75,  b: 65 },
				{ y: '2020', a: 100, b: 50 }
			],
			xkey: 'y',
			ykeys: ['a', 'b'],
			labels: ['Total Sales', 'Total Revenue'],
			lineColors: ['#00c5fb','#0253cc'],
			lineWidth: '3px',
			resize: true,
			redraw: true
		});
	}
		
});