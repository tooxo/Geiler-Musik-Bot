$.ajax({
  type: 'GET',
  url: 'http/mongo_response',
  success: function(msg) {
    msg = msg.split("'").join('"');
    let mm = JSON.parse(msg);
    mm = mm.sort(function(a, b){
        const keyA = new Date(a.x),
            keyB = new Date(b.x);
        if(keyA < keyB) return -1;
    if(keyA > keyB) return 1;
    return 0;
    });

      const canvas = document.getElementById('loadtime_chart').getContext('2d');
      const options = {
          type: 'scatter',
          data: {
              datasets: [{
                  label: "Responsetime in ms",
                  data: mm,
                  backgroundColor: [
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
                      'rgba(255, 159, 64, 1)'
                  ],
                  borderWidth: 1,
                  showLine: true
              }]
          },
          options: {
              scales: {
                  xAxes: [{
                      type: 'time',
                      time: {
                          displayFormats: {
                              'day': 'MMM DD'
                          }
                      }
                  }],
                  yAxes: [{
                      ticks: {
                          beginAtZero: true
                      }
                  }]
              },
              responsive: false,
              elements: {
                  line: {
                      tension: 0
                  }
              }
          }
      };
      const chart = new Chart(canvas, options);
  }
});
