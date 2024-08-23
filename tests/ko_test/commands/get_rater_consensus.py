import csv
# import pandas
import shutil
import os

file_path = "scripts/Ko_Stories_Consensus.csv"

data_dict = {}

# Read CSV
with open(file_path, 'r') as csv_file:

    # Create reader object
    csv_reader = csv.reader(csv_file)

    # Skip header
    next(csv_reader, None)

    # Iterate through eachrow
    for row in csv_reader:
        # Structure
        # [story, article, rater1, rater2, rater3, consensus]
        if row[5] != 'invalid':

            if row[0] in data_dict:
                data_dict[row[0]].append(row[1])
            else:
                data_dict[row[0]] = [row[1]]

print(len(data_dict))



# Store stores/articles to data_dict
# try:
#     with open(file_path, 'r') as file:
#         # Skip the first line
#         iter_file = iter(file)
#         next(iter_file)

#         for line in iter_file:
#             parts = line.strip().split(';')

#             if len(parts) < 3:
#                 continue

#             first_part = int(parts[0])
#             second_part = int(parts[1])
#             third_part = parts[2]

#             if "null" in third_part:
#                 continue

#             if first_part in data_dict:
#                 data_dict[first_part].append(second_part)
#             else:
#                 data_dict[first_part] = [second_part]

# except Exception as e:
#     print("Exception")
#     print("An error occurred: {}".format(e))

# Create a new directory named "stories" if it doesn't exist
# new_directory = "stories"
# if not os.path.exists(new_directory):
#     os.makedirs(new_directory)

# # Copy files to the new directory
# source_directory = "/scratch/failures/ko_failures/extraction/stories"

# for story in data_dict.keys():
#     for article in data_dict[story]:
#         source_path = os.path.join(source_directory, str(story), "{}.txt".format(article))
#         new_story_directory = new_directory + "/" + str(story)
#         if not os.path.exists(new_story_directory):
#             os.makedirs(new_story_directory)
#         destination_path = os.path.join(new_story_directory, "{}.txt".format(article))

#         try:
#             shutil.copyfile(source_path, destination_path)
#             print("File copied: {} to {}".format(source_path, destination_path))
#         except FileNotFoundError as e:
#             print("File not found: {}".format(source_path))
#         except Exception as e:
#             print("Error copying file: {}".format(e))
