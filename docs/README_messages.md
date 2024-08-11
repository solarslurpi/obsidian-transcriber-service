# Messages
An `sse` connection is used to send messages to the client.  The events include `status`, `data` and `server_error`.  `status` messages are liberally sprinkled throughout the code to provide the client progress update.  A `server_error` lets the client know the event loop has stopped and cleanup has been done on the server side code for this run.  The client will need to start over.  `data` messages are used to send the transcribed text to the client.

## Data messages
After the transcription process is complete, the following data messages are sent to the client:

- `key`: The first data message is the `key`.  The `key` is created by the service when the transcribed content is cached. See the [`make_key`](https://github.com/solarslurpi/obsidian-transcriber-service/blob/030fc45cb8fee3eef4fea68f1f9395ed150ea895/src/transcription_state_code.py#L226) method. If data messages are lost, the Obsidian client can request one or more messages associated with the `key`.
- `basename` - The `basename` is returned to the client to be used as the title of the transcribed Obsidian note.  If the original audio came from YouTube, the basename is the YouTube title sanitized to have characters that will work when creating a file.  See the [download_video](https://github.com/solarslurpi/obsidian-transcriber-service/blob/030fc45cb8fee3eef4fea68f1f9395ed150ea895/src/youtube_handler_code.py#L74) method.  If the original audio source was an audio file, the audiofile's name is used.  See the [extract](https://github.com/solarslurpi/obsidian-transcriber-service/blob/030fc45cb8fee3eef4fea68f1f9395ed150ea895/src/audio_handler_code.py#L37) method.
- `num_chapters` - The transcript is broken into [Chapters](/docs/README_glossary.md#chapters). By sending the number of chapters, the client knows how many chapters to expect.
- `metadata` - The [metadata](/docs/README_glossary.md#metadata) from the original audio source is sent to the client.  The Obsidian client uses the metadata to create the note's front matter.
- `chapter` - Each chapter is then sent to the client up to num_chapters.

The obsidian client maintains state on which messages have been received. After a timeout period, if the state is not complete, the client requests the missing messages using the `/api/v1/missing_content` FastAPI endpoint.  The server will then resend the missing messages.

### Debugging
If the Obsidian client cannot create the transcript due to missing messages, it is time to debug.
#### Messages sent from the Server
- Isolate debug statements to the `app.py` module. This is the module that contains the sse event generator that is responsible for sending the messages.  See the [event_generator](https://github.com/solarslurpi/obsidian-transcriber-service/blob/030fc45cb8fee3eef4fea68f1f9395ed150ea895/src/app.py#L141) code.  To do this, modify `logging_config.py` and set all modules except `app` to `logging.WARNING`.  Set the `app` module to `logging.DEBUG`.
- Start the server.  My dev environment is running on Windows within a `venv`. I start the server from the project root with `python src\app.py`.
- Verify the FastAPI endpoints are available by navigating the browser to `http://localhost:8000/docs`. This should bring up the Swagger UI provided by FastAPI.
- Start a client.  For this test, I use `postman`.  Using `postman` isolates the potential problems to the server side code. It allows setting up the SSE session as well as sending the `transcribe` request.  I created a collection that has
    - send this first: SSE session setup: `$ curl --location 'http://127.0.0.1:8081/api/v1/sse' `
    - send audio setup (e.g. is for YouTube)...It is something like this:`curl --location "http://127.0.0.1:8081/api/v1/process_audio" --header "accept: application/json" --form "youtube_url=\"https://www.youtube.com/watch?v=yYxoLIsbl84\"" --form "file=@\"/path/to/file\"" --form "audio_quality=\"default\"" --form "chapter_chunk_time=\"10\""`.  I copy/pasted the `curl` command from Postman. I am not able to get this to work on Windows even though it works in Postman.
- View the records within the SSE tab:
```
id: 34
event: reset-state
data: Clear out the previous content.
retry: 3000

id: 35
event: data
data: {"key": "https://www.youtube.com/watch?v=yYxoLIsbl84_Systran/faster-whisper-tiny.en"}
retry: 3000

id: 36
event: data
data: {"num_chapters": 2}
retry: 3000

id: 37
event: data
data: {"basename": "Extracting Knowledge Graphs and Structured Data from very long PDF files"}
retry: 3000

id: 38
event: data
data: {"metadata": {"audio_input": {"youtube_url": "https://www.youtube.com/watch?v=yYxoLIsbl84", "audio_filepath": null, "audio_quality": "Systran/faster-whisper-tiny.en", "compute_type": "int8",
"chapter_time_chunk": 10}, "title": "Extracting Knowledge Graphs and Structured Data from very long PDF files", "tags": "", "description": "Extracting Knowledge Graphs and Structured Data from very long PDF files using gpt-4o-mini and gpt-4o....}}
retry: 3000

id: 39
event: data
data: {"chapter": {"title": "", "start_time": "00:00:00", "end_time": "00:10:06", "text": " Hey, ......."}}
retry: 3000

id: 40
event: data
data: {"chapter": {"title": "", "start_time": "00:10:06", "end_time": "00:13:02", "text": " And then we are again using JSON within to the mission JSON here, but we did mention on the user message. We are asking to extract key entities and their relationships from this disk turns the JSON object is going to turn into one into two in relationships that is present across each and every one of these titles so you can modify this if you wanted a different behavior just remember that you can make it your own. And we get that each entity relationships we loop over them we get the off entities and the relationships and we add the nodes and the edges. And then we toggle physics true you can set this to false and I'll show the buttons and we return the net now that's this was just a function create knowledge graph. We are going to use it after we asked you want to create knowledge graph yes no if the user answers yes time you're going to create it and save it as a knowledge graph that HTML informative print statement so as you can see it's pretty simple but. It works very well like I said called files for this will be available at my page on like will be in the description and comment. Check out my website, we can have access to all my videos over 350 of them and 250 of them are available to download for my patrons any one of them, like I said and check out my interest really love the thousand next master class if you want to take care of look at it. It's available at connoisseur level patrons, I also have weekly may meet each for my active plus patrons next one is tomorrow Sunday, I was fourth while PM, but we do this. And I also started it and perks these are discounts and free memberships and so on from different interesting providers first one. Only one currently we have is boring lounge they help you to the blue sewer. ACO score for your startup by submitting into 100 plus platforms. Our offering is off my deck level patrons and four dollars off to my connoisseur level patrons. And finally, I do have one on one consultations this is also it's different different tiers at my patreon if you take a look at it where choose are in prodigy. One hour per month and three hours per month, respectively. Thank you for watching, if you did enjoy this please give it a like and subscribe to get notified my future video. For I am much more active recently on X platform, my handle is at high on the score echo. Rejoin me there, I post valuable content over there as well. Thank you for watching and see you in the next video.", "number": 2}}
retry: 3000
```

#### Review Messages
The first message (id=34) is a `reset-state` event.  This tells the client to clear out the state because a new transcription is starting.

The `data` event messges follow. The data messages will about as debug statements as well as messages to the Postman's connected SSE client. If they appear similar to what is shown above, the server is correctly sending messages.
