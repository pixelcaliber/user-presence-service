# user-presence-service

Part of chat-application microservices: Enables real time user-presence functionality which marks user active/inactive or online/offline using HEARTBEAT mechanism based on last user activity received from the client timestamp (here: mouse-up mouse-down movements) and comparing it with a threshold time quantum.

- Worker running infinitely, checking for user's last timestamp and if found more than the threshold time quantum (~10 mins) mark them as inactive in the user-presence database (here: postgres)
- Utilizes heartbeat mechinism to query for user status using pooling
- utilized redis cluster to store the last active timestamp; evicition pollicy: LRU and cache size: 100mb
- has enpoints for:
  - updating user's last active timestmap in the redis cluster
  - retrieving the user's last active timestamp from the redis cluster
  - querying for user's active/inactive status in the database (here: postgres)

tech-stack: Kafka, Redis, Postgres, Python, Flask, Postgres
