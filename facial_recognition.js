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
            if (this.users.length > 0) {
                var content = document.createElement("span");
                content.innerHTML = "Hei " + this.parseNames(this.users);
                wrapper.appendChild(content);
            }
            if (this.users.length < 1) {
                var content = document.createElement("span");
                content.innerHTML = "Hei";
                wrapper.appendChild(content);
            }
        }
        Log.info(wrapper);
        return wrapper;
    },


    socketNotificationReceived: function(notification, payload) {
        Log.info('FR: got user from python');
        if(notification === 'USER') {
            this.gotIdentity(payload.user_map);
        }
    },

    gotIdentity: function(identity) {
        Log.info("FR: got identity: " + identity);
        var identities = JSON.parse(identity);
        this.sayHello(identities);
    },

    sayHello: function (identities) {
        // if (!this.isDuplicateUser(identity)) {
            this.users = identities;
            // this.current_user.name = identity;
            // this.current_user.time = this.timestamp();

            if (!this.active_greeting) {
                Log.info("Saying hello");
                this.active_greeting = true;
                this.updateDom();
                var self = this;
                setTimeout(function(){
                    Log.info('Done saying hello');
                    self.active_greeting = false;
                    self.updateDom();
                }, this.config.display_duration*1000);
            }
        // }
    },
    
    parseName: function (name) {
        var lastIndex = name.lastIndexOf(" ");
        return name.substring(0, lastIndex);
    },
    
    parseNames: function (names) {
        var concat = '';
        var join1 = ' og ';
        var join2 = ', ';
        if (names.length < 0) {
            return concat;
        } else if (names.length === 1) {
            concat = this.parseName(names[0]);
        } else {
            concat = this.parseName(names[0]);
            for (var i = 1; i < names.length-1; i++) {
                concat += join2+this.parseName(names[i]);
            }
            concat += join1+this.parseName(names[names.length-1]);
        }
        return concat;
    },

    isDuplicateUser: function (identity) {
        return (identity === this.current_user.name && (this.timestamp() - this.current_user.time) < this.config.duplicate_timeframe);
    },

    timestamp: function () {
        return Math.round(+new Date()/1000);
    },

    start: function() {
        this.users = [];
        this.current_user = {
            name: '',
            time: this.timestamp()-this.config.duplicate_timeframe
        };
        this.active_greeting = false;
        Log.info('FR: Starting module: ' + this.name);
        this.sendSocketNotification('START_RECOGNITION', this.config);
    }
});