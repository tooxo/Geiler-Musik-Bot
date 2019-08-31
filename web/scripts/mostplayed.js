$.ajax({
    type: 'GET',
    url: 'http/mongo_most',
    success: function (msg) {
        msg = msg.split("'").join('"');
        let mm = JSON.parse(msg);

        mm = mm.sort(function (a, b) {
            const keyA = a.value,
                keyB = b.value;
            if (keyA < keyB) return 1;
            if (keyA > keyB) return -1;
            return 0;
        });
        let label = [];
        let values = [];
        for (let x = 0; x <= 10; x++) {
            try {
                values.push(mm[x].value);
                label.push(mm[x].name);
            } catch {
                break
            }
        }
        const ctx = document.getElementById("mostplayed_chart");
        const myChart = new Chart(ctx, {
            type: 'horizontalBar',
            data: {
                labels: label,
                datasets: [{
                    label: 'Number of Plays',
                    data: values,
                    backgroundColor: [
                        'rgba(255, 99, 132, 0.2)',
                        'rgba(54, 162, 235, 0.2)',
                        'rgba(255, 206, 86, 0.2)',
                        'rgba(75, 192, 192, 0.2)',
                        'rgba(153, 102, 255, 0.2)',
                        'rgba(255, 159, 64, 0.2)',
                        'rgba(255, 99, 132, 0.2)',
                        'rgba(54, 162, 235, 0.2)',
                        'rgba(255, 206, 86, 0.2)',
                        'rgba(75, 192, 192, 0.2)',
                        'rgba(153, 102, 255, 0.2)',
                        'rgba(255, 159, 64, 0.2)'
                    ],
                    borderColor: [
                        'rgba(255,99,132,1)',
                        'rgba(54, 162, 235, 1)',
                        'rgba(255, 206, 86, 1)',
                        'rgba(75, 192, 192, 1)',
                        'rgba(153, 102, 255, 1)',
                        'rgba(255, 159, 64, 1)',
                        'rgba(255,99,132,1)',
                        'rgba(54, 162, 235, 1)',
                        'rgba(255, 206, 86, 1)',
                        'rgba(75, 192, 192, 1)',
                        'rgba(153, 102, 255, 1)',
                        'rgba(255, 159, 64, 1)'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: false,
                scales: {
                    xAxes: [{
                        ticks: {
                            maxRotation: 90,
                            minRotation: 80,
                            beginAtZero: true
                        }
                    }]
                }
            }
        });
    }
});
