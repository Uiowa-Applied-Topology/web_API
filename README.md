# Tanglenomicon Data Server API

The Tanglenomicon data server API describes the API provided by the Tanglenomicon to read/write to the mongodb.

# Planning

## Tasks

Tasks will be decomposed per feature. Each feature will include one or many endpoints. Issues will be tracked per report, combining where it makes sense.

## Version control

Version control will be git based with github as the source of truth. Work items will have a branch per work item. Merging a work item will be managed by github pull requests.

## Project Structure

Project structure will follow a standard python project structure

```
📦tanglenomicon_data_api
 ┣ 📂.github
 ┣ 📂docs
 ┣ 📂tanglenomicon_data_api
 ┣ 📂test
 ┣ 📜.flake8
 ┣ 📜.gitignore
 ┣ 📜LICENSE
 ┣ 📜README.md
 ┣ 📜requirements.txt
 ┗ 📜setup.py
```

- 📂tanglenomicon_data_api : Shall contains source code
- 📂test : Shall contain test code
- 📂docs : Shall contain documentation for specific features

## Define a Unit: A unit in this project shall be a python module.

## Quality

This project will be a public API for the tanglenomicon project. This requires a high level of validation. With the primary design goal of never crashing. While api R/W failures are acceptable with reporting.

### Unit testing

Every unit is expected to have a unit test suite. Unit test suites are expected to flex every public interface of their unit. Code coverage is optional.

### Integration testing

Integration tests are expected for every program flow.

## Requirements

### Functional Requirements

```mermaid

flowchart LR
    subgraph 'Generation'
        direction LR
        G1([Get Montesinos job])
        G2([Report Montesinos job])
    end
    subgraph 'Job Handling'
        direction LR
        JH1([Build job])
        JH2([Clean up stale jobs   ])
        JH3([Clean up complete jobs])
        JH4([Mark job as complete  ])
        JH5([Mark job as new       ])
        JH6([Mark job as pending   ])
        JH7([Fill job queue        ])
    end
    subgraph 'Database Handling'
        direction LR
        DH1([Mark progress   ])
        DH2([Write record set])
        DH3([Read record set ])
    end

    client["Client fa-user-o"]
    time["Client fa-user-o"]


    client --> G1
    client --> G2
    time --> JH2
    time --> JH3
    time --> JH7

    JH1 -. include .-> JH5
    JH2 -. include .-> JH6
    JH7 -. include .-> JH1
    JH1 -. include .-> DH3
    JH3 -. include .-> DH1
    JH3 -. include .-> DH2
    G1  -. include .-> JH6
    G2  -. include .-> JH4

```
Functional requirements are phrased in the following use cases

```{toctree}
:titlesonly:
use_cases/index.md
```

### Non-functional Requirements

* Must be packaged as a docker container
* Must run in linux

## Technologies

### Languages/Frameworks

The project will be written in python using the [fastapi](https://fastapi.tiangolo.com/) framework. All required packages are included in the `requirements.txt`

Using a vitrual environment is suggested from the root run in powershell:

```shell
python -m venv py_venv
.\py_venv\Scripts\Activate.ps1
pip install -r .\requirements.txt
```

#### Style Guide

All python files are expected to pass the configured flake8 without warnings this includes aligning to [https://github.com/psf/black](https://github.com/psf/black).

### Tools

* vscode
* mermaid.js
* plantUML
* python3
* pytest
* flake8
* git

# Design and Documentation


## System

### Block Diagram

```mermaid

flowchart LR
    tanglenomicon_data_api["Tanglenomicon API"]
    subgraph  Interfaces
        age["Generation Endpoint\n&lt;&lt;interface&gt;&gt;"]

        aj["Job\n&lt;&lt;interface&gt;&gt;"]
        es["State\n&lt;&lt;enumeration&gt;&gt;"]
    end


    subgraph Internal
        dc["DB Connector"]
        jq["Job Queue"]
        cs["Config Store"]
        sm["Security Model"]
    end
    subgraph Montesinos
        mge["Montesinos Generation Endpoint\n&lt;&lt;interface&gt;&gt;"]


        mj["Montesinos Job\n&lt;&lt;interface&gt;&gt;"]

    end

    mj  ---> |1..*|jq
    mge -.-> age
    mj -.-> aj
    aj -.-> es
    cs  ---> tanglenomicon_data_api
    jq  ---> |1| tanglenomicon_data_api
    mge ---> |1| tanglenomicon_data_api
    sm  ---> |1| tanglenomicon_data_api
    dc  ---> |1| jq
    dc  ---> |1| sm


```


## Units


Unit descriptions are as follows:

```{toctree}
:titlesonly:
unit_description/index.md
```