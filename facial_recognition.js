Module.register("facial_recognition", {
  // Default module config.
  defaults: {
    sensitivity: 0.5,
    duplicate_timeframe: 10,
    display_duration: 10
  },

  // Override dom generator.
  getDom: function() {
    var wrapper = document.createElement("div");
    if (this.active_greeting) {
      var content = document.createElement("span");
      var unknown_faces = this.face_count - this.users.length;
      if (this.users.length > 0) {
        content.innerHTML = "Hei " + this.parseNames(this.users);
        if (unknown_faces > 1) {
          content.innerHTML += " og " + String(unknown_faces) + " andre";
        } else if (unknown_faces == 1) {
          content.innerHTML += " og en annen";
        }
      } else if (this.users.length < 1) {
        content.innerHTML = "Hei";
        if (unknown_faces > 0) {
          content.innerHTML += " dere";
        }
      }

      wrapper.appendChild(content);
    }
    if (this.active_emotion) {
      var content = document.createElement("span");
      content.innerHTML = this.getMoodAsText(this.emotion);
      wrapper.appendChild(content);
    }
    if (this.active_test) {
      var content = document.createElement("span");
      content.innerHTML = this.testMessage;
      wrapper.appendChild(content);
    }
    Log.info(wrapper);
    return wrapper;
  },

  getMoodAsText: function(emotion) {
    var emotions = [
      { name: "trist", score: emotion.scores.sadness },
      { name: "nøytral", score: emotion.scores.neutral },
      { name: "sint", score: emotion.scores.anger },
      { name: "redd", score: emotion.scores.fear },
      { name: "glad", score: emotion.scores.happiness },
      { name: "overrasket", score: emotion.scores.surprised }
    ];
    emotions.sort(function(a, b) {
      if (a.score == b.score) {
        return 0;
      } else if (a.score < b.score) {
        return 1;
      } else {
        return -1;
      }
    });
    var emotion_text = "Ser ut som du er ";
    if (this.active_greeting) {
      emotion_text = ", det ser ut som du er ";
    }
    if (emotions[0].name === "nøytral") {
      emotion_text += "litt " + emotions[1].name;
    } else {
      emotion_text += "ganske " + emotions[0].name;
    }
    emotion_text += " i dag";
    return emotion_text;
  },

  socketNotificationReceived: function(notification, payload) {
    Log.info("FR: got payload from python");
    Log.info("FR: is of type " + notification);
    console.log("Got payload from node_helper");
    console.log(`It is of type ${notification}`);
    console.log(payload);
    if (notification === "identity") {
      this.gotIdentity(payload.names, payload.faces);
    }
    if (notification === "emotion") {
      this.showEmotion(payload.emotion);
    }
    // this.displayMessage('notification: ' + JSON.stringify(payload.emotion));
  },

  displayMessage: function(message) {
    Log.info("testing message");
    if (!this.active_test) {
      this.active_test = true;
      this.testMessage = message;
      this.updateDom();
      var self = this;
      setTimeout(function() {
        Log.info("Done displaying emotion");
        self.active_test = false;
        self.updateDom();
      }, this.config.display_duration * 1000);
    }
  },

  showEmotion: function(emotion) {
    Log.info("Showing emotion");
    if (!this.active_emotion && emotion.length != 0) {
      this.emotion = emotion[0];
      this.active_emotion = true;
      this.updateDom();
      var self = this;
      setTimeout(function() {
        Log.info("Done displaying emotion");
        self.active_emotion = false;
        self.updateDom();
      }, this.config.display_duration * 1000);
    }
  },

  gotIdentity: function(names, faces) {
    Log.info("FR: got names: " + names);
    Log.info("FR: got face count: " + faces);
    this.sayHello(names, faces);
  },

  sayHello: function(names, faces) {
    // if (!this.isDuplicateUser(identity)) {
    this.users = names;
    this.face_count = faces;
    // this.current_user.name = identity;
    // this.current_user.time = this.timestamp();

    if (!this.active_greeting) {
      Log.info("Saying hello");
      this.active_greeting = true;
      this.updateDom();
      var self = this;
      setTimeout(function() {
        Log.info("Done saying hello");
        self.active_greeting = false;
        self.updateDom();
      }, this.config.display_duration * 1000);
    }
    // }
  },

  parseName: function(name) {
    var lastIndex = name.lastIndexOf(" ");
    return lastIndex === -1 ? name : name.substring(0, lastIndex);
  },

  parseNames: function(names) {
    var concat = "";
    var join1 = " og ";
    var join2 = ", ";
    if (names.length < 0) {
      return concat;
    } else if (names.length === 1) {
      concat = this.parseName(names[0]);
    } else {
      concat = this.parseName(names[0]);
      for (var i = 1; i < names.length - 1; i++) {
        concat += join2 + this.parseName(names[i]);
      }
      concat += join1 + this.parseName(names[names.length - 1]);
    }
    return concat;
  },

  isDuplicateUser: function(identity) {
    return (
      identity === this.current_user.name &&
      this.timestamp() - this.current_user.time <
        this.config.duplicate_timeframe
    );
  },

  timestamp: function() {
    return Math.round(+new Date() / 1000);
  },

  start: function() {
    this.users = [];
    this.face_count = 0;
    this.current_user = {
      name: "",
      time: this.timestamp() - this.config.duplicate_timeframe
    };
    this.emotion = {};
    this.active_greeting = false;
    this.active_emotion = false;
    this.active_test = false;
    this.testMessage = "Test";
    Log.info("FR: Starting module: " + this.name);
    this.sendSocketNotification("START_RECOGNITION", this.config);
  }
});
