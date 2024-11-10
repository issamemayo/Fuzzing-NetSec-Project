let url = "ws://127.0.0.1:8000/ws/fuzz/";
const socket = new WebSocket(url);

socket.onopen = function (event) {
  console.log("WebSocket is open now.");
  socket.send(JSON.stringify({ message: "Hello, server!" }));
};

socket.onmessage = function (event) {
  const data = JSON.parse(event.data);
  console.log("Received from server:", data.message);
};

socket.onclose = function (event) {
  console.log("WebSocket is closed now.");
};
