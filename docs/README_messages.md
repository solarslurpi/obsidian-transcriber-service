# Messages
An `sse` connection is used to send messages to the client.  The events include `status`, `data` and `server_error`.  `status` messages are liberally sprinkled throughout the code to provide the client progress update.  A `server_error` lets the client know the event loop has stopped and cleanup has been done on the server side code for this run.  The client will need to start over.  `data` messages are used to send the transcribed text to the client.

## Data messages
After the transcription process is complete, the following data messages are sent to the client:

- `key`: The first data message is the `key`.  The `key` is created by the service when the transcribed content is cached. See the  If data messages are lost, the Obsidian client can request one or more messages associated with the `key`.
- `basename` -