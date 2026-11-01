# Architecture image status (V15)

`system_architecture.png` is drawn from the implemented code (components, topics, rates, the separate
temperature safety rule, the durable outbox, the UUID acknowledgement, what is NOT implemented).
It replaces the earlier AI-generated picture, whose labels did not match the code (for example it
showed a pre-selected model, a fleet dashboard and an MQTT/HTTPS uplink that do not exist).

Still check it against your own system before you submit: if you change anything (topic names,
rates, a TLS broker, a different backend), update both the picture and `system_architecture.mmd`.
`system_architecture.mmd` is the text source of the same diagram.
