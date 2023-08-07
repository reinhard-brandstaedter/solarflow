$(document).ready(function () {
  const outputHomectx = document.getElementById("outputHome").getContext("2d");

  const outputHome = new Chart(outputHomectx, {
    type: "bar",
    data: {
      datasets: [{ label: "Output to Home (W)",  }],
    },
    options: {
      borderWidth: 1,
      borderColor: ['rgba(130, 182, 223, 1)',],
      backgroundColor: ['rgba(192, 224, 248, 1)',],
      plugins: {
        legend: {
            display: false,
        }
      },
      scales: {
        y: {
          text: "W",
          beginAtZero: true
        }
      }
    },
  });

  const solarInputctx = document.getElementById("solarInput").getContext("2d");
  const solarInput = new Chart(solarInputctx, {
    type: "bar",
    data: {
      datasets: [{ label: "Solar Input (W)",  }],
    },
    options: {
      borderWidth: 1,
      borderColor: ['rgba(248, 212, 105, 1)',],
      backgroundColor: ['rgba(249, 236, 184, 1)',],
      plugins: {
        legend: {
            display: false,
        }
      },
      scales: {
        y: {
          beginAtZero: true
        }
      }
    },
  });

  const outputPackctx = document.getElementById("outputPack").getContext("2d");
  const outputPack = new Chart(outputPackctx, {
    type: "bar",
    data: {
      datasets: [{ label: "Charging (W)",  }],
    },
    options: {
      borderWidth: 1,
      borderColor: ['rgba(95, 170, 145, 1)',],
      backgroundColor: ['rgba(175, 218, 208, 1)',],
      plugins: {
        legend: {
            display: false,
        }
      },
      scales: {
        y: {
          beginAtZero: true
        }
      }
    },
  });

  const electricLevelctx = document.getElementById("electricLevel").getContext("2d");
  const electricLevel = new Chart(electricLevelctx, {
    type: "bar",
    data: {
      datasets: [{ label: "Average Battery Level",  }],
    },
    options: {
      borderWidth: 1,
      borderColor: ['rgba(95, 170, 145, 1)',],
      backgroundColor: ['rgba(175, 218, 208, 1)',],
      plugins: {
        legend: {
            display: false,
        }
      },
      scales: {
        y: {
          beginAtZero: true
        }
      }
    },
  });

  const maxTempctx = document.getElementById("maxTemp").getContext("2d");
  const maxTemp = new Chart(maxTempctx, {
    type: "bar",
    data: {
      datasets: [{ label: "Battery Temperature",  }],
    },
    options: {
      borderWidth: 1,
      borderColor: ['rgba(95, 170, 145, 1)',],
      backgroundColor: ['rgba(175, 218, 208, 1)',],
      plugins: {
        legend: {
            display: false,
        }
      },
      scales: {
        y: {
          beginAtZero: true
        }
      }
    },
  });

  const socLevelctx = document.getElementById("socLevel").getContext("2d");
  const socLevel = new Chart(socLevelctx, {
    type: "bar",
    data: {
      datasets: [{ label: "Battery State of Charge",  }],
    },
    options: {
      borderWidth: 1,
      borderColor: ['rgba(95, 170, 145, 1)',],
      backgroundColor: ['rgba(175, 218, 208, 1)',],
      plugins: {
        legend: {
            display: false,
        }
      },
      scales: {
        y: {
          beginAtZero: true
        }
      }
    },
  });

  $('#form-outputHomeLimit').on('submit', function () {
    socket.emit('setLimit', '{"property": "outputLimit", "value":' + $('#outputHomeLimit').val() +'}' );
    return false;
  });

  $('#form-solarInputLimit').on('submit', function () {
    socket.emit('setLimit', '{"property": "inputLimit", "value":' + $('#solarInputLimit').val() +'}' );
    return false;
  });

  $('#form-socSet').on('submit', function () {
    socket.emit('setLimit', '{"property": "socSet", "value":' + $('#socSet').val()*10 +'}' );
    return false;
  });

  function addData(label, metric, data) {
    remove = false
    if (metric == "socLevel" || metric == "maxTemp" ) {
      idx = eval(metric).data.labels.indexOf(label)
      remove = (idx >= 0)
      if (remove) {
        eval(metric).data.labels.splice(idx,1)
      }
    }
    eval(metric).data.labels.push(label);
    eval(metric).data.datasets.forEach((dataset) => {
      if (remove) {
        console.log("removing data")
        dataset.data.splice(idx,1)
      }
      dataset.data.push(data);
    });
    eval(metric).update();
  }

  function removeFirstData(metric) {
    eval(metric).data.labels.splice(0, 1);
    eval(metric).data.datasets.forEach((dataset) => {
      dataset.data.shift();
    });
  }

  const MAX_DATA_COUNT = 200;
  //connect to the socket server.
  //   var socket = io.connect("http://" + document.domain + ":" + location.port);
  var socket = io.connect();

  //receive details from server
  socket.on("updateSensorData", function (msg) {
    console.log("Received sensorData: "+ msg.date + "::" + msg.metric + " :: " + msg.value);

    // Show only MAX_DATA_COUNT data
    if (eval(msg.metric).data.labels.length > MAX_DATA_COUNT) {
      removeFirstData(msg.metric);
    }
    addData(msg.date, msg.metric, msg.value);
  });
});
