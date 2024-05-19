# Unit: Job Queue

## Description

This class defines the job queue. This is used to hold the current job states for the server.

## Diagrams

```mermaid

classDiagram

    class jq["Job Queue"]{
        - List~Job~ job_queue
        - Semephore semephore
        - db_connector db
        + mark_job_complete(job_id)
        + get_next_job(type)
        + clean_stale_jobs()
        + clean_complete_jobs()
        + add_new_jobs(job)
    }
```

## Function flow

### clean_stale_jobs
```mermaid


stateDiagram-v2

    [*] --> for
    state "for each job" as for {
    state if_state <<choice>>
    state "Get State" as staleChk
    state "Set state to new" as setNew
    [*] --> staleChk
     staleChk --> if_state
    if_state --> setNew: if is Stale
    if_state --> [*] : if is not Stale
    setNew --> [*]
    }
    for   --> [*]
```

### clean_complete_jobs
```mermaid


stateDiagram-v2

    [*] --> for
    state "for each job" as for {
    state if_state <<choice>>
    state "Get State" as staleChk
    state "Commit to storage" as setNew
    [*] --> staleChk
     staleChk --> if_state
    if_state --> setNew: if is complete
    if_state --> [*] : if is not complete
    setNew --> [*]
    }
    for   --> [*]
```
### add_new_jobs

```mermaid


stateDiagram-v2

    state if_state <<choice>>
    state "Get queue fill" as staleChk
    state "Build job from storage" as setNew
    [*] --> staleChk
    staleChk --> if_state
    if_state --> setNew: if is underfilled
    if_state --> [*] : if is not underfilled
    setNew --> staleChk
```


### mark_job_complete
```mermaid


stateDiagram-v2
    state if_state <<choice>>

    state "Get job state" as getjs
    state "Update job payload" as updateJob
    state "Set state of job to complete" as setNew

    [*] --> getjs
    getjs --> if_state
    if_state --> updateJob : if is pending
    if_state --> [*] : if is not pending
    updateJob --> setNew
    setNew --> [*]
```


### get_next_job
```mermaid


stateDiagram-v2
    state "Get lowest index new job of 'type'" as staleChk

    [*] --> staleChk
    staleChk --> [*]
```

## Unit test description

Unit has no stand alone functionality.