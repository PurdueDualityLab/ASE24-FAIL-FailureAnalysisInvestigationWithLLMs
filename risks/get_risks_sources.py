import os
import re
import environ
from collections import Counter
import matplotlib.pyplot as plt

def extract_sources_from_file(file_path):
    with open(file_path, 'r', encoding='utf-8', errors='replace') as file:
        content = file.read().split('----------------------------------------------------------------------')[0]

    # Use the provided regex to extract articles from the content
    sources = re.findall(r'\(([^()]+)\)', content)
    filtered_sources = []
    for s in sources:
        s = s.lower()
        # filter the sources that are not relevant
        if s == 'comp.risks' or any(char.isdigit() for char in s) or '@' in s:
            continue
        if 'via' in s:
            s = s.split('via')[0]
        for char in s:
            # format the source properly
            if char == '\n':
                s = s.replace(char, '')

        filtered_sources.append(s)
    
    return filtered_sources

def count_sources(directory_path):
    sources_counter = Counter()

    for filename in os.listdir(directory_path):
        if filename.endswith('.txt'):
            file_path = os.path.join(directory_path, filename)
            sources = extract_sources_from_file(file_path)
            sources_counter.update(sources)

    return sources_counter


def plot_results(sources_counter, threshold=20, bar_width=0.8):
    total_count = sum(sources_counter.values())

    # Filter sources with counts less than the threshold
    filtered_sources = {k: v for k, v in sources_counter.items() if v >= threshold}
    other_count = sum(v for k, v in sources_counter.items() if v < threshold)

    # Add 'other' category
    filtered_sources['other'] = other_count

    # Calculate percentages
    percentages = [(v / total_count) * 100 for v in filtered_sources.values()]

    # Sort sources and percentages in descending order
    sorted_sources, sorted_percentages = zip(*sorted(zip(filtered_sources.keys(), percentages), key=lambda x: x[1]))

    # Plot the horizontal bar chart with adjusted bar width
    plt.figure(figsize=(15, 20))
    bars = plt.barh(sorted_sources, sorted_percentages, color='skyblue', height=bar_width)

    # Display percentage numbers next to the bars
    for bar, percentage in zip(bars, sorted_percentages):
        plt.text(bar.get_width() + 1, bar.get_y() + bar.get_height()/2, f'{percentage:.1f}%', va='center')

    plt.xlabel('Percentage (%)')
    plt.ylabel('Source')
    plt.title(f'Percentage of Sources in RISKS Digest Articles (total: {total_count}))')
    plt.tight_layout()
    plt.savefig('output.png', bbox_inches='tight')
    plt.show()

env = environ.Env()
directory_path = env('RISKS_ARTICLE_PATH')
sources_counter = count_sources(directory_path)
plot_results(sources_counter)

# Write the sorted results to a file
# with open('risks_sources.txt', 'w', encoding='utf-8') as output_file:
#     for article, count in sorted(sources_counter.items(), key=lambda x: x[1], reverse=True):
#         output_file.write(f'{count} occurrences - {article}\n')

