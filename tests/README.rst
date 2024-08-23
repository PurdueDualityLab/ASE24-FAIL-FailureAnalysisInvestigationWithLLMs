Failures Evaluation
========

This folder contains commands necessary to monitor, test, and evaluate the performance and quality of the Failures pipeline and database.

Input Files
-----------

- tests/ground_truth/ground_truth_classify.xlsx : Ground truth file for describes failure, analyzability, incident id. (file provided with correct format)
- tests/ground_truth/ground_truth_postmortem.xlsx : Ground truth file for incident postmortem information. (file provided with correct format)

Fetch Articles Or Incident Data
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Description
------------

This command is designed for fetching Article and Incident data based on either Article or Incident ids.

Output Files
------------

- tests/fetched_data/incident_data.csv : Contains all non-embedding information stored in the incident class for each incident.
- tests/fetched_data/article_data.csv : Contains all non-embedding information stored in the article class for each article.

Commands
--------

#. Display the help text::

    $ docker compose -f local.yml run --rm django python -m tests fetchdata --help

#. Run evaluation & save to CSV::

    $ docker compose -f local.yml run --rm django python -m tests fetchdata --option {Integer Choice} --ids {List of integers separated by spaces}


Evaluate Pipeline's Classification Command
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Description
------------

This command is designed for evaluating the pipeline's classification command. The classification command is responsible for determing whether an article does or does not describe a software failure.

Output Files
------------

- tests/performance/describes_failure.csv : Contains evaluation metrics listed below

Metrics Evaluated
-----------------

- Accuracy (Percentage): Measures the overall correctness of the classification in percentage.
- Accuracy (Fraction): Indicates the accuracy of the classification in fraction format.
- False Positive (Percentage): Percentage of false positives in the classification.
- False Positive (Fraction): Fraction of false positives in the classification.
- False Negative (Percentage): Percentage of false negatives in the classification.
- False Negative (Fraction): Fraction of false negatives in the classification.
- Wrong (Percentage): Percentage of incorrect classifications.
- Wrong (Fraction): Fraction of incorrect classifications.
- Total Evaluated: Total number of articles evaluated.

Commands
--------

#. Display the help text::

    $ docker compose -f local.yml run --rm django python -m tests evaluateclassification --help

#. Run evaluation & save to CSV (default path /tests/performance/describes_failure.csv)::

    $ docker compose -f local.yml run --rm django python -m tests evaluateclassification --saveCSV


Evaluate Pipeline's Identification Command
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Description
------------

This command is designed for evaluating the pipeline's identification command. The identification command is responsible for determing whether or not an article has enough information to analyze the software failure.

Output Files
------------

- tests/performance/analyzable_failure.csv : Contains evaluation metrics listed below

Metrics Evaluated
-----------------

- Accuracy (Percentage): Measures the overall correctness of the identification in percentage.
- Accuracy (Fraction): Indicates the accuracy of the identification in fraction format.
- False Positive (Percentage): Percentage of false positives in the identification.
- False Positive (Fraction): Fraction of false positives in the identification.
- False Negative (Percentage): Percentage of false negatives in the identification.
- False Negative (Fraction): Fraction of false negatives in the identification.
- Wrong (Percentage): Percentage of incorrect identifications.
- Wrong (Fraction): Fraction of incorrect identifications.
- Total Evaluated: Total number of articles evaluated.

Commands
--------

#. Display the help text::

    $ docker compose -f local.yml run --rm django python -m tests evaluateidentification --help

#. Run evaluation & save to CSV (default path /tests/performance/analyzable_failure.csv)::

    $ docker compose -f local.yml run --rm django python -m tests evaluateidentification --saveCSV


Evaluate Pipeline's Merge Command
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Description
------------

This command is designed for evaluating the pipeline's merge command. The merge command is responsible for clustering together articles that report on the same software failure.

Output Files
------------

- tests/performance/merge.csv : Contains evaluation metrics listed below

Metrics Evaluated
-----------------

- Homogeneity: Measures the homogeneity of clusters.
- Completeness: Measures the completeness of clusters.
- V Measure: Combines homogeneity and completeness into a single metric.
- Percentage of Articles Used: Percentage of articles from ground truth that had incidents associated with them in the failures database.
- Fraction of Articles Used: Fraction of articles from ground truth that had incidents associated with them in the failures database.

Commands
--------

#. Display the help text::

    $ docker compose -f local.yml run --rm django python -m tests evaluatemerge --help

#. Run a scrape::

    $ docker compose -f local.yml run --rm django python -m tests evaluatemerge --saveCSV


Evaluate Pipeline's Postmortem Analysis (Needs refactoring, might not work)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Description
------------

This command is designed for evaluating the pipeline's open response postmortem ability. This command automates comparing the data within the Failures database to a sample manual ground truth set of incidents. The command compares each of the non-taxonomy postmortem categories using ChatGPT.

Metrics Evaluated
-----------------

- Invalid: Count of invalid comparisons between two sets.
- Disjoint: Count of disjoint comparisons between two sets.
- Equal: Count of equal comparisons between two sets.
- Subset: Count of subset comparisons between two sets.
- Superset: Count of superset comparisons between two sets.
- Overlapping: Count of overlapping comparisons between two sets.

Commands
--------

#. Display the help text::

    $ docker compose -f local.yml run --rm django python -m failures scrape --help

#. Run a scrape::

    $ docker compose -f local.yml run --rm django python -m failures scrape --keyword "keyword"


Evaluate Pipeline's Taxonomy Analysis (Needs refactoring, not currently working)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Description
------------

This command is designed for evaluating the pipeline's taxonomy analysis. This command automates comparing the data within the Failures database to a sample manual ground truth set of incidents. This compares the taxonomy values.

Metrics Evaluated
-----------------

- Accuracy: Measures the overall correctness of the classification.
- Precision: Indicates the accuracy of positive predictions.
- Recall: Measures the ability to capture positive instances.
- F1 Score: Balances precision and recall.

Commands
--------

#. Display the help text::

    $ docker compose -f local.yml run --rm django python -m failures scrape --help

#. Run a scrape::

    $ docker compose -f local.yml run --rm django python -m failures scrape --keyword "keyword"


Evaluate and Run Pipeline (Outdated)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Description
------------

This command is designed for evaluating and running the pipeline

Metrics Evaluated
-----------------

- All metrics from previous commands

Commands
--------

#. Display the help text::

    $ docker compose -f local.yml run --rm django python -m failures scrape --help

#. Run a scrape::

    $ docker compose -f local.yml run --rm django python -m failures scrape --keyword "keyword"
