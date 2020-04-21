/* This Source Code Form is subject to the terms of the Mozilla Public
 * License, v. 2.0. If a copy of the MPL was not distributed with this
 * file, You can obtain one at http://mozilla.org/MPL/2.0/. */

"use strict";

/**
 * List of connections for `content <-> devtools` communication.
 */
var connections = {};

var port_app = chrome.runtime.connectNative("har_catcher");

/*
Listen for messages from the app.
*/
port_app.onMessage.addListener((response) => {
  console.log("background.js: Received response");
});

/**
 * This script is responsible for relaying messages between
 * content and devtools scopes.
 *
 * Basic listener for connect messages. It's responsible
 * for creating mappings and forwarding messages between
 * content and devtools scopes.
 *
 * Both, the content and devtools scope must send
 * an initialization message in order to pair.
 */
chrome.runtime.onConnect.addListener(function(connection) {
  //console.log("background-script: onConnect", connection);

  var listener;

  // Setup port (connection) for messages from devtools scope.
  if (connection.name === "devtools") {
    listener = function(message, sender, sendResponse) {
      //console.log("background-script: from devtools", message, sender);

      var con = connections[message.tabId] = (connections[message.tabId] || {});
      con.devtools = connection;

      // Remove port from the list when closed.
      listener.close = function() {
        delete con.devtools;
      }

      switch (message.action) {
        case "getHAR":
          console.log("background.js: Got HAR");
          console.log(message.har);
          port_app.postMessage(message.har);
          console.log("background.js: Message sent");
          break;
        case "requestFinished":
          break;
      }
    }
  }

  // Setup port (connection) for messages from content scope.
  if (connection.name === "content") {
    listener = function(message, port, sendResponse) {
      //console.log("background-script: from content", message, port);

      var con = connections[port.sender.tab.id] = (connections[port.sender.tab.id] || {});
      con.content = connection;

      // Remove port from the list when closed.
      listener.close = function() {
        delete con.content;
      }

      if (con.devtools && message.action) {
        con.devtools.postMessage(message);
      }
    }
  }

  // Add devtools or content listener.
  connection.onMessage.addListener(listener);

  // Listen for connection close.
  connection.onDisconnect.addListener(function() {
    if (listener.close) {
      listener.close();
    }
    connection.onMessage.removeListener(listener);
  });
});
