# FAIL [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.13376644.svg)](https://doi.org/10.5281/zenodo.13376644)

FAIL is an LLM based pipeline to collect and analyze software failures from the news. This paper can be found here [https://arxiv.org/abs/2406.08221](https://arxiv.org/abs/2406.08221).

A database of software failures from 2010 to 2022 curated by FAIL is available at: [http://ec2-44-222-209-185.compute-1.amazonaws.com:8000/dashboard/](http://ec2-44-222-209-185.compute-1.amazonaws.com:8000/dashboard/)
- Unfortunately, the website is currently broken, and we are working on fixing it. In the meantime, our raw database is available as a JSON dump at: [https://drive.google.com/file/d/1Ajwxj2PKVunTJHT98naD9s7lc6kmptHu/view](https://drive.google.com/file/d/1Ajwxj2PKVunTJHT98naD9s7lc6kmptHu/view)
- You can also view our database as a SQL dump at [![DOI](https://zenodo.org/badge/DOI/10.5281/zenodo.13376695.svg)](https://doi.org/10.5281/zenodo.13376695)
- The JSON data contains a list of articles and incidents. Incidents have a generated postmortem report as described in Table 1 of the paper. Please note that there are occasionall missing (N/A) values in the reports. An analysis of this data is described in Section 4 of the paper.


## About
This repository contains all of the artifacts of the project.

Our artifact includes the following (ordered by sections):
|   Item   |   Description  |   Corresponding content in the paper  |
|----------|----------------|---------------------------------------|
|[Source code of FAIL](#running-the-pipeline)| Source code of the pipeline to automatically analyze failures from the news | Section 3 - FAIL: Design and implementation |
| [Manual Analysis and Evaluation](#manual-analysis-and-evaluation) | Manual analysis of incidents and evaluation of the pipeline | Section 3.2 - Component Development and Validation | |
| [Results](#plot-figures-and-gather-statistics-used-in-the-paper) | Source code to plot figures and gather other results from the paper |  Section 4 - Analyzing the FAIL DB |


## Citations
For citations, please refer to the following:

**APA Citation:**
Anandayuvaraj, D., Campbell, M., Tewari, A., & Davis, J. C. (2024). *FAIL: Analyzing Software Failures from the News Using LLMs*. Proceedings of the 2024 IEEE/ACM International Conference on Automated Software Engineering (ASE). IEEE.

**BibTeX Citation:**
```bibtex
@inproceedings{ananday2024fail,
  title={FAIL: Analyzing Software Failures from the News Using LLMs},
  author={Anandayuvaraj, Dharun and Campbell, Matthew and Tewari, Arav and Davis, James C},
  booktitle={Proceedings of the 2024 IEEE/ACM International Conference on Automated Software Engineering (ASE)},
  year={2024},
  organization={IEEE}
}
```

## Setting up the pipeline

### Setting up the docker containers for the pipeline

1. Build and spin up the container:

    ```bash
    $ docker compose -f local.yml up --build -d
    ```

2. Apply the migrations in the container:

    ```bash
    $ docker compose -f local.yml run --rm django python manage.py makemigrations
    $ docker compose -f local.yml run --rm django python manage.py migrate
    ```

3. Make sure the container is running:

    ```bash
    $ docker compose -f local.yml up
    ```

> [!TIP]
Note: To log stdout/stderr for pipeline command that is detached, follow these steps:
>1. Run the command:
>
>        $ docker compose -f local.yml run -e OPENAI_API_KEY -d --name failures_run_command django python -m failures classify  
>2. Wait for the command to finish running, then export the log:
>
>        $ docker logs failures_run_command >> failures_run_command.log 2>&1
>3. Then kill the container:
>
>        $ docker rm failures_run_command


### Admin Site

1. Create an admin account:

    ```bash
    $ docker compose -f local.yml run --rm django python manage.py createsuperuser
    ```

2. Access the site administration page at `/admin/`

## Running the pipeline

### Step 1. Searching and scraping news articles 
Option 1. Using the Admin Site and the Command Line

   1. Navigate to the `/admin/` page and log in.

   2. Click on `Search Queries` underneath the `Articles` section.

   3. Click on `ADD SEARCH QUERY +`.

   4. Enter a search query and click `SAVE`.

   5. Run a scrape from the command line:

       ```bash
       $ docker compose -f local.yml run --rm django python -m failures scrape
       ```

Option 2. Using Only the Command Line

   1. Display the help text:

       ```bash
       $ docker compose -f local.yml run --rm django python -m failures scrape --help
       ```

   2. Run a scrape:

       ```bash
       $ docker compose -f local.yml run --rm django python -m failures scrape --keyword "keyword"
       ```

> [!TIP] 
>To scrape news for specific years, specific sources, specific key words, modify and run: [tests/commands/exp_RunQueriesCommand.py](tests/commands/exp_RunQueriesCommand.py)

### Step 2. Classifying articles on whether they report on software failures

1. Display the help text:

    ```bash
    $ docker compose -f local.yml run --rm django python -m failures classifyfailure --help
    ```

2. Classify articles:

    ```bash
    $ docker compose -f local.yml run -e OPENAI_API_KEY --rm django python -m failures classifyfailure
    ```

### Step 3. Classifying articles on whether they contain enough information for failure analysis

1. Display the help text:

    ```bash
    $ docker compose -f local.yml run --rm django python -m failures classifyanalyzable --help
    ```

2. Classify articles:

    ```bash
    $ docker compose -f local.yml run -e OPENAI_API_KEY --rm django python -m failures classifyanalyzable
    ```

### Step 4. Merge articles reporting on the same failure into incidents

1. Display the help text:

    ```bash
    $ docker compose -f local.yml run --rm django python -m failures merge --help
    ```

2. Merge articles:

    ```bash
    $ docker compose -f local.yml run -e OPENAI_API_KEY --rm django python -m failures merge
    ```

### Step 6. Create a postmortem report for each incident

1. Display the help text:

    ```bash
    $ docker compose -f local.yml run --rm django python -m failures postmortemincidentautovdb --help
    ```

2. Create postmortem reports:

    ```bash
    $ docker compose -f local.yml run -e OPENAI_API_KEY --rm django python -m failures postmortemincidentautovdb
    ```

> [!NOTE]
> Step 5 (RAG) from the paper is within this command.


### Plot figures and gather statistics used in the paper 

1. Display the help text:

    ```bash
    $ docker compose -f local.yml run --rm django python -m failures results --help
    ```

2. Create postmortem reports:

    ```bash
    $ docker compose -f local.yml run -e OPENAI_API_KEY --rm django python -m failures results
    ```

## Manual analysis and evaluation

### Step 2 to Step 4: Manual analysis and evaluation: [results/manual_analysis/Step2_to_Step4.xlsx](results/manual_analysis/Step2_to_Step4.xlsx)

### Step 6: Manual analysis and evaluation: [results/manual_analysis/Step6.xlsx](results/manual_analysis/Step6.xlsx)

### To evaluate the steps of the pipeline automatically, follow [tests/README.rst](tests/README.rst)
