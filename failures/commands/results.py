import argparse
import logging
import textwrap

import csv
import pandas as pd
from datetime import datetime
from collections import defaultdict
import matplotlib.pyplot as plt
import plotly.graph_objects as go
from collections import Counter
import itertools
from urllib.parse import urlparse

from django.db.models import Count, Q

from failures.articles.models import Article, Incident
from failures.commands.PROMPTS import TAXONOMY_QUESTIONS, CPS_KEYS


class ResultsCommand:
    def prepare_parser(self, parser: argparse.ArgumentParser):
        parser.description = textwrap.dedent(
            """
            Report results for paper from the database.
            """
        
        )

    def run(self, args: argparse.Namespace, parser: argparse.ArgumentParser):

        logging.info("\nReporting Results.")

        start_year = 2010
        end_year = 2022
        start_date = datetime(start_year, 1, 1)
        end_date = datetime(end_year, 12, 31, 23, 59, 59)

        incidents = Incident.objects.filter(published__range=(start_date, end_date))

        plot_incidents_over_time(incidents, start_year, end_year)
        plot_frequency_of_articles_to_incidents(incidents)
        plot_all_taxonomy(incidents)

        plot_taxonomy(incidents, "causes")
        plot_taxonomy(incidents, "impacts")

        print_stats(incidents, start_date, end_date)

        plot_keywords_sources(incidents)


def plot_incidents_over_time(incidents, start_year, end_year):
    ### To plot incidents over time
    
    years = [year for year in range(start_year, end_year + 1)]

    # Initialize a dictionary to store the count of incidents per year
    incidents_per_year = {year: 0 for year in years}

    # Count the number of incidents per year
    for incident in incidents:
        if incident.published.year in years:
            incidents_per_year[incident.published.year] += 1

    # Create lists of years and corresponding incident counts
    years_list = list(incidents_per_year.keys())
    incident_counts = list(incidents_per_year.values())

    # Calculate year-over-year changes
    yearly_changes = []
    for i in range(1, len(incident_counts)):
        yearly_changes.append(incident_counts[i] - incident_counts[i - 1])

    # Calculate the average change in the number of incidents
    average_change = sum(yearly_changes) / len(yearly_changes)

    # Print the results
    logging.info(f"Yearly changes in incident counts: {yearly_changes}")
    logging.info(f"Average change in the number of incidents per year: {average_change:.2f}")
    

    # Plotting
    plt.bar(years_list, incident_counts, color="tab:blue", edgecolor="midnightblue")
    plt.ylabel('Number of incidents')
    plt.xticks(years_list, rotation=45)  # Ensure all years are displayed on the x-axis
    plt.grid(axis='y', linestyle='--', alpha=0.7)
    plt.tight_layout()  # Adjust layout to prevent clipping of labels
    plt.savefig('results/IncidentsOverTime.png',dpi=300)



def plot_frequency_of_articles_to_incidents(incidents):
    ### To plot the frequency of articles to incidents 
    
    # Annotate the number of articles for each incident
    incidents_with_article_count = incidents.annotate(num_articles=Count('articles'))

    # Extract the number of articles for each incident
    article_counts = incidents_with_article_count.values_list('num_articles', flat=True)

    # Plot the histogram
    plt.hist(article_counts, bins=range(min(article_counts), max(article_counts) + 1), align='left', color="tab:blue",edgecolor="midnightblue")
    plt.xlabel('Number of articles')
    plt.ylabel('Number of incidents')
    plt.grid(True)
    plt.yscale('log')

    #Plot box plot
    #plt.boxplot(article_counts)

    plt.savefig('results/FrequencyArticlesIncidents.png',dpi=300)

    article_counts = pd.Series(article_counts)
    logging.info("Summary stats:")
    logging.info(article_counts.describe())

    total_incidents = incidents_with_article_count.count()

    # Calculate the percentages
    count_1_article = incidents_with_article_count.filter(num_articles=1).count()
    count_2_to_10_articles = incidents_with_article_count.filter(num_articles__range=(2, 10)).count()
    count_11_to_20_articles = incidents_with_article_count.filter(num_articles__range=(11, 20)).count()
    count_21_to_30_articles = incidents_with_article_count.filter(num_articles__range=(21, 30)).count()
    count_more_than_30_articles = incidents_with_article_count.filter(num_articles__gt=30).count()

    # Calculate the percentages
    percentage_1_article = count_1_article / total_incidents * 100
    percentage_2_to_10_articles = count_2_to_10_articles / total_incidents * 100
    percentage_11_to_20_articles = count_11_to_20_articles / total_incidents * 100
    percentage_21_to_30_articles = count_21_to_30_articles / total_incidents * 100
    percentage_more_than_30_articles = count_more_than_30_articles / total_incidents * 100

    # Print the results
    logging.info(f"Count of incidents with exactly 1 article: {count_1_article}, Percentage: {percentage_1_article:.2f}%")
    logging.info(f"Count of incidents with 2 to 10 articles: {count_2_to_10_articles}, Percentage: {percentage_2_to_10_articles:.2f}%")
    logging.info(f"Count of incidents with 11 to 20 articles: {count_11_to_20_articles}, Percentage: {percentage_11_to_20_articles:.2f}%")
    logging.info(f"Count of incidents with 21 to 30 articles: {count_21_to_30_articles}, Percentage: {percentage_21_to_30_articles:.2f}%")
    logging.info(f"Count of incidents with more than 30 articles: {count_more_than_30_articles}, Percentage: {percentage_more_than_30_articles:.2f}%")
    


def plot_all_taxonomy(incidents):

    fields = list(TAXONOMY_QUESTIONS.keys())

    # Create a defaultdict to hold the counts for each field
    field_counts = {field: defaultdict(int) for field in fields}

    # Process each incident
    for incident in incidents:
        for field in fields:
            field_value = getattr(incident, f"{field}_option", "")
            if field_value:  # Check if the field value is not empty or None
                values = [v.strip() for v in field_value.split(",") if v.strip()]  # Split and strip whitespace
                for value in values:
                    field_counts[field][value] += 1

    # Convert the dictionary to a DataFrame
    data = {field: dict(counts) for field, counts in field_counts.items()}
    df = pd.DataFrame(data).fillna(0).astype(int)

    # Transpose the DataFrame for easier plotting
    df = df.T
    df.index.name = 'Fields'

    # Plotting the stacked bar chart
    ax = df.plot(kind='barh', stacked=True, figsize=(14, 8))

    # Adding labels and title
    ax.set_xlabel('Count')
    ax.set_ylabel('Fields')
    ax.set_title('Distribution of Keys for Each Field in Incidents')
    ax.legend(title='Options', bbox_to_anchor=(1.05, 1), loc='upper left')

    plt.savefig('results/TaxonomyDistributionOverYears.png')
    

def print_stats(incidents, start_date, end_date):

    num_incidents = len(incidents)
    logging.info("Number of incidents between 2010 to 2022: " + str(num_incidents))

    incidents = Incident.objects.filter(published__range=(start_date, end_date), rag=True)
    num_incidents = len(incidents)
    logging.info("Number of incidents between 2010 to 2022 with RAG: " + str(num_incidents))

    incidents = Incident.objects.filter(published__range=(start_date, end_date), rag=False)
    num_incidents = len(incidents)
    logging.info("Number of incidents between 2010 to 2022 without RAG: " + str(num_incidents))

    incidents = Incident.objects.filter(published__range=(start_date, end_date))
    num_incidents = len(incidents)
    
    count = 0
    for incident in incidents:
        if "one_organization" in incident.recurring_option or "multiple_organization" in incident.recurring_option:
            count += 1
    
    logging.info("Number of recurring incidents, one_organization or multiple_organization: "+ str(count) +", "+str(int(count/num_incidents*100)) + "%")
    
    # Query to annotate each incident with the count of related articles
    incidents_with_article_counts = Incident.objects.annotate(article_count=Count('articles'))

    # Filter incidents which have more than 30 articles
    incidents_with_more_than_30_articles = incidents_with_article_counts.filter(article_count__gt=30)

    # Print the IDs of these incidents
    for incident in incidents_with_more_than_30_articles:
        logging.info(f"Incident ID: {incident.id}, Article Count: {incident.article_count}")
        print(f"Incident ID: {incident.id}, Article Count: {incident.article_count}")


    years = list(Article.objects.values_list('published__year', flat=True).distinct())

    stats = {}
    for year in years:
        count_all = Article.objects.filter(published__year=year).count()
        count_scrape_successful = Article.objects.filter(scrape_successful=True, published__year=year).count()
        count_describes_failure = Article.objects.filter(describes_failure=True, published__year=year).count()
        count_analyzable_failure = Article.objects.filter(analyzable_failure=True, published__year=year).count()

        # Count incidents with articles for the specific year
        count_incidents = Incident.objects.filter(published__year=year).count() #Incident.objects.filter(articles__published__year=year).distinct().count()

        stats[year] = {
            'all': count_all,
            'scrape_successful': count_scrape_successful,
            'describes_failure': count_describes_failure,
            'analyzable_failure': count_analyzable_failure,
            'incidents': count_incidents
        }


    csv_file_path = 'results/stats.csv'
    # Write the data to the CSV file
    with open(csv_file_path, 'w', newline='') as csvfile:
        fieldnames = ['Year', 'All', 'Scrape Successful', 'Describes Failure', 'Analyzable Failure', 'Incidents']
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

        # Write the header
        writer.writeheader()

        # Write the data
        for year, counts in stats.items():
            writer.writerow({
                'Year': year,
                'All': counts['all'],
                'Scrape Successful': counts['scrape_successful'],
                'Describes Failure': counts['describes_failure'],
                'Analyzable Failure': counts['analyzable_failure'],
                'Incidents': counts['incidents']
            })

    logging.info(f'Stats has been written to {csv_file_path}')

def plot_taxonomy(incidents, characterize):
    ### For plotting the taxonomy
    
    #incidents = incidents.filter(~Q(objective_option__in=["non-malicious", "unknown"]))
    #incidents = incidents.filter(cps_option="TRUE")
    #incidents = incidents.filter(phase_option__contains="operation")

    num_incidents = len(incidents)

    causes = ["recurring", "phase", "boundary", "nature", "dimension", "objective", "intent", "capability", "cps", "perception", "communication", "application"]
    impacts = ["duration", "behaviour", "domain", "consequence"]

    data  = {}
    for taxonomy_key in TAXONOMY_QUESTIONS.keys():
        data[taxonomy_key] = []


    for incident in incidents:
        for field in data.keys():
            values = getattr(incident, field+"_option")
            if values:
                true_values = [val.strip() for val in values.split(",")]
                if "unknown" in true_values and len(true_values) > 1: #If LLM says unknown and other options, then remove unknown.
                    true_values.remove("unknown")
                data[field].extend(true_values)

    df = pd.DataFrame({key: pd.Series(value) for key, value in data.items()})

    # Determine the maximum count for scaling
    max_count = max(df.apply(lambda x: x.value_counts().max(), axis=0))

    fields = list(data.keys())
    if characterize == "causes":
        fields = [key for key in fields if key in causes]
    elif characterize == "impacts":
        fields = [key for key in fields if key in impacts]
    
    fig, axes = plt.subplots(nrows=int(len(fields)/4), ncols=4, figsize=(20, int((len(fields)/4)*5)))

    for i, ax in enumerate(axes.flatten()):
        if i < len(fields):
            num_incidents_ratio = num_incidents
            field = fields[i]
            value_counts = df[field].value_counts()

            if field == "consequence":
                #value_counts = value_counts.drop(index="no_consequence")
                value_counts = value_counts.drop(index="non-human")
                value_counts = value_counts.drop(index="theoretical_consequence")

            bars = value_counts.plot(kind='barh', ax=ax)
            ax.set_title(field)
            ax.set_xlabel('Number of incidents')
            #ax.set_ylabel('Keys')

            if field in CPS_KEYS:
                ax.set_xlim(0, df["cps"].value_counts()["TRUE"])  # Set the CPS Max for all subplots
                num_incidents_ratio = df["cps"].value_counts()["TRUE"]
            else:
                ax.set_xlim(0, num_incidents)  # Set the same x-axis limit for all subplots

            labels = [label.replace('_', '\n') for label in value_counts.index]
            ax.set_yticklabels(labels) # Replace underscores with spaces and set y-tick labels

                # Display value of each bar inside the bar
            for bar in bars.patches:
                width = bar.get_width()
                placement = 'inside' if width > (max_count * 0.7) else 'outside'
                text_color = 'black'
                offset = -5 if placement == 'inside' else 5
                ha = 'right' if placement == 'inside' else 'left'
                ax.text(width + offset, bar.get_y() + bar.get_height() / 2, str(width)+", "+str(int(width/num_incidents_ratio*100))+"%", ha=ha, va='center', color=text_color, fontsize=12)
        
    plt.tight_layout()
    plt.savefig(f'results/TaxonomyDistributionSubplotsRecurring{characterize}.png',dpi=300)
    
        

def plot_keywords_sources(incidents):
    ### To plot pie chart of keywords and sources 
    
    # Step 2: Get the associated articles for the queried incidents
    articles = Article.objects.filter(incident__in=incidents)

    # Step 3: Count the articles by keywords and sources
    keyword_counter = Counter()
    source_counter = Counter()


    for article in articles:
        unique_keywords = set(article.search_queries.values_list('keyword', flat=True))
        for keyword in unique_keywords:
            keyword_counter[keyword] += 1
        
        # Extract the domain name from the source URL
        if "dailymail" in article.source:
            domain = urlparse(article.source).netloc.split('.')[-3]
        else:
            domain = urlparse(article.source).netloc.split('.')[-2]
        
        source_counter[domain] += 1

    # Remove "software " from keyword labels
    keyword_counter = {k.replace("software ", ""): v for k, v in keyword_counter.items() if k.startswith("software ")}
    
    # Group small counts for keywords and sources
    keyword_counter = group_small_counts(keyword_counter)
    source_counter = group_small_counts(source_counter)

    # Sort the counters by count (smallest to largest)
    keyword_counter = dict(sorted(keyword_counter.items(), key=lambda item: item[1]))
    source_counter = dict(sorted(source_counter.items(), key=lambda item: item[1]))


    # Define a larger color palette
    colors = plt.cm.tab20.colors  # Tab20 has 20 distinct colors
    color_cycle = itertools.cycle(colors) # Create a color cycle iterator to handle more colors

    # Step 4: Plot the figures with two subplots
    fig, axs = plt.subplots(1, 2, figsize=(10, 5))

    # First subplot: Pie chart of articles by keywords
    wedges, texts, autotexts = axs[0].pie(keyword_counter.values(), labels=keyword_counter.keys(), autopct='%1.0f%%', startangle=140, colors=[next(color_cycle) for _ in keyword_counter], radius=1, pctdistance=0.85)
    axs[0].set_xlabel('(a)', weight='bold')

    # Increase text size and percentage size for the subplot
    for text in texts + autotexts:
        text.set_fontsize(12)
        text.set_color('black')
        text.set_fontweight('bold')  # Make labels bold


    # Second subplot: Pie chart of articles by sources
    wedges, texts, autotexts = axs[1].pie(source_counter.values(), labels=source_counter.keys(), autopct='%1.0f%%', startangle=140, colors=[next(color_cycle) for _ in source_counter], radius=1, pctdistance=0.85)
    axs[1].set_xlabel('(b)', weight='bold')

    # Increase text size and percentage size for the subplot
    for text in texts + autotexts:
        text.set_fontsize(12)
        text.set_color('black')
        text.set_fontweight('bold')  # Make labels bold


    #plt.subplots_adjust(left=0.1, right=0.9, top=0.9, bottom=0.1, wspace=0.3)
    plt.tight_layout()

    plt.savefig(f'results/SourcesKeywordsPieChart.png',dpi=300)


    # Step 4: Group keywords that are less than 2% into the "Other" category
    def group_small_counts(counter, threshold=0.02):
        total_count = sum(counter.values())
        other_count = 0
        grouped_counter = Counter()
        for key, count in counter.items():
            if count / total_count < threshold:
                other_count += count
            else:
                grouped_counter[key] += count
        if other_count > 0:
            grouped_counter["other"] = other_count
        return grouped_counter
    
    
    '''
    tax_field = "dimension"
    tax_options = ["hardware"]

    # Construct the filter expression dynamically
    filter_expression = Q()
    for tax_option in tax_options:
        filter_expression |= Q(**{f"{tax_field}_option__contains": tax_option})

    # Apply the filter expression to the queryset
    filtered_incidents = incidents.filter(filter_expression)

    #filtered_incidents = incidents.filter(recurring_option__contains="multiple_organization")

    characterize = ""  # "impacts" or "causes"
    causes = ["recurring", "phase", "boundary", "nature", "dimension", "objective", "intent", "capability", "cps", "perception", "communication", "application"]
    impacts = ["duration", "behaviour", "domain", "consequence"]

    # Function to process incidents into a DataFrame
    def process_incidents(incidents):
        data = {taxonomy_key: [] for taxonomy_key in TAXONOMY_QUESTIONS.keys()}
        for incident in incidents:
            for field in data.keys():
                values = getattr(incident, field + "_option")
                if values:
                    true_values = [val.strip() for val in values.split(",")]
                    if "unknown" in true_values and len(true_values) > 1:
                        true_values.remove("unknown")
                    data[field].extend(true_values)
        return pd.DataFrame({key: pd.Series(value) for key, value in data.items()})

    # Process main incidents and filtered incidents
    df = process_incidents(incidents)
    filtered_df = process_incidents(filtered_incidents)

    # Determine the maximum count for scaling
    max_count = max(df.apply(lambda x: x.value_counts().max(), axis=0))

    # Filter fields based on characterize variable
    fields = list(TAXONOMY_QUESTIONS.keys())
    if characterize == "causes":
        fields = [key for key in fields if key in causes]
    elif characterize == "impacts":
        fields = [key for key in fields if key in impacts]

    # Create subplots
    fig, axes = plt.subplots(nrows=int(len(fields) / 4), ncols=4, figsize=(20, int((len(fields) / 4) * 5)))

    # Plot each taxonomy field
    for i, ax in enumerate(axes.flatten()):
        if i < len(fields):
            field = fields[i]
            num_incidents_ratio = num_incidents

            # Main incidents value counts
            value_counts = df[field].value_counts()

            # Filtered incidents value counts
            filtered_value_counts = filtered_df[field].value_counts()

            if field == "consequence":
                value_counts = value_counts.drop(index="non-human", errors='ignore')
                value_counts = value_counts.drop(index="theoretical_consequence", errors='ignore')
                filtered_value_counts = filtered_value_counts.drop(index="non-human", errors='ignore')
                filtered_value_counts = filtered_value_counts.drop(index="theoretical_consequence", errors='ignore')

            # Reindex filtered_value_counts to match the main value_counts index
            filtered_value_counts = filtered_value_counts.reindex(value_counts.index).fillna(0)

            # Plot main incidents
            bars = value_counts.plot(kind='barh', ax=ax, alpha=0.7, color='mistyrose', label='All Incidents')
            
            # Overlay filtered incidents
            filtered_bars = filtered_value_counts.plot(kind='barh', ax=ax, alpha=0.5, color='aquamarine', label='Filtered Incidents')
            
            ax.set_title(field)
            ax.set_xlabel('Number of incidents')
            if field in CPS_KEYS:
                ax.set_xlim(0, df["cps"].value_counts().get("TRUE", 0))
                num_incidents_ratio = df["cps"].value_counts().get("TRUE", 0)
            else:
                ax.set_xlim(0, num_incidents)

            labels = [label.replace('_', '\n') for label in value_counts.index]
            ax.set_yticks(range(len(labels)))
            ax.set_yticklabels(labels)

            # Display value of each bar inside the bar for main incidents
            for bar in bars.patches:
                width = bar.get_width()
                placement = 'inside' if width > (max_count * 0.7) else 'outside'
                text_color = 'red'
                offset = -5 if placement == 'inside' else 5
                ha = 'right' if placement == 'inside' else 'left'
                ax.text(width + offset, bar.get_y() + bar.get_height() / 2, str(width) + ", " + str(int(width / num_incidents_ratio * 100)) + "%", ha=ha, va='center', color=text_color, fontsize=8, rotation=45)
            
            # Display value of each bar inside the bar for filtered incidents
            for bar in filtered_bars.patches:
                width = bar.get_width()
                placement = 'inside' if width > (max_count * 0.7) else 'outside'
                text_color = 'blue'
                offset = -5 if placement == 'inside' else 5
                ha = 'right' if placement == 'inside' else 'left'
                ax.text(width + offset, bar.get_y() + bar.get_height() / 2, str(width) + ", " + str(int(width / num_incidents_ratio * 100)) + "%", ha=ha, va='center', color=text_color, fontsize=8, rotation=45)

            ax.legend()

    plt.tight_layout()
    #plt.savefig(f'results/taxonomy/{tax_field}-multiple_organization-one_organization.png',dpi=300)
    plt.savefig(f'results/taxonomy/{tax_field}-{tax_option}.png',dpi=300)
    '''