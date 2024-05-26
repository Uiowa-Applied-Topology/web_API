# Use case:

Report Montesinos Job

# Primary actor:

Client

# Goal:

Receives a completed job from a client.

# Preconditions:

* Client and server are on the same network.
* Client is on known runner list.

# Trigger:

Client reports a complete montesinos job.


# Scenario:

1) Client makes a `put` to the server with job data
2) Server verifies client ID
3) Server stores job results
