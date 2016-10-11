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

        pyshell.on('message', function (identities) {
            console.log("FR: [" + self.name + "] " + identities);
            self.sendSocketNotification('USER', {user_map: identities});
        });

        pyshell.end(function (err) {
            if (err) throw err;
            console.log("FR: [" + self.name + "] " + 'finished');
            this.python_start()
        });
    }
});