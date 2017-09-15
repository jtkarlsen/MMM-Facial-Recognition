'use strict';
const NodeHelper = require('node_helper');

const PythonShell = require('python-shell');
var pythonStarted = false;

module.exports = NodeHelper.create({

    socketNotificationReceived: function(notification, payload) {
        console.log('FR: Got request to start python application');
        if(notification === 'START_RECOGNITION') {
            this.config = payload;
            if(!pythonStarted) {
                pythonStarted = true;
                this.python_start();
            }
        }
    },

    python_start: function () {
        console.log("FR: Starting python application");
        const self = this;
        const pyshell = new PythonShell('modules/' + this.name + '/facial_recognition.py', {
            mode: 'text'
        });

        pyshell.on('message', function (data) {
            var payload = JSON.parse(data);
            console.log("FR: [" + self.name + "] " + data);
            console.log("FR: [" + self.name + "] " + payload);
            console.log("FR: [" + self.name + "] " + "sending type: " + payload.type);
            self.sendSocketNotification(payload.type, payload);
        });

        pyshell.end(function (err) {
            if (err) throw err;
            console.log("FR: [" + self.name + "] " + 'finished');
            this.python_start()
        });
    }
});