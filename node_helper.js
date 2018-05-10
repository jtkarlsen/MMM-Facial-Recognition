"use strict";
var exec = require("child_process").exec;
const NodeHelper = require("node_helper");
const PythonShell = require("python-shell");

module.exports = NodeHelper.create({
  socketNotificationReceived: function(notification, payload) {
    console.log("FR: Got request to start python application");
    if (notification === "START_RECOGNITION") {
      this.config = payload;
      this.python_start();
    }
  },

  python_start: function() {
    console.log("FR: Killing possible previous python script");
    exec("killall python", (error, stdout, stderr) => {
      console.log("stdout: " + stdout);
      console.log("stderr: " + stderr);
      if (error !== null) {
        console.log("exec error: " + error);
      }
    });
    console.log("FR: Starting python application");
    const self = this;
    const pyshell = new PythonShell(
      "modules/" + this.name + "/facial_recognition.py",
      {
        mode: "text"
      }
    );

    pyshell.on("message", function(data) {
      var payload = JSON.parse(data);
      console.log("FR: [" + self.name + "] " + data);
      console.log("FR: [" + self.name + "] " + payload);
      console.log("FR: [" + self.name + "] " + "sending type: " + payload.type);
      self.sendSocketNotification(payload.type, payload);
    });

    pyshell.end(function(err) {
      if (err) throw err;
      console.log("FR: [" + self.name + "] " + "finished");
      this.python_start();
    });
  }
});
